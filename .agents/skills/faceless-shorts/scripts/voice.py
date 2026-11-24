"""Narration for $0 on this computer: Kokoro-82M text-to-speech (Apache-2.0) via kokoro-onnx. No account, no API.

  scripts/py scripts/voice.py <project>          script.json -> data/narration.wav + data/lines.json (exact line times)
  scripts/py scripts/voice.py --list             voices that narrate well
  scripts/py scripts/voice.py --download         only fetch the model files (~340 MB, once)

script.json: { "voice": "am_michael", "speed": 1.05, "lead": 0.45, "outro": 0.9, "gap": 0.32,
               "lines": [ { "text": "What if you swallow gum?", "caps": "...", "gap": 0.3 }, ... ] }
One line = one CUT, not one sentence: a sentence can run across several lines ("It slides down your throat and lands
in your stomach," / "where acid gets to work on it."). Lines are grouped into whole sentences and each sentence is
spoken in ONE pass, so the intonation flows naturally; then every cut inside a sentence is found in the audio (snapped
to the nearest pause, else placed by length). "gap" (on a sentence's last line) = the pause after that sentence.
Write numbers the way they're SAID. Then run words.py for the word timings.
"""
import argparse, json, os, re, subprocess, sys, urllib.request
from pathlib import Path
import numpy as np
from scipy.io import wavfile

HOME = Path(os.environ.get('FACELESS_HOME', Path.home() / '.faceless-shorts'))
KDIR = HOME / 'kokoro'
PDIR = HOME / 'piper-voices'                    # piper models: <lang>_<REGION>-<name>-<quality>.onnx
PIPER_PY = HOME / 'piper-venv/bin/python'       # piper lives in its own venv (espeak-ng deps)
PIPER_RE = re.compile(r'^[a-z]{2}_[A-Z]{2}-[a-z]+$')
EDGE_RE = re.compile(r'^[a-z]{2}-[A-Z]{2}-[A-Za-z0-9]+Neural$')
SARVAM_RE = re.compile(r'^(?:sarvam:)?([a-zA-Z0-9_-]+)$')
FILES = {
    'kokoro-v1.0.onnx': 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx',
    'voices-v1.0.bin': 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin',
}
GOOD = {
    # Sarvam AI (native Indian languages, expressive storytelling)
    'sarvam:shubh': 'Telugu male, expressive native storyteller (sarvam ai, realistic)',
    'sarvam:ratan': 'Telugu male, deep grounded narrator (sarvam ai, realistic)',
    'sarvam:anand': 'Telugu male, warm folktale storyteller (sarvam ai, realistic)',
    'sarvam:priya': 'Telugu female, expressive storyteller (sarvam ai, realistic)',
    # Edge-TTS (ultra-realistic Microsoft Neural speech, natural cadence, zero cost)
    'en-US-ChristopherNeural': 'US male, authoritative, documentary (edge-tts, realistic)',
    'en-US-GuyNeural': 'US male, passionate, news/story (edge-tts, realistic)',
    'en-US-JennyNeural': 'US female, friendly conversational (edge-tts, realistic)',
    'en-US-AndrewMultilingualNeural': 'US male, warm & authentic (edge-tts, realistic)',
    'te-IN-MohanNeural': 'Telugu male, natural conversational (edge-tts, realistic)',
    'te-IN-ShrutiNeural': 'Telugu female, friendly warm (edge-tts, realistic)',
    # Kokoro (English, local onnx)
    'am_michael': 'US male, steady explainer (default)', 'am_puck': 'US male, lively, playful', 'am_fenrir': 'US male, deeper',
    'am_onyx': 'US male, low', 'af_heart': 'US female, warm (best overall)', 'af_bella': 'US female, bright',
    'af_nicole': 'US female, soft and close', 'bm_george': 'UK male, documentary', 'bm_fable': 'UK male, storyteller',
    'bf_emma': 'UK female, calm',
    # Piper (Telugu & Hindi, local onnx)
    'hi_IN-rohan': 'Hindi male, steady explainer (piper)',
    'hi_IN-pratham': 'Hindi male, younger (piper)',
    'hi_IN-priyamvada': 'Hindi female (piper)',
    'te_IN-venkatesh': 'Telugu male, steady explainer (piper)',
    'te_IN-maya': 'Telugu female (piper)',
    'te_IN-padmavathi': 'Telugu female, soft (piper)',
}
SR = 24000


def ensure_models():
    KDIR.mkdir(parents=True, exist_ok=True)
    for name, url in FILES.items():
        p = KDIR / name
        if p.exists() and p.stat().st_size > 1_000_000: continue
        print(f'downloading {name} (once)...', flush=True)
        tmp = p.with_suffix('.part'); urllib.request.urlretrieve(url, tmp); tmp.rename(p)


def trim(x, thr=0.008):
    """cut leading/trailing silence so line start/end times are exact"""
    idx = np.where(np.abs(x) > thr)[0]
    if not len(idx): return x
    a = max(0, idx[0] - int(0.01 * SR)); b = min(len(x), idx[-1] + int(0.03 * SR)); return x[a:b]


def silences(x, thr=0.012, min_len=0.06):
    """pauses inside speech: [(start_s, end_s)] where the 10 ms RMS stays under thr for >= min_len"""
    hop = int(0.01 * SR); n = len(x) // hop
    rms = np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1)); quiet = rms < thr * np.abs(x).max()
    out, st = [], None
    for f, q in enumerate(quiet):
        if q and st is None: st = f
        if (not q or f == n - 1) and st is not None:
            if (f - st) * 0.01 >= min_len: out.append((st * 0.01, f * 0.01))
            st = None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('project', nargs='?'); ap.add_argument('--list', action='store_true'); ap.add_argument('--download', action='store_true')
    ap.add_argument('--voice'); ap.add_argument('--speed', type=float)
    a = ap.parse_args()
    if a.list:
        for k, v in GOOD.items(): print(f'{k:30s} {v}')
        return
    if a.download:
        ensure_models()
        return
    if not a.project: ap.error('project folder missing')
    P = Path(a.project); S = json.loads((P / 'script.json').read_text())
    sarvam_key = os.environ.get('SARVAM_API_KEY')
    if not sarvam_key:
        kf = HOME / 'sarvam_key.txt'
        if kf.exists(): sarvam_key = kf.read_text().strip()

    is_te = S.get('lang') == 'te' or any('\u0c00' <= c <= '\u0c7f' for c in json.dumps(S))
    if is_te and sarvam_key:
        default_v = 'sarvam:shubh'
    elif is_te:
        default_v = 'te-IN-MohanNeural'
    else:
        default_v = 'en-US-ChristopherNeural'

    voice = a.voice or S.get('voice', default_v)
    if is_te and voice in ('en-US-ChristopherNeural', 'am_michael'):
        voice = 'sarvam:shubh' if sarvam_key else 'te-IN-MohanNeural'
    speed = a.speed or S.get('speed', 1.0)
    pitch_val = S.get('pitch', '+0Hz')
    # group the lines into whole sentences (a line ending in . ? ! closes one; "break": true forces a close)
    groups, cur = [], []
    for i, ln in enumerate(S['lines']):
        cur.append(i)
        if re.search(r'[.?!]["\')]*$', ln['text'].strip()) or ln.get('break') or i == len(S['lines']) - 1: groups.append(cur); cur = []
    if voice.startswith('sarvam:'):
        if not sarvam_key: raise SystemExit('SARVAM_API_KEY missing (set in env or ~/.faceless-shorts/sarvam_key.txt)')
        spk = voice.split(':', 1)[1]
        cache_dir = P / 'data/sarvam_cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        import base64, urllib.request, hashlib

        def say_sarvam(text):
            h = hashlib.sha256(f"{spk}_{speed}_{text}".encode('utf-8')).hexdigest()[:16]
            wav_path = cache_dir / f"{h}.wav"
            if not wav_path.exists():
                url = 'https://api.sarvam.ai/text-to-speech'
                headers = {'api-subscription-key': sarvam_key, 'Content-Type': 'application/json'}
                payload = {
                    'text': text,
                    'target_language_code': 'te-IN' if is_te else 'hi-IN',
                    'speaker': spk,
                    'model': 'bulbul:v3',
                    'pace': float(speed),
                    'speech_sample_rate': SR
                }
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
                with urllib.request.urlopen(req) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    wav_path.write_bytes(base64.b64decode(data['audios'][0]))
            sr0, x0 = wavfile.read(wav_path)
            x = x0.astype(np.float64) / 32768.0
            return trim(x)

        say = say_sarvam
    elif EDGE_RE.match(voice):                      # edge-tts engine: ultra-realistic neural speech
        import asyncio, edge_tts, hashlib
        rate_pct = int(round((speed - 1.0) * 100))
        rate_str = f"{rate_pct:+d}%"
        cache_dir = P / 'data/edge_cache'
        cache_dir.mkdir(parents=True, exist_ok=True)

        async def _synth(txt, mp3_path):
            c = edge_tts.Communicate(txt, voice, rate=rate_str, pitch=pitch_val)
            await c.save(mp3_path)

        def say_edge(text):
            h = hashlib.sha256(f"{voice}_{speed}_{pitch_val}_{text}".encode('utf-8')).hexdigest()[:16]
            mp3_path = cache_dir / f"{h}.mp3"
            wav_path = cache_dir / f"{h}.wav"
            if not wav_path.exists():
                asyncio.run(_synth(text, str(mp3_path)))
                subprocess.run(
                    ['ffmpeg', '-y', '-i', str(mp3_path), '-ar', str(SR), '-ac', '1', str(wav_path)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                )
                try: mp3_path.unlink()
                except Exception: pass
            sr0, x0 = wavfile.read(wav_path)
            x = x0.astype(np.float64) / 32768.0
            return trim(x)

        say = say_edge
    elif PIPER_RE.match(voice):                   # piper engine: non-English voices, 22050 Hz -> resample to SR
        from scipy.signal import resample_poly
        model = next(iter(sorted(PDIR.glob(f'{voice}*.onnx'))), None)
        if not model: raise SystemExit(f'piper voice missing: {PDIR}/{voice}*.onnx (download it to ~/.faceless-shorts/piper-voices/)')
        texts = sorted({' '.join(S['lines'][i]['text'] for i in g) for g in groups} | {S['lines'][i]['text'] for i in range(len(S['lines']))})
        man = {'out': str(P / 'data/piper'), 'length_scale': round(1.0 / speed, 3), 'sents': {f't{k:03d}': t for k, t in enumerate(texts)}}
        mpath = P / 'data/piper_manifest.json'; (P / 'data').mkdir(parents=True, exist_ok=True); mpath.write_text(json.dumps(man, indent=1, ensure_ascii=False))
        r = subprocess.run([str(PIPER_PY), str(Path(__file__).parent / 'piper_say.py'), str(model), str(mpath)], capture_output=True, text=True)
        if r.returncode != 0: raise SystemExit(f'piper failed: {r.stderr.strip()[-600:]}')
        print(r.stdout.strip()[-200:], flush=True)
        clips = {}
        for k, t in enumerate(texts):
            sr0, x0 = wavfile.read(P / 'data/piper' / f't{k:03d}.wav')
            x = resample_poly(x0.astype(np.float64) / 32768.0, SR, sr0) if sr0 != SR else x0.astype(np.float64) / 32768.0
            clips[t] = trim(x)
        say = lambda text: clips[text]
    else:                                         # kokoro engine (English)
        ensure_models()
        from kokoro_onnx import Kokoro
        k = Kokoro(str(KDIR / 'kokoro-v1.0.onnx'), str(KDIR / 'voices-v1.0.bin'))
        lang = 'en-gb' if voice.startswith('b') else 'en-us'
        say = lambda text: trim(np.asarray(k.create(text, voice=voice, speed=speed, lang=lang)[0], dtype=np.float64))
    out = [np.zeros(int(S.get('lead', 0.4) * SR))]; t = len(out[0]) / SR; lines = [None] * len(S['lines'])
    for g in groups:
        x = say(' '.join(S['lines'][i]['text'] for i in g))
        cuts = [0.0]
        if len(g) > 1:                                    # find each cut inside the sentence
            lens = np.array([len(say(S['lines'][i]['text'])) for i in g], dtype=float)
            pauses = silences(x)
            for c in np.cumsum(lens)[:-1] / lens.sum() * len(x) / SR:
                near = [p for p in pauses if abs((p[0] + p[1]) / 2 - c) < 0.4]
                if near: p = min(near, key=lambda p: abs((p[0] + p[1]) / 2 - c)); cuts.append((p[0], p[1]))
                else: cuts.append((c, c))
        n = len(x) / SR
        for j, i in enumerate(g):
            a = 0.0 if j == 0 else cuts[j][1]; b = n if j == len(g) - 1 else cuts[j + 1][0]
            lines[i] = {'i': i, 'text': S['lines'][i]['text'], 'start': round(t + a, 3), 'end': round(t + b, 3)}
            print(f'{i:2d} {lines[i]["start"]:6.2f}-{lines[i]["end"]:6.2f}  {S["lines"][i]["text"]}', flush=True)
        gap = np.zeros(int(float(S['lines'][g[-1]].get('gap', S.get('gap', 0.3))) * SR))
        out += [x, gap]; t += (len(x) + len(gap)) / SR
    outro = np.zeros(int(float(S.get('outro', 0.9)) * SR)); out.append(outro)
    y = np.concatenate(out)

    # Broadcast Studio Vocal Mastering Strip (warmth, anti-boxiness, clarity, leveling)
    try:
        from vocal_master import master_vocal_audio
        y_mastered = master_vocal_audio(y, SR, lang='te' if is_te else 'en')
        out_sr = 48000
    except Exception as e:
        print(f"[voice] Warning: vocal_master fallback ({e})")
        peak = np.abs(y).max()
        y_mastered = (y / (peak + 1e-9) * 0.9) if peak > 0 else y
        out_sr = SR

    (P / 'data').mkdir(exist_ok=True)
    wavfile.write(P / 'data/narration.wav', out_sr, (y_mastered * 32767).astype(np.int16))
    dur = len(y_mastered) / out_sr
    (P / 'data/lines.json').write_text(json.dumps({'duration': round(dur, 3), 'voice': voice, 'speed': speed, 'lines': lines}, indent=1))
    print(f'data/narration.wav ({dur:.2f} s, {voice} x{speed}, mastered @ {out_sr}Hz) + data/lines.json. Next: words.py')


if __name__ == '__main__':
    main()
