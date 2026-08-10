#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python3 gerar_beat_v3.py
python3 gerar_voz_rap_v3.py
python3 mixar_audio_v3.py
python3 preparar_paineis_v3.py
python3 render_v3.py

ffprobe -v error \
  -show_entries format=duration:stream=index,codec_name,width,height,r_frame_rate,sample_rate,channels \
  -of json ../../saidas/gojo_15s_v3.mp4
ffmpeg -v error -i ../../saidas/gojo_15s_v3.mp4 -f null -
ffmpeg -hide_banner -i ../../saidas/gojo_15s_v3.mp4 -map 0:a:0 \
  -af ebur128=peak=true -f null - 2>&1 | tail -n 16

MOOV=$(grep -m1 -oba 'moov' ../../saidas/gojo_15s_v3.mp4 | cut -d: -f1)
MDAT=$(grep -m1 -oba 'mdat' ../../saidas/gojo_15s_v3.mp4 | cut -d: -f1)
[ -n "$MOOV" ] && [ -n "$MDAT" ] && [ "$MOOV" -lt "$MDAT" ]
echo "faststart: OK (moov=$MOOV, mdat=$MDAT)"
