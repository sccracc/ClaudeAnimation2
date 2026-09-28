#!/usr/bin/env bash
# Build the finished short: timeline -> frames -> sound mix -> final MP4 (no API calls; uses the saved narration + score).
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH=src
python3 src/build_vo.py                       # narration cut + cue sheet (from assets/audio/narration_take1.wav)
python3 src/render.py --workers "${WORKERS:-4}" --out build/video_only.mp4   # high-quality master (CRF 15)
python3 src/audio.py                          # sfx + music + narration -> build/mix.wav (-16 LUFS)
mkdir -p output
# Delivery encode: two-pass H.264 tuned to keep the paper grain, sized to stay under 100 MB.
X="aq-mode=3:aq-strength=0.85:psy-rd=1.0,0.25:deblock=-2,-2:no-dct-decimate=1"
ffmpeg -v error -y -i build/video_only.mp4 -c:v libx264 -preset slower -b:v 12600k -maxrate 22000k -bufsize 34000k \
  -x264-params "$X" -pass 1 -passlogfile build/x264 -pix_fmt yuv420p -profile:v high -g 48 -an -f null /dev/null
ffmpeg -v error -y -i build/video_only.mp4 -i build/mix.wav -map 0:v:0 -map 1:a:0 -c:v libx264 -preset slower -b:v 12600k \
  -maxrate 22000k -bufsize 34000k -x264-params "$X" -pass 2 -passlogfile build/x264 -pix_fmt yuv420p -profile:v high -g 48 \
  -c:a aac -b:a 256k -ar 48000 -shortest -movflags +faststart output/animated-short-final.mp4
echo "wrote output/animated-short-final.mp4"
