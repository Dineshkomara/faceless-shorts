#!/usr/bin/env python3
"""Cinema Multi-Character Dialogue & Ensemble Voice Engine.

Transforms video scripts from single-narrator monologues into dynamic,
multi-character conversational dramas with distinct actor voices, pitch modulation,
conversational turn-taking, and character-tagged caption timings.

Features:
  1. Cast Matrix: Maps characters to distinct voice models, pitch, rate, and theme colors.
  2. Multi-Character Synthesis: Edge-TTS, Piper, and Kokoro support per character.
  3. Conversational Cadence: Natural conversational reaction gaps between speakers (0.28-0.45s)
     vs internal sentence pauses (0.18-0.25s).
  4. Speaker-Tagged Timings: Produces data/lines.json and data/words.json with speaker attribution.
  5. Backward Compatibility: Plain script.json without speaker tags runs seamlessly as single-narrator.

Usage:
  py scripts/dialogue_engine.py <project_dir>
"""

import argparse
import asyncio
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile

HOME = Path(os.environ.get('FACELESS_HOME', Path.home() / '.faceless-shorts'))
KDIR = HOME / 'kokoro'
PDIR = HOME / 'piper-voices'
PIPER_PY = HOME / 'piper-venv/bin/python'
PIPER_RE = re.compile(r'^[a-z]{2}_[A-Z]{2}-[a-z]+$')
EDGE_RE = re.compile(r'^[a-z]{2}-[A-Z]{2}-[A-Za-z0-9]+Neural$')
SARVAM_RE = re.compile(r'^(?:sarvam:)?([a-zA-Z0-9_-]+)$')

SR = 24000
norm = lambda w: re.sub(r'[^\w]+', '', w.lower())

# Detect Sarvam AI Key for native Telugu synthesis
SARVAM_KEY = os.environ.get('SARVAM_API_KEY')
if not SARVAM_KEY:
    kf = HOME / 'sarvam_key.txt'
    if kf.exists():
        SARVAM_KEY = kf.read_text().strip()

# Built-in Ensemble Cast Presets (Telugu & English)
# When Sarvam key is available, Telugu characters automatically use native Sarvam AI voices.
DEFAULT_CAST = {
    "te": {
        "narrator": {"name": "సూత్రధారుడు (Narrator)", "voice": "sarvam:shubh" if SARVAM_KEY else "te-IN-MohanNeural", "pitch": "+0Hz", "rate": "+0%", "color": "#F3F4F6"},
        "hero":     {"name": "నాయకుడు (Hero)",          "voice": "sarvam:shubh" if SARVAM_KEY else "te-IN-MohanNeural", "pitch": "-2Hz", "rate": "-1%", "color": "#FFD700"},
        "elder":    {"name": "మహర్షి / గురువు (Elder)",   "voice": "sarvam:ratan" if SARVAM_KEY else "te-IN-MohanNeural", "pitch": "-3Hz", "rate": "-2%", "color": "#FB923C"},
        "deity":    {"name": "దేవుడు (Divine)",         "voice": "sarvam:ratan" if SARVAM_KEY else "te-IN-MohanNeural", "pitch": "-2Hz", "rate": "-1%", "color": "#FACC15"},
        "cunning":  {"name": "ఇంద్రుడు / మాయ (Cunning)", "voice": "sarvam:anand" if SARVAM_KEY else "te-IN-MohanNeural", "pitch": "+2Hz", "rate": "+1%", "color": "#38BDF8"},
        "devi":     {"name": "దేవి / స్త్రీ (Goddess)",     "voice": "sarvam:priya" if SARVAM_KEY else "te-IN-ShrutiNeural", "pitch": "+0Hz", "rate": "+0%", "color": "#F472B6"},
    },
    "en": {
        "narrator":  {"name": "Narrator",            "voice": "en-US-ChristopherNeural", "pitch": "+0Hz", "rate": "+0%", "color": "#F3F4F6"},
        "expert":    {"name": "Scientist / Mentor",  "voice": "en-US-ChristopherNeural", "pitch": "-2Hz", "rate": "-1%", "color": "#38BDF8"},
        "protagonist":{"name": "Hero / Explorer",    "voice": "en-US-GuyNeural",         "pitch": "+0Hz", "rate": "+2%", "color": "#FBBF24"},
        "analyst":   {"name": "Analyst",             "voice": "en-US-AndrewMultilingualNeural", "pitch": "-2Hz", "rate": "+0%", "color": "#34D399"},
        "female_lead":{"name": "Specialist",         "voice": "en-US-JennyNeural",       "pitch": "+0Hz", "rate": "+0%", "color": "#F472B6"},
        "young":     {"name": "Young Challenger",    "voice": "en-US-AvaNeural",         "pitch": "+2Hz", "rate": "+1%", "color": "#A78BFA"},
    }
}


def trim_silence(x, thr=0.008):
    """Cut leading/trailing silence to lock exact speech boundaries."""
    idx = np.where(np.abs(x) > thr)[0]
    if not len(idx):
        return x
    a = max(0, idx[0] - int(0.01 * SR))
    b = min(len(x), idx[-1] + int(0.03 * SR))
    return x[a:b]


def parse_script_lines(S):
    """Normalizes lines and extracts speaker metadata."""
    lang = S.get('lang', 'te' if any('\u0c00' <= c <= '\u0c7f' for c in json.dumps(S)) else 'en')
    cast_dict = S.get('cast', {})
    default_voice = S.get('voice', 'te-IN-MohanNeural' if lang == 'te' else 'en-US-ChristopherNeural')

    # Flatten scenes if structured as multi-scene episode
    raw_lines = []
    if 'scenes' in S and isinstance(S['scenes'], list):
        for sc in S['scenes']:
            for ln in sc.get('lines', []):
                raw_lines.append(ln)
    elif 'lines' in S:
        raw_lines = S['lines']

    parsed = []
    for i, item in enumerate(raw_lines):
        if isinstance(item, str):
            item = {'text': item}
        text = item.get('text', '').strip()
        if not text:
            continue

        speaker_key = item.get('speaker', 'narrator').lower()
        char_meta = cast_dict.get(speaker_key, {})
        preset_meta = DEFAULT_CAST.get(lang, {}).get(speaker_key, {})

        voice = item.get('voice') or char_meta.get('voice') or preset_meta.get('voice') or default_voice
        pitch = item.get('pitch') or char_meta.get('pitch') or preset_meta.get('pitch') or "+0Hz"
        rate = item.get('rate') or char_meta.get('rate') or preset_meta.get('rate') or "+0%"
        color = item.get('color') or char_meta.get('color') or preset_meta.get('color') or "#F3F4F6"
        name = item.get('speaker_name') or char_meta.get('name') or preset_meta.get('name') or speaker_key.capitalize()
        emotion = item.get('emotion', 'neutral')

        parsed.append({
            'index': i,
            'speaker': speaker_key,
            'speaker_name': name,
            'voice': voice,
            'pitch': pitch,
            'rate': rate,
            'color': color,
            'emotion': emotion,
            'text': text,
            'gap': float(item.get('gap', 0.0)),
        })

    return parsed, lang


async def synthesize_edge(text, voice, pitch, rate, out_wav):
    """Synthesizes high-fidelity speech via edge-tts."""
    import edge_tts
    tmp_mp3 = out_wav.with_suffix('.mp3')
    communicate = edge_tts.Communicate(text, voice, pitch=pitch, rate=rate)
    await communicate.save(str(tmp_mp3))
    subprocess.run(
        ['ffmpeg', '-y', '-i', str(tmp_mp3), '-ar', str(SR), '-ac', '1', str(out_wav)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
    )
    if tmp_mp3.exists():
        tmp_mp3.unlink()


def synthesize_line(line_item, cache_dir):
    """Synthesizes speech for an individual line utterance."""
    text = line_item['text']
    voice = line_item['voice']
    pitch = line_item['pitch']
    rate = line_item['rate']

    sig = f"{voice}_{pitch}_{rate}_{text}"
    h = hashlib.sha256(sig.encode('utf-8')).hexdigest()[:18]
    cached_wav = cache_dir / f"line_{h}.wav"

    if not cached_wav.exists():
        if voice.startswith('sarvam:'):
            spk = voice.split(':', 1)[1]
            if SARVAM_KEY:
                import base64, urllib.request
                try:
                    url = 'https://api.sarvam.ai/text-to-speech'
                    headers = {'api-subscription-key': SARVAM_KEY, 'Content-Type': 'application/json'}
                    payload = {
                        'text': text,
                        'target_language_code': 'te-IN',
                        'speaker': spk,
                        'model': 'bulbul:v3',
                        'pace': 1.0,
                        'speech_sample_rate': SR
                    }
                    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
                    with urllib.request.urlopen(req) as resp:
                        res_data = json.loads(resp.read().decode('utf-8'))
                        cached_wav.write_bytes(base64.b64decode(res_data['audios'][0]))
                except Exception as e:
                    print(f"  [dialogue_engine] Sarvam AI fallback to Edge-TTS ({e})")
                    fallback_voice = 'te-IN-ShrutiNeural' if spk == 'priya' else 'te-IN-MohanNeural'
                    asyncio.run(synthesize_edge(text, fallback_voice, pitch, rate, cached_wav))
            else:
                fallback_voice = 'te-IN-ShrutiNeural' if spk == 'priya' else 'te-IN-MohanNeural'
                asyncio.run(synthesize_edge(text, fallback_voice, pitch, rate, cached_wav))
        elif EDGE_RE.match(voice):
            asyncio.run(synthesize_edge(text, voice, pitch, rate, cached_wav))
        elif PIPER_RE.match(voice):
            from scipy.signal import resample_poly
            model = next(iter(sorted(PDIR.glob(f'{voice}*.onnx'))), None)
            if not model:
                # Fallback to default edge voice if piper model file is not present locally
                fallback_voice = 'te-IN-MohanNeural' if 'te_' in voice else 'en-US-ChristopherNeural'
                asyncio.run(synthesize_edge(text, fallback_voice, pitch, rate, cached_wav))
            else:
                mpath = cache_dir / f"piper_{h}.json"
                out_dir = cache_dir / f"piper_out_{h}"
                out_dir.mkdir(parents=True, exist_ok=True)
                mpath.write_text(json.dumps({
                    'out': str(out_dir),
                    'length_scale': 1.0,
                    'sents': {'t000': text}
                }, ensure_ascii=False))
                subprocess.run(
                    [str(PIPER_PY), str(Path(__file__).parent / 'piper_say.py'), str(model), str(mpath)],
                    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                raw_wav = out_dir / 't000.wav'
                sr0, x0 = wavfile.read(raw_wav)
                x = resample_poly(x0.astype(np.float64) / 32768.0, SR, sr0) if sr0 != SR else x0.astype(np.float64) / 32768.0
                wavfile.write(cached_wav, SR, (x * 32767).astype(np.int16))
        else:
            # Kokoro fallback
            from kokoro_onnx import Kokoro
            k = Kokoro(str(KDIR / 'kokoro-v1.0.onnx'), str(KDIR / 'voices-v1.0.bin'))
            lang_code = 'en-gb' if voice.startswith('b') else 'en-us'
            audio_arr = k.create(text, voice=voice, speed=1.0, lang=lang_code)[0]
            wavfile.write(cached_wav, SR, (audio_arr * 32767).astype(np.int16))

    sr, data = wavfile.read(cached_wav)
    samples = data.astype(np.float64) / 32768.0
    return trim_silence(samples)


def align_dialogue_words(lines_data, S, dur_audio):
    """Spreads word timestamps attributed by character speaker."""
    words = []
    for l in lines_data:
        spk = l['speaker']
        spk_name = l['speaker_name']
        spk_col = l['color']
        tokens = [w for w in l['text'].split() if norm(w)]
        if not tokens:
            continue

        wts = [len(norm(w)) + 2.5 + (2.5 if w.endswith(',') else 4.0 if re.search(r'[.?!]$', w) else 0) for w in tokens]
        lo = l['start']
        hi = l['end']
        tot_wt = sum(wts) or 1.0
        cur_t = lo

        for tok, wt in zip(tokens, wts):
            d = (hi - lo) * wt / tot_wt
            word_dur = d * 0.92
            words.append({
                'w': tok,
                'line': l['i'],
                'speaker': spk,
                'speaker_name': spk_name,
                'speaker_color': spk_col,
                's': round(cur_t, 3),
                'e': round(cur_t + word_dur, 3),
            })
            cur_t += d

    return words


def build_dialogue_soundtrack(project_dir):
    """Main execution entrypoint for multi-character dialogue synthesis."""
    P = Path(project_dir).resolve()
    script_file = P / 'script.json'
    if not script_file.exists():
        raise SystemExit(f"script.json not found in {P}")

    S = json.loads(script_file.read_text(errors='replace'))
    parsed_lines, lang = parse_script_lines(S)

    if not parsed_lines:
        raise SystemExit(f"No dialogue lines found in {script_file}")

    cache_dir = P / 'data' / 'dialogue_cache'
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"🎬 [CRAFT-VOICE] Synthesizing Multi-Character Dialogue ({len(parsed_lines)} utterances, lang: {lang})...")
    out_audio = [np.zeros(int(S.get('lead', 0.45) * SR))]
    cur_time = len(out_audio[0]) / SR
    processed_lines = []

    last_speaker = None
    for idx, item in enumerate(parsed_lines):
        speaker = item['speaker']
        text = item['text']

        # Conversational Turn-Taking Timing:
        # Different speaker -> dramatic conversational beat (0.35s)
        # Same speaker -> natural breath/sentence pause (0.22s)
        if last_speaker is not None:
            if speaker != last_speaker:
                turn_gap_s = item['gap'] if item['gap'] > 0 else 0.35
            else:
                turn_gap_s = item['gap'] if item['gap'] > 0 else 0.22
            gap_samples = np.zeros(int(turn_gap_s * SR))
            out_audio.append(gap_samples)
            cur_time += len(gap_samples) / SR

        samples = synthesize_line(item, cache_dir)
        dur = len(samples) / SR
        line_start = cur_time
        line_end = line_start + dur

        out_audio.append(samples)
        cur_time += dur

        processed_lines.append({
            'i': idx,
            'speaker': speaker,
            'speaker_name': item['speaker_name'],
            'voice': item['voice'],
            'color': item['color'],
            'emotion': item['emotion'],
            'text': text,
            'start': round(line_start, 3),
            'end': round(line_end, 3),
        })

        print(f"  [{item['speaker_name']}]: {line_start:6.2f}s - {line_end:6.2f}s | {text[:55]}...")
        last_speaker = speaker

    # Outro padding
    outro_s = float(S.get('outro', 1.0))
    out_audio.append(np.zeros(int(outro_s * SR)))

    final_waveform = np.concatenate(out_audio)

    # Apply Studio Vocal Mastering Channel Strip (warmth, anti-boxiness, de-essing, leveling)
    try:
        from vocal_master import master_vocal_audio
        final_waveform = master_vocal_audio(final_waveform, SR, lang=lang)
        final_sr = 48000
    except Exception as e:
        print(f"  [dialogue_engine] Warning: vocal_master fallback ({e})")
        peak = np.abs(final_waveform).max()
        if peak > 0:
            final_waveform = (final_waveform / peak) * 0.92
        final_sr = SR

    total_dur = len(final_waveform) / final_sr
    data_dir = P / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)

    # Write primary master narration audio (backward-compatible) and dedicated dialogue track
    wav_path = data_dir / 'narration.wav'
    wavfile.write(wav_path, final_sr, (final_waveform * 32767).astype(np.int16))
    wavfile.write(data_dir / 'dialogue.wav', final_sr, (final_waveform * 32767).astype(np.int16))

    # Write rich multi-speaker line timeline
    lines_meta = {
        'duration': round(total_dur, 3),
        'mode': 'ensemble_dialogue',
        'lang': lang,
        'cast_count': len(set(l['speaker'] for l in processed_lines)),
        'lines': processed_lines
    }
    (data_dir / 'lines.json').write_text(json.dumps(lines_meta, indent=2, ensure_ascii=False))

    # Generate speaker-attributed words
    words = align_dialogue_words(processed_lines, S, total_dur)
    (data_dir / 'words.json').write_text(json.dumps(words, indent=1, ensure_ascii=False))
    (data_dir / 'words.txt').write_text('\n'.join(
        f"{w['s']:7.2f} {w['e']:7.2f}  [{w['speaker']:^10s}] L{w['line']:<2d} {w['w']}"
        for w in words
    ))

    print(f"✨ Dialogue Master Complete: {wav_path} ({total_dur:.2f}s, {len(words)} words, {lines_meta['cast_count']} speakers).")
    return lines_meta


def main():
    ap = argparse.ArgumentParser(description="Multi-Character Dialogue & Ensemble Voice Engine")
    ap.add_argument("project", nargs="?", default=".", help="Project directory")
    args = ap.parse_args()
    build_dialogue_soundtrack(args.project)


if __name__ == '__main__':
    main()
