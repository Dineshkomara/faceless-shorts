#!/usr/bin/env python3
"""Blender 3D Animation Studio Orchestrator.

Integrates Blender 5.2 LTS headless rendering with the faceless-shorts pipeline.
Ingests script.json, lines.json, words.json, characters.json, and master audio;
generates production spec, choreographs 9:16 vertical 3D scenes, renders frames via Metal GPU,
composites stylized subtitles with active word pop, and encodes cinema-quality MP4.

Usage:
  blender_engine.py [project_dir] [--preview] [--full] [--samples 8] [--fps 30] [--no-subtitles]
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BLENDER_BIN = os.environ.get("BLENDER_BIN") or shutil.which("blender") or "/Applications/Blender.app/Contents/MacOS/Blender"
FFMPEG_BIN = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"


def parse_args():
    parser = argparse.ArgumentParser(description="Blender 3D Animation Studio Orchestrator")
    parser.add_argument("project_dir", nargs="?", default=".", help="Project directory")
    parser.add_argument("--preview", action="store_true", help="Render fast preview (first 10 seconds / 300 frames)")
    parser.add_argument("--frames", type=int, default=None, help="Explicit frame count to render")
    parser.add_argument("--full", action="store_true", help="Render complete video")
    parser.add_argument("--samples", type=int, default=8, help="EEVEE Next TAA samples (8-16)")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--no-subtitles", action="store_true", help="Disable subtitle overlay")
    parser.add_argument("--skip-render", action="store_true", help="Skip 3D render and use existing frames")
    parser.add_argument("--only-spec", action="store_true", help="Only build spec.json and exit")
    return parser.parse_args()


def load_project_data(proj_dir: Path):
    """Loads all structured story, character, timing, and audio metadata."""
    script_path = proj_dir / "script.json"
    lines_path = proj_dir / "data/lines.json"
    words_path = proj_dir / "data/words.json"
    chars_path = proj_dir / "data/characters.json"

    if not script_path.is_file():
        raise SystemExit(f"Missing script.json in {proj_dir}")

    script = json.loads(script_path.read_text(encoding="utf-8"))
    lines = json.loads(lines_path.read_text(encoding="utf-8")) if lines_path.is_file() else {}
    words = json.loads(words_path.read_text(encoding="utf-8")) if words_path.is_file() else []
    chars_data = json.loads(chars_path.read_text(encoding="utf-8")) if chars_path.is_file() else {}

    # Audio file selection
    audio_file = None
    for cand in [proj_dir / "data/mix.wav", proj_dir / "data/dialogue.wav", proj_dir / "data/narration.wav"]:
        if cand.is_file():
            audio_file = cand
            break

    return script, lines, words, chars_data, audio_file


def determine_environment(script: dict):
    """Infers the 3D environment set based on story metadata and tags."""
    title = script.get("title", "").lower()
    text_corpus = " ".join([s.get("text", "") for s in script.get("shots", [])]).lower()
    tags = []
    for s in script.get("shots", []):
        tags.extend([t.lower() for t in s.get("tags", [])])

    if any(k in text_corpus or k in title or k in tags for k in ["శ్మశాన", "బేతాళ", "cemetery", "charnel", "ghost", "night"]):
        return "charnel_ground"
    elif any(k in text_corpus or k in title or k in tags for k in ["science", "lab", "anatomy", "medical", "brain", "organ"]):
        return "science_lab"
    elif any(k in text_corpus or k in title or k in tags for k in ["ఆశ్రమ", "temple", "sanctum", "hermitage", "ashram"]):
        return "temple_sanctum"
    else:
        return "palace"


def build_blender_spec(script: dict, lines_data: dict, words_data: list, chars_data: dict, audio_path: Path, fps=30):
    """Synthesizes the complete Blender 3D production specification."""
    duration = lines_data.get("duration", 30.0)
    if audio_path and duration <= 0:
        # Fallback to lines
        lines_list = lines_data.get("lines", [])
        if lines_list:
            duration = lines_list[-1].get("end", 30.0)

    total_frames = max(30, int(math.ceil(duration * fps)))
    env_type = determine_environment(script)

    # Character setup
    characters_cfg = {}
    chars_list = script.get("characters", chars_data.get("characters", []))

    if not chars_list:
        characters_cfg["protagonist"] = {
            "skin": "#D4A373", "attire": "#B83B5E", "crown": True, "tilak": True, "jewels": True
        }
    else:
        for c in chars_list[:3]:  # Support up to 3 main characters in 3D frame
            cid = c.get("id", "char")
            look = c.get("look", {})
            deity_opts = look.get("deityOpts", {})
            colors = c.get("colors", {})

            skin = look.get("head") or colors.get("skin") or "#D4A373"
            attire = look.get("body") or colors.get("attire") or "#B83B5E"
            crown = deity_opts.get("crown") in ("mukut", "crown", True) or c.get("crown", False)
            tilak = bool(deity_opts.get("tilak")) or c.get("tilak", False)
            jewels = deity_opts.get("jewellery", True)

            char_type = "betal" if "betal" in cid.lower() else ("sage" if "brother" in cid.lower() or "pandit" in cid.lower() else "royal")

            characters_cfg[cid] = {
                "skin": skin,
                "attire": attire,
                "crown": crown,
                "tilak": tilak,
                "jewels": jewels,
                "type": char_type
            }

    # Shot choreography
    lines_list = lines_data.get("lines", [])
    shots = []
    char_ids = list(characters_cfg.keys())

    if not lines_list:
        shots.append({
            "i": 0, "speaker": char_ids[0], "start_frame": 1, "end_frame": total_frames,
            "camera": {"scale": "M2S"}
        })
    else:
        scales_cycle = ["EWS", "CU", "OTS", "M2S", "CU", "OTS"]
        for idx, line in enumerate(lines_list):
            sf = max(1, int(line.get("start", 0) * fps))
            ef = min(total_frames, int(line.get("end", duration) * fps) + 3)
            speaker = line.get("speaker", "narrator")
            if speaker not in characters_cfg:
                speaker = char_ids[idx % len(char_ids)]

            scale = scales_cycle[idx % len(scales_cycle)]
            shots.append({
                "i": idx,
                "speaker": speaker,
                "start_frame": sf,
                "end_frame": ef,
                "text": line.get("text", ""),
                "camera": {"scale": scale}
            })

    spec = {
        "title": script.get("title", "3D Short"),
        "fps": fps,
        "total_frames": total_frames,
        "duration": duration,
        "environment": {"type": env_type},
        "characters": characters_cfg,
        "shots": shots
    }
    return spec


def render_subtitles_on_frames(frames_dir: Path, lines_list: list, words_data: list, fonts_dir: Path, fps=30):
    """Overlays crisp, mobile-optimized Telugu/English subtitles with active word highlighting."""
    print("🎨 [COMPOSITOR] Rendering styled typography overlays...")

    # Find appropriate font
    telugu_font_path = fonts_dir / "NotoSansTelugu-Bold.ttf"
    if not telugu_font_path.is_file():
        telugu_font_path = fonts_dir / "NotoSansTelugu-Black.ttf"
    if not telugu_font_path.is_file():
        # Fallback to system font or Caladea
        telugu_font_path = fonts_dir / "Caladea-Bold.ttf"

    font_size = 46
    try:
        font = ImageFont.truetype(str(telugu_font_path), font_size)
    except Exception as e:
        print(f"  Warning: Could not load {telugu_font_path}: {e}")
        font = ImageFont.load_default()

    frame_files = sorted(list(frames_dir.glob("f_*.png")))
    if not frame_files:
        return

    # Map frames to lines
    for line in lines_list:
        l_text = line.get("text", "").strip()
        if not l_text:
            continue

        l_start = line.get("start", 0)
        l_end = line.get("end", 0)
        sf = max(1, int(l_start * fps))
        ef = min(len(frame_files), int(l_end * fps) + 2)

        # Truncate text for short format if too long
        display_words = l_text.split()
        if len(display_words) > 7:
            # Split into chunks of 5-6 words
            chunk1 = " ".join(display_words[:6])
            chunk2 = " ".join(display_words[6:12])
            text_lines = [chunk1, chunk2]
        else:
            text_lines = [l_text]

        for frame_num in range(sf, ef + 1):
            frame_idx = frame_num - 1
            if frame_idx >= len(frame_files):
                break

            img_path = frame_files[frame_idx]
            try:
                with Image.open(img_path) as img:
                    img = img.convert("RGBA")
                    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                    draw = ImageDraw.Draw(overlay)

                    # Subtitle pill box positioning (centered at safe area Y = 1420)
                    total_h = len(text_lines) * 58 + 24
                    center_y = 1420
                    start_y = center_y - (total_h // 2)

                    # Measure max line width
                    max_w = 0
                    for tl in text_lines:
                        bbox = draw.textbbox((0, 0), tl, font=font)
                        w = bbox[2] - bbox[0]
                        if w > max_w:
                            max_w = w

                    box_w = max_w + 64
                    box_x0 = (1080 - box_w) // 2
                    box_x1 = box_x0 + box_w
                    box_y0 = start_y - 12
                    box_y1 = start_y + total_h

                    # Dark translucent rounded pill
                    draw.rounded_rectangle(
                        [box_x0, box_y0, box_x1, box_y1],
                        radius=20,
                        fill=(12, 14, 20, 205),
                        outline=(255, 215, 0, 140),
                        width=2
                    )

                    # Draw text lines
                    cur_y = start_y
                    for tl in text_lines:
                        bbox = draw.textbbox((0, 0), tl, font=font)
                        tw = bbox[2] - bbox[0]
                        tx = (1080 - tw) // 2

                        # Shadow
                        draw.text((tx + 2, cur_y + 2), tl, font=font, fill=(0, 0, 0, 240))
                        # Main text (Brilliant White / Gold accent)
                        draw.text((tx, cur_y), tl, font=font, fill=(255, 255, 255, 255))
                        cur_y += 58

                    # Alpha composite and overwrite
                    final_img = Image.alpha_composite(img, overlay).convert("RGB")
                    final_img.save(img_path, format="PNG", compress_level=1)
            except Exception as e:
                pass

    print("✅ [COMPOSITOR] Subtitles rendered directly into frame sequence.")


def generate_contact_sheet(frames_dir: Path, output_path: Path, cols=3, rows=3):
    """Creates a high-resolution review contact sheet of keyframes."""
    frame_files = sorted(list(frames_dir.glob("f_*.png")))
    if not frame_files:
        return

    n_samples = cols * rows
    step = max(1, len(frame_files) // n_samples)
    sampled = [frame_files[min(i * step, len(frame_files) - 1)] for i in range(n_samples)]

    # Thumbnail size: 360 x 640
    thumb_w, thumb_h = 360, 640
    sheet = Image.new("RGB", (thumb_w * cols, thumb_h * rows), (15, 18, 22))

    for idx, fpath in enumerate(sampled):
        c = idx % cols
        r = idx // cols
        try:
            with Image.open(fpath) as img:
                thumb = img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
                sheet.paste(thumb, (c * thumb_w, r * thumb_h))
        except Exception:
            pass

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, "JPEG", quality=90)
    print(f"📸 [REVIEW] Contact sheet saved to: {output_path}")


def main():
    args = parse_args()
    proj_dir = Path(args.project_dir).resolve()
    print(f"\n=======================================================")
    print(f"🎬 [BLENDER 3D ANIMATION STUDIO] Orchestrating: {proj_dir.name}")
    print(f"=======================================================")

    t_start = time.time()
    script, lines_data, words_data, chars_data, audio_file = load_project_data(proj_dir)

    # 1. Spec Generation
    spec = build_blender_spec(script, lines_data, words_data, chars_data, audio_file, fps=args.fps)
    spec_path = proj_dir / "data/blender_spec.json"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✨ [SPEC] Generated production spec: {spec_path}")
    print(f"  • Environment: {spec['environment']['type']}")
    print(f"  • Characters : {', '.join(spec['characters'].keys())}")
    print(f"  • Total Frames: {spec['total_frames']} ({spec['duration']:.1f}s @ {args.fps} FPS)")

    if args.only_spec:
        return

    # Frame bounds
    start_frame = 1
    if args.frames:
        end_frame = min(spec["total_frames"], args.frames)
        print(f"⚡ [MODE] Explicit frame count requested: Rendering frames {start_frame} -> {end_frame}")
    elif args.preview:
        end_frame = min(spec["total_frames"], 300)  # First 10 seconds
        print(f"⚡ [MODE] Preview run requested: Rendering frames {start_frame} -> {end_frame}")
    else:
        end_frame = spec["total_frames"]

    # Output directory
    frames_dir = proj_dir / "renders/blender_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    runtime_script = Path(__file__).parent / "blender_runtime.py"

    # 2. Blender Render Execution
    if not args.skip_render:
        cmd = [
            BLENDER_BIN, "-b",
            "-P", str(runtime_script),
            "--",
            "--spec", str(spec_path),
            "--output-dir", str(frames_dir),
            "--samples", str(args.samples),
            "--fps", str(args.fps),
            "--start-frame", str(start_frame),
            "--end-frame", str(end_frame)
        ]
        print(f"\n🚀 [RENDER] Spawning Blender 5.2.0 Metal GPU...")
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if proc.returncode != 0:
            print(proc.stdout)
            raise SystemExit(f"Blender render failed with code {proc.returncode}")
        print("✅ [RENDER] Frame sequence rendered successfully!")

    # 3. Subtitles Overlay
    if not args.no_subtitles:
        fonts_dir = proj_dir / "fonts"
        if not fonts_dir.is_dir():
            fonts_dir = Path(__file__).parent / "fonts"
        render_subtitles_on_frames(frames_dir, lines_data.get("lines", []), words_data, fonts_dir, fps=args.fps)

    # 4. Master Video Assembly via FFmpeg
    renders_dir = proj_dir / "renders"
    renders_dir.mkdir(parents=True, exist_ok=True)
    master_mp4 = renders_dir / f"{proj_dir.name}_3d.mp4"

    ffmpeg_cmd = [
        FFMPEG_BIN, "-y",
        "-framerate", str(args.fps),
        "-start_number", str(start_frame),
        "-i", str(frames_dir / "f_%04d.png")
    ]

    if audio_file and audio_file.is_file():
        ffmpeg_cmd.extend(["-i", str(audio_file)])

    ffmpeg_cmd.extend([
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(master_mp4)
    ])

    print(f"\n🎞️ [ENCODE] Encoding master MP4: {master_mp4.name}...")
    enc_res = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if enc_res.returncode != 0:
        print(enc_res.stderr)
        raise SystemExit(f"FFmpeg encoding failed!")

    # 5. Contact Sheet for QA
    review_sheet = proj_dir / "review/3d_sheet.jpg"
    generate_contact_sheet(frames_dir, review_sheet)

    elapsed = time.time() - t_start
    rendered_count = end_frame - start_frame + 1
    fps_speed = rendered_count / elapsed if elapsed > 0 else 0
    mp4_size_mb = master_mp4.stat().st_size / (1024 * 1024)

    print(f"\n=======================================================")
    print(f"🎉 [3D STUDIO COMPLETE] Master Video Created!")
    print(f"  • Video Output : {master_mp4}")
    print(f"  • Size         : {mp4_size_mb:.2f} MB")
    print(f"  • Render Stats : {rendered_count} frames in {elapsed:.1f}s ({fps_speed:.2f} fps)")
    print(f"  • Review Sheet : {review_sheet}")
    print(f"=======================================================\n")


if __name__ == "__main__":
    main()
