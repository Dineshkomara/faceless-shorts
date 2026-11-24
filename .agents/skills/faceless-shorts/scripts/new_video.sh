#!/bin/bash
# Start a new video from a style's working example (engine + shots + script), so it renders straight away.
#   bash new_video.sh <style> <short-name> [--dir <parent>]     → <pipeline-root>/<short-name>/
#   bash new_video.sh --list                                    the styles
set -eu
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
list_styles() {
  for d in "$SKILL"/styles/*/; do
    if [ -f "$d/example/index.html" ] && [ -f "$d/example/src/main.js" ] && [ -f "$d/example/tools/capture.mjs" ]; then
      printf '%s\n' "$(basename "$d")"
    fi
  done
  return 0
}
if [ "${1:-}" = "--list" ]; then list_styles; exit 0; fi
USAGE="usage: new_video.sh <style> <short-name> [--dir <parent>]   (runnable styles: $(list_styles | tr '\n' ' '))"
STYLE="${1:?$USAGE}"; NAME="${2:?$USAGE}"; shift 2
DEFAULT_ROOT="$(cd "$SKILL/../../.." && pwd)"
PARENT="${PIPELINE_ROOT:-$DEFAULT_ROOT}"
while [ $# -gt 0 ]; do case "$1" in --dir) PARENT="${2:?}"; shift 2 ;; *) echo "unknown option $1" >&2; exit 2 ;; esac; done
SRC="$SKILL/styles/$STYLE/example"
[ -f "$SRC/index.html" ] && [ -f "$SRC/src/main.js" ] && [ -f "$SRC/tools/capture.mjs" ] || { echo "style '$STYLE' has no runnable frame-capture scaffold ($USAGE)" >&2; exit 2; }
DST="$PARENT/$NAME"
[ -e "$DST" ] && { echo "$DST already exists: pick another name" >&2; exit 2; }
mkdir -p "$PARENT"; cp -R "$SRC" "$DST"; mkdir -p "$DST/renders" "$DST/review" "$DST/data" "$DST/covers"
rm -f "$DST/data/narration.wav" "$DST/data/mix.wav" "$DST/data/words.json" "$DST/data/words.txt" "$DST/data/cues.json" "$DST/renders/"* "$DST/review/"* "$DST/covers/"* 2>/dev/null || true
echo "$DST"
echo "style: $STYLE. Read $SKILL/styles/$STYLE/STYLE.md, then rewrite script.json + src/shots.js"
