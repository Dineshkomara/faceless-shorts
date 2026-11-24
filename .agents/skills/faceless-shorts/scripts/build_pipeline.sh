#!/usr/bin/env bash
# build_pipeline.sh - Unified, deterministic build, render, and automated YouTube upload runner
# Usage: ./build_pipeline.sh [project_dir] [--skip-audio] [--skip-assets] [--no-render] [--no-upload] [--dry-run]
set -euo pipefail

PROJ="${1:-.}"
cd "$PROJ"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PY="$SKILL_DIR/scripts/py"

echo "=== [CRAFT 1/8: SCREENWRITER] Syntax & Script Verification ==="
if [ -f "src/shots.js" ]; then
  node --input-type=module --check < src/shots.js
fi

SKIP_AUDIO=0
SKIP_ASSETS=0
NO_RENDER=0
NO_UPLOAD=0
for arg in "$@"; do
  if [ "$arg" = "--skip-audio" ]; then SKIP_AUDIO=1; fi
  if [ "$arg" = "--skip-assets" ]; then SKIP_ASSETS=1; fi
  if [ "$arg" = "--no-render" ]; then NO_RENDER=1; fi
  if [ "$arg" = "--no-upload" ]; then NO_UPLOAD=1; fi
done

if [ "$SKIP_AUDIO" -eq 0 ]; then
  if grep -qiE '"cast"|"speaker"' script.json 2>/dev/null; then
    echo "=== [CRAFT 2/8: CASTING & VOICE] Multi-Character Dialogue & Native Voice Acting (dialogue_engine.py) ==="
    "$PY" "$SKILL_DIR/scripts/dialogue_engine.py" .
  else
    echo "=== [CRAFT 2/8: CASTING & VOICE] Voiceover synthesis (voice.py) ==="
    "$PY" "$SKILL_DIR/scripts/voice.py" .

    echo "=== [CRAFT 2/8: VOICE] Word-level timing (words.py) ==="
    "$PY" "$SKILL_DIR/scripts/words.py" .
  fi
fi

if [ "$SKIP_ASSETS" -eq 0 ]; then
  echo "=== [CRAFT 3/8: CHARACTER DESIGNER] Character Design & Costume Concepts (setup_characters.py) ==="
  "$PY" "$SKILL_DIR/scripts/setup_characters.py" . || echo "  (Character asset setup fallback)"

  echo "=== [CRAFT 4/8: PRODUCTION DESIGNER] Atmospheric Environments & Sets (setup_backgrounds.py) ==="
  "$PY" "$SKILL_DIR/scripts/setup_backgrounds.py" . || echo "  (Background asset setup fallback)"
fi

if grep -qiE '"broll"|"realistic"' script.json 2>/dev/null || [ "${FETCH_BROLL:-0}" -eq 1 ]; then
  echo "=== [CRAFT 4/8: PRODUCTION DESIGN] Sourcing realistic B-roll footage (fetch_broll.py) ==="
  "$PY" "$SKILL_DIR/scripts/fetch_broll.py" . || echo "  (B-roll fetch skipped or partial)"
fi

if grep -qiE '"amar-chitra-katha"|"folk-tale"|"illustrations"' script.json 2>/dev/null || [ -d "assets/illustrations" ] || [ "${FETCH_FOLKTALE:-0}" -eq 1 ]; then
  echo "=== [CRAFT 4/8: PRODUCTION DESIGN] 2D Amar Chitra Katha Indian Folk Art (setup_folktale_illustrations.py) ==="
  "$PY" "$SKILL_DIR/scripts/setup_folktale_illustrations.py" . || echo "  (Folktale illustration setup fallback)"
fi

IS_3D=0
if grep -qiE '"3d-blender"|"style":\s*"3d"' script.json 2>/dev/null || [ "${USE_3D:-0}" -eq 1 ]; then
  IS_3D=1
fi

if [ -f "tools/capture.mjs" ] && [ "$IS_3D" -eq 0 ]; then
  echo "=== [CRAFT 5/8: CINEMATOGRAPHER & DIRECTOR] Camera Blocking & Scene Check (capture.mjs check) ==="
  CHECK_OUTPUT="$(node tools/capture.mjs check)"
  printf '%s\n' "$CHECK_OUTPUT"
  VIDEO_DURATION="$(printf '%s\n' "$CHECK_OUTPUT" | awk '/^duration / {print $2; exit}')"
  SCENE_COUNT="$(printf '%s\n' "$CHECK_OUTPUT" | awk '/^s[0-9][0-9][[:space:]]/ {n++} END {print n+0}')"
  if [ -n "$VIDEO_DURATION" ]; then
    MIN_SCENES="$(awk -v d="$VIDEO_DURATION" 'BEGIN { if (d < 30) n=6; else if (d < 60) n=int((d+4.499)/4.5); else if (d <= 90) n=18; else {n=int((d+4.499)/4.5); if (n>30) n=30} print n }')"
    if [ "$SCENE_COUNT" -lt "$MIN_SCENES" ]; then
      echo "SCENE DENSITY FAILED: $SCENE_COUNT shots for ${VIDEO_DURATION}s; add purposeful angle/insert shots until at least $MIN_SCENES."
      exit 1
    fi
    echo "SCENE DENSITY OK: $SCENE_COUNT shots for ${VIDEO_DURATION}s (minimum $MIN_SCENES)."
  else
    echo "SCENE DENSITY FAILED: capture.mjs check did not report duration."
    exit 1
  fi

  echo "=== [CRAFT 6/8: SOUND DESIGNER] Foley & Sound Cue Extraction (capture.mjs cues) ==="
  node tools/capture.mjs cues

  echo "=== [CRAFT 7/8: FILM EDITOR & VFX] Rhythmic Pacing Gate (capture.mjs pacing) ==="
  node tools/capture.mjs pacing

  echo "=== [CRAFT 6/8: SOUND DESIGNER] Master Multi-Track Mix (mix.py) ==="
  if [ -f "$SKILL_DIR/scripts/mix.py" ]; then
    "$PY" "$SKILL_DIR/scripts/mix.py" .
  else
    "$PY" tools/mix.py .
  fi

  echo "=== [CRAFT 7/8: FILM EDITOR & VFX] Visual QA Contact Sheet (capture.mjs sheet) ==="
  mkdir -p review
  node tools/capture.mjs sheet review/all.jpg 0.5 10
fi

# The 3D Blender route skips the browser audio/QA stages above, but still uses
# capture.mjs for its shot timeline. Enforce the same minimum shot density.
if [ -f "tools/capture.mjs" ] && [ "$IS_3D" -eq 1 ]; then
  echo "=== [CRAFT 5/8: 3D SHOT DENSITY] Scene Check (capture.mjs check) ==="
  CHECK_OUTPUT="$(node tools/capture.mjs check)"
  printf '%s\n' "$CHECK_OUTPUT"
  VIDEO_DURATION="$(printf '%s\n' "$CHECK_OUTPUT" | awk '/^duration / {print $2; exit}')"
  SCENE_COUNT="$(printf '%s\n' "$CHECK_OUTPUT" | awk '/^s[0-9][0-9][[:space:]]/ {n++} END {print n+0}')"
  if [ -z "$VIDEO_DURATION" ]; then
    echo "SCENE DENSITY FAILED: capture.mjs check did not report duration."
    exit 1
  fi
  MIN_SCENES="$(awk -v d="$VIDEO_DURATION" 'BEGIN { if (d < 30) n=6; else if (d < 60) n=int((d+4.499)/4.5); else if (d <= 90) n=18; else {n=int((d+4.499)/4.5); if (n>30) n=30} print n }')"
  if [ "$SCENE_COUNT" -lt "$MIN_SCENES" ]; then
    echo "SCENE DENSITY FAILED: $SCENE_COUNT shots for ${VIDEO_DURATION}s; add purposeful angle/insert shots until at least $MIN_SCENES."
    exit 1
  fi
  echo "SCENE DENSITY OK: $SCENE_COUNT shots for ${VIDEO_DURATION}s (minimum $MIN_SCENES)."
fi

if [ "$NO_RENDER" -eq 0 ]; then
  mkdir -p renders
  PROJ_BASENAME="$(basename "$PWD")"
  VID="renders/${PROJ_BASENAME}.mp4"
  VID_3D="renders/${PROJ_BASENAME}_3d.mp4"

  if [ "$IS_3D" -eq 1 ]; then
    echo "=== [CRAFT 8/8: 3D MASTER RENDER] Blender 5.2 EEVEE Next Metal GPU (blender_engine.py) ==="
    "$PY" "$SKILL_DIR/scripts/blender_engine.py" . --full
    VID="$VID_3D"
  elif [ ! -f "$VID" ] && [ ! -f "renders/${PROJ_BASENAME}_web.mp4" ] && [ ! -f "renders/video.mp4" ] && [ ! -f "renders/video_web.mp4" ]; then
    echo "=== [CRAFT 8/8: MASTER RENDER] Encoding Cinema MP4 (capture.mjs video) ==="
    node tools/capture.mjs video "$VID"
  fi

  echo "=== [CRAFT 8/8: PACKAGING] High-CTR Cover Generation (make_cover.sh) ==="
  mkdir -p covers
  if [ ! -f "covers/cover.jpg" ]; then
    ACT_VID="renders/${PROJ_BASENAME}_web.mp4"
    [ -f "$ACT_VID" ] || ACT_VID="$VID"
    [ -f "$ACT_VID" ] || ACT_VID="renders/video_web.mp4"
    [ -f "$ACT_VID" ] || ACT_VID="renders/video.mp4"
    if [ -f "$ACT_VID" ]; then
      zsh "$SKILL_DIR/scripts/make_cover.sh" "$ACT_VID" covers/cover.jpg 10.0 "THE STORY|UNFOLDS" 96 || true
    fi
  fi

  if [ "$NO_UPLOAD" -eq 0 ]; then
    echo "=== [CRAFT 8/8: AUDIENCE ENGAGEMENT] Automated YouTube Upload (upload_youtube.py) ==="
    UPLOAD_ARGS=(".")
    for a in "$@"; do
      if [ "$a" = "--force" ] || [ "$a" = "--upload" ] || [ "$a" = "--dry-run" ]; then
        UPLOAD_ARGS+=("$a")
      fi
    done
    "$PY" "$SKILL_DIR/scripts/upload_youtube.py" "${UPLOAD_ARGS[@]}"
  fi
fi

echo "=== BUILD & UPLOAD PIPELINE COMPLETE ==="
