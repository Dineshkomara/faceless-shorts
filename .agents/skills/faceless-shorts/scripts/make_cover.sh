#!/usr/bin/env bash
# Procedural Short cover (thumbnail): dramatic frame + bold ALL-CAPS text.
# Usage: make_cover.sh <video.mp4> <out.jpg> <time_s> "LINE 1|LINE 2" [fontsize]
# - Lines separated by |, centered, white text + heavy black outline, lower third.
set -e
V="$1"; OUT="$2"; T="${3:-0.5}"; TEXT="$4"; FS="${5:-96}"
FONT="$(dirname "$0")/fonts/Inter-Black.otf"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
# 0) prefer a caption-free frame rendered straight from the project's canvas (needs patched
#    capture.mjs with --nocap); falls back to the MP4 frame at T.
PROJ="$(dirname "$(dirname "$V")")"
FRAME_FILE=""
if [ -f "$PROJ/tools/capture.mjs" ] && (cd "$PROJ" && node tools/capture.mjs frames "$TMP/nocap" "$T" --nocap >/dev/null 2>&1); then
  FRAME_FILE="$TMP/nocap/$(ls "$TMP/nocap" | head -1)"
  echo "cover frame: canvas (caption-free) at $T s"
fi
if [ -z "$FRAME_FILE" ]; then
  FRAME_FILE="$TMP/frame.png"
  ffmpeg -y -loglevel error -ss "$T" -i "$V" -frames:v 1 \
    -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" "$FRAME_FILE"
  echo "cover frame: MP4 at $T s (captions baked in)"
fi
# 1) overlay text: | separated lines -> centered caption block
# 2) text layer: one centered label per | line, stacked; shadow; composite lower third
TMP_TXT="$TMP/txt.png"
IFS="|" read -r -a TXTL <<< "$TEXT"
N=${#TXTL[@]}
[ "$N" -ge 1 ] || { echo "no text given"; exit 2; }
FIRST=1
for ((i = 0; i < N; i++)); do
  LN="${TXTL[$i]}"
  magick -background none -fill white -stroke black -strokewidth 13 \
    -font "$FONT" -pointsize "$FS" label:"$LN" "$TMP/line$((i + 1)).png"
  if [ "$FIRST" = 1 ]; then magick "$TMP/line$((i + 1)).png" "$TMP_TXT"; FIRST=0; else
    magick "$TMP_TXT" "$TMP/line$((i + 1)).png" -background none -gravity center -append "$TMP_TXT"
  fi
done
magick "$TMP_TXT" \( +clone -background black -shadow 60x14+0+10 \) +swap \
  -background none -layers merge +repage "$TMP/txt2.png"
magick "$FRAME_FILE" "$TMP/txt2.png" -gravity south -geometry +0+210 -composite "$OUT"
echo "cover: $OUT"
