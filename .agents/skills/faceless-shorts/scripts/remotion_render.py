#!/usr/bin/env python3
"""Remotion Renderer for Faceless Shorts.

Bridges a faceless-shorts project (script.json, data/words.json, data/broll.json, data/mix.wav)
into OpenMontage's Remotion composer (ShortsExplainer 1080x1920) for frame-accurate 60fps rendering.

Usage:
  scripts/py scripts/remotion_render.py <project_dir> [output.mp4] [--theme THEME]
"""

import json, os, subprocess, sys
from pathlib import Path

COMPOSER_DIR = Path(os.environ.get('REMOTION_COMPOSER_DIR', Path.home() / 'OpenMontage/remotion-composer'))

def main():
    if len(sys.argv) < 2:
        print("Usage: remotion_render.py <project_dir> [output.mp4] [--theme THEME]", file=sys.stderr)
        sys.exit(1)

    P = Path(sys.argv[1]).resolve()
    out_mp4 = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else P / 'renders/remotion_out.mp4'

    theme = "flat-motion-graphics"
    for i, a in enumerate(sys.argv):
        if a == '--theme' and i + 1 < len(sys.argv):
            theme = sys.argv[i + 1]

    script_file = P / 'script.json'
    if not script_file.exists():
        print(f"Error: {script_file} not found", file=sys.stderr)
        sys.exit(1)

    S = json.loads(script_file.read_text())
    lines = S.get('lines', [])

    # Load words for Remotion WordCaption (word, startMs, endMs)
    words_data = []
    words_file = P / 'data/words.json'
    if words_file.exists():
        try:
            raw_words = json.loads(words_file.read_text())
            for w in raw_words:
                word_txt = w.get("w") or w.get("word") or w.get("text", "")
                if not word_txt:
                    continue
                st = float(w.get("s") if "s" in w else w.get("start", 0))
                et = float(w.get("e") if "e" in w else w.get("end", st + 0.3))
                words_data.append({
                    "word": word_txt,
                    "startMs": int(st * 1000),
                    "endMs": int(et * 1000)
                })
        except Exception as e:
            print(f"Warning loading words: {e}", file=sys.stderr)

    # Stage project assets into Remotion's public/ folder for security sandbox access
    public_proj_dir = COMPOSER_DIR / 'public/staged' / P.name
    public_proj_dir.mkdir(parents=True, exist_ok=True)
    if (P / 'assets').exists():
        staged_assets = public_proj_dir / 'assets'
        if staged_assets.is_symlink() or staged_assets.exists():
            try: staged_assets.unlink()
            except Exception: pass
        try:
            staged_assets.symlink_to(P / 'assets')
        except Exception:
            import shutil
            shutil.copytree(P / 'assets', staged_assets, dirs_exist_ok=True)

    # Load B-roll manifest if exists
    broll_map = {}
    broll_file = P / 'data/broll.json'
    if broll_file.exists():
        try:
            bmanifest = json.loads(broll_file.read_text())
            for item in bmanifest:
                shot_idx = item.get("shot", 0)
                v_rel = item.get("video_file")
                f_rel = item.get("file")
                chosen_rel = v_rel if v_rel and (P / v_rel).exists() else f_rel
                if chosen_rel and (P / chosen_rel).exists():
                    broll_map[shot_idx] = f"staged/{P.name}/{chosen_rel}"
        except Exception as e:
            print(f"Warning loading broll manifest: {e}", file=sys.stderr)

    # Load lines timing
    timing_file = P / 'data/lines.json'
    shot_timings = []
    total_dur = 0.0
    if timing_file.exists():
        try:
            t_obj = json.loads(timing_file.read_text())
            shot_timings = t_obj.get("lines", [])
            total_dur = float(t_obj.get("duration", 0))
        except Exception:
            pass

    # Fallback timing if lines.json missing
    if len(shot_timings) < len(lines):
        cur_t = 0.0
        shot_timings = []
        for line in lines:
            dur = max(2.5, len(line.get('text', '').split()) * 0.35)
            shot_timings.append({"start": cur_t, "end": cur_t + dur})
            cur_t += dur
        total_dur = cur_t

    cuts = []
    for i, line in enumerate(lines):
        t_info = shot_timings[i] if i < len(shot_timings) else {"start": i * 4.0, "end": (i + 1) * 4.0}
        st = float(t_info.get("start", 0))
        # Smooth transition to next line start or end
        if i + 1 < len(shot_timings):
            next_st = float(shot_timings[i + 1].get("start", st + 4.0))
            et = next_st
        else:
            et = float(t_info.get("end", st + 4.0))
            if total_dur > et:
                et = total_dur

        if i == 0:
            st = 0.0

        cut = {
            "id": f"shot_{i:02d}",
            "in_seconds": round(st, 2),
            "out_seconds": round(et, 2),
            "animation": "ken-burns" if i % 2 == 0 else "zoom-in"
        }

        # Check if B-roll media exists
        if i in broll_map:
            cut["source"] = broll_map[i]
            cut["backgroundOverlay"] = 0.35
        else:
            cut["source"] = ""
            cut["backgroundColor"] = "#0A0F1D"

        # Apply shot styling based on hook/stat/callout
        if i == 0:
            cut["type"] = "hero_title"
            cut["text"] = line.get("text", "")[:45]
            cut["subtitle"] = S.get("topic", "")
        elif any(c.isdigit() for c in line.get("text", "")) and len(line.get("text", "").split()) < 12:
            cut["type"] = "stat_card"
            words = line.get("text", "").split()
            stat_w = next((w for w in words if any(c.isdigit() for c in w)), "100%")
            cut["stat"] = stat_w
            cut["subtitle"] = line.get("text", "")
            cut["accentColor"] = "#FFD43B"
        elif i == len(lines) - 1:
            cut["type"] = "callout"
            cut["title"] = "TAKEAWAY"
            cut["text"] = line.get("text", "")
            cut["callout_type"] = "tip"

        cuts.append(cut)

    props = {
        "theme": theme,
        "cuts": cuts,
        "overlays": [],
        "captions": words_data,
        "captionStyle": {
            "wordsPerPage": 3,
            "fontSize": 54,
            "bottomOffset": 260
        }
    }

    props_file = P / 'data/remotion_props.json'
    props_file.parent.mkdir(parents=True, exist_ok=True)
    props_file.write_text(json.dumps(props, indent=2))
    print(f"Generated Remotion props: {props_file}")

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    temp_silent_mp4 = out_mp4.with_suffix('.silent.mp4')
    print(f"Rendering Remotion visual composition to: {temp_silent_mp4} ...")

    cmd = [
        'npx', 'remotion', 'render',
        'src/index.tsx',
        'ShortsExplainer',
        str(temp_silent_mp4),
        '--props', str(props_file),
        '--codec', 'h264',
        '--concurrency', '2'
    ]

    res = subprocess.run(cmd, cwd=COMPOSER_DIR)
    if res.returncode != 0:
        print(f"Remotion render exited with code {res.returncode}", file=sys.stderr)
        sys.exit(res.returncode)

    # Multiplex cinematic audio mix
    mix_wav = P / 'data/mix.wav'
    if mix_wav.exists():
        print(f"Multiplexing audio {mix_wav.name} into final video...")
        mux_cmd = [
            'ffmpeg', '-y', '-i', str(temp_silent_mp4), '-i', str(mix_wav),
            '-map', '0:v', '-map', '1:a',
            '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
            '-shortest', '-movflags', '+faststart',
            str(out_mp4)
        ]
        subprocess.run(mux_cmd, check=True)
        try: temp_silent_mp4.unlink()
        except Exception: pass
    else:
        temp_silent_mp4.rename(out_mp4)

    print(f"SUCCESS: Remotion video rendered at {out_mp4}")

if __name__ == '__main__':
    main()
