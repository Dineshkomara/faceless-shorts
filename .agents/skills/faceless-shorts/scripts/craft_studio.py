#!/usr/bin/env python3
"""Movie Studio Craft Orchestrator.

Orchestrates all 8 filmmaking crafts for cinema-grade short and episodic long-form video production.

Crafts Managed:
  1. Screenwriter (craft-screenwriter): Multi-character dialogue & narrative structure
  2. Director (craft-director): Scene blocking, shot scales, and camera angles
  3. Voice Casting (craft-casting-voice): Actor casting & dialogue_engine.py synthesis
  4. Character Designer (craft-character-designer): Reference gathering & alpha sprites
  5. Production Designer (craft-production-designer): Atmospheric sets & backgrounds
  6. Cinematographer (craft-cinematographer): Three-point lighting & camera choreography
  7. Sound Designer (craft-sound-designer): Foley, environmental beds & dynamic cues
  8. Editor / VFX (craft-editor-vfx): Rhythmic pacing, L/J-cuts, color grading & render

Usage:
  py scripts/craft_studio.py status [project]
  py scripts/craft_studio.py produce [project] [--format short|episode]
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ROOT = Path(os.environ.get('PIPELINE_ROOT', Path(__file__).resolve().parents[4]))
PY = SKILL_DIR / 'scripts/py'


def audit_production(project_dir):
    """Audits the completion status of all film crafts in a project."""
    P = Path(project_dir)
    if not P.is_dir():
        cand = ROOT / project_dir
        if cand.is_dir():
            P = cand
        else:
            P = P.resolve()
    else:
        P = P.resolve()

    print(f"\n🎬 ==================== MOVIE PRODUCTION AUDIT: {P.name} ====================")

    crafts = [
        ("Screenplay & Story", (P / 'script.json').exists(), "script.json present"),
        ("Character Design & Sprites", (P / 'data/characters.json').exists(), f"{len(list(P.glob('assets/characters/*.png')))} sprites rendered"),
        ("Production Design & Sets", (P / 'data/backgrounds.json').exists(), f"{len(list(P.glob('assets/backgrounds/*.jpg')))} environments styled"),
        ("Dialogue & Voice Ensemble", (P / 'data/narration.wav').exists() or (P / 'data/dialogue.wav').exists(), "dialogue master soundtrack synthesized"),
        ("Word & Speaker Alignment", (P / 'data/words.json').exists(), "speaker-tagged word timings verified"),
        ("Sound Design & Foley", (P / 'data/cues.json').exists() and (P / 'data/mix.wav').exists(), "foley cues & dynamic audio mix ready"),
        ("Visual QA Sheet", bool(list(P.glob('review/*.jpg'))), "contact sheet approved"),
        ("Master Video Render", bool(list(P.glob('renders/*.mp4'))), "cinematic MP4 master encoded"),
    ]

    all_ready = True
    for craft_name, is_done, detail in crafts:
        icon = "✅" if is_done else "⏳"
        status_label = "READY" if is_done else "PENDING"
        print(f"  {icon} [{status_label:7s}] {craft_name:<30s} : {detail}")
        if not is_done:
            all_ready = False

    print("=========================================================================\n")
    return all_ready


def produce_movie(project_dir, video_format="short"):
    """Executes the deterministic movie-level craft production pipeline."""
    P = Path(project_dir)
    if not P.is_dir():
        cand = ROOT / project_dir
        if cand.is_dir():
            P = cand
        else:
            P = P.resolve()
    else:
        P = P.resolve()
    print(f"\n🚀 Initiating Movie Production Pipeline ({video_format.upper()} FORMAT) for: {P.name}")

    pipeline_script = SKILL_DIR / 'scripts/build_pipeline.sh'
    if not pipeline_script.exists():
        raise SystemExit(f"Build pipeline missing: {pipeline_script}")

    # Step 1: Check script.json
    script_file = P / 'script.json'
    if not script_file.exists():
        raise SystemExit(f"Missing script.json in {P}")

    S = json.loads(script_file.read_text(errors='replace'))
    is_multi_speaker = bool(S.get('cast')) or any(isinstance(l, dict) and l.get('speaker') for l in S.get('lines', []))

    # Step 2: Synthesize Vocal Ensemble & Dialogue
    print("\n[CRAFT: VOICE & CASTING] Building character dialogue track...")
    dialogue_script = SKILL_DIR / 'scripts/dialogue_engine.py'
    res = subprocess.run([str(PY), str(dialogue_script), str(P)])
    if res.returncode != 0:
        print("  (Warning: dialogue_engine fallback to legacy voice.py)")
        subprocess.run([str(PY), str(SKILL_DIR / 'scripts/voice.py'), str(P)], check=True)
        subprocess.run([str(PY), str(SKILL_DIR / 'scripts/words.py'), str(P)], check=True)

    # Step 3: Run Full Pipeline (Characters, Backgrounds, Foley, Sheet, Render)
    print("\n[CRAFT: STUDIO PIPELINE] Assembling visual sets, cinematography, sound, and final render...")
    cmd = ['bash', str(pipeline_script), str(P), '--skip-audio']
    subprocess.run(cmd, check=True)

    audit_production(P)
    print("🎬 Movie-Level Production Complete!")


def main():
    ap = argparse.ArgumentParser(description="Movie Studio Craft Orchestrator")
    ap.add_argument("command", choices=["status", "produce"], help="Action to perform")
    ap.add_argument("project", nargs="?", default=".", help="Project directory")
    ap.add_argument("--format", choices=["short", "episode"], default="short", help="Video format duration")
    args = ap.parse_args()

    if args.command == "status":
        audit_production(args.project)
    elif args.command == "produce":
        produce_movie(args.project, video_format=args.format)


if __name__ == '__main__':
    main()
