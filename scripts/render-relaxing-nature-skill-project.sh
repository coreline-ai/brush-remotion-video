#!/bin/zsh
set -euo pipefail

ROOT="${0:A:h:h}"
PROJECT_ID="relaxing-nature-youtube-660s-skill"
DATA_DIR="$ROOT/data/$PROJECT_ID"
PUBLIC_DIR="$ROOT/tmp/$PROJECT_ID/public"
RENDER_DIR="$ROOT/tmp/$PROJECT_ID/renders"
OUTPUT_DIR="$ROOT/output"
CONCURRENCY="${CONCURRENCY:-4}"

mkdir -p "$RENDER_DIR" "$OUTPUT_DIR"

for chapter in 01 02 03 04 05 06; do
  props="$DATA_DIR/chapters/chapter-$chapter.props.json"
  video="$RENDER_DIR/chapter-$chapter.mp4"
  log="$DATA_DIR/chapter-$chapter-render.log"

  duration=""
  if [[ -f "$video" ]]; then
    duration="$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$video" || true)"
    duration="${duration%,}"
  fi
  if [[ "$duration" == "110.000000" ]]; then
    echo "[SKIP] chapter-$chapter already rendered"
    continue
  fi

  echo "[RENDER] chapter-$chapter"
  npx remotion render "$ROOT/src/index.ts" BrushLandscape "$video" \
    --props="$props" \
    --public-dir="$PUBLIC_DIR" \
    --concurrency="$CONCURRENCY" \
    --codec=h264 \
    --crf=20 \
    >"$log" 2>&1

  duration="$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$video")"
  duration="${duration%,}"
  if [[ "$duration" != "110.000000" ]]; then
    echo "[FAIL] chapter-$chapter video duration: $duration" >&2
    exit 1
  fi
  echo "[PASS] chapter-$chapter duration=$duration"
done

concat_file="$DATA_DIR/chapter-video-concat.txt"
: >"$concat_file"
for chapter in 01 02 03 04 05 06; do
  # Remotion adds a silent audio stream even for audio:null props.  Strip it
  # before concat so the container duration cannot offset the next video PTS.
  chapter_video_only="$RENDER_DIR/chapter-$chapter-video-only.mp4"
  ffmpeg -hide_banner -loglevel error -y \
    -i "$RENDER_DIR/chapter-$chapter.mp4" \
    -map 0:v:0 -c:v copy -an -movflags +faststart "$chapter_video_only"
  echo "file '$chapter_video_only'" >>"$concat_file"
done

video_only="$OUTPUT_DIR/$PROJECT_ID-video-only.mp4"
final="$OUTPUT_DIR/$PROJECT_ID-final.mp4"
audio="$ROOT/public/relaxing-nature-youtube-600s/audio/relaxing-nature-original-bgm-master-660s.wav"

echo "[CONCAT] $video_only"
ffmpeg -hide_banner -loglevel error -y \
  -f concat -safe 0 -i "$concat_file" \
  -map 0:v:0 -c:v copy -an -movflags +faststart "$video_only"

echo "[MUX] $final"
ffmpeg -hide_banner -loglevel error -y \
  -i "$video_only" -i "$audio" \
  -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$final"

echo "[DONE] $final"
