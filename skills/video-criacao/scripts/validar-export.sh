#!/usr/bin/env bash
# Validação objetiva: estrutura, decode completo, loudness/true peak e faststart.
set -euo pipefail

[ "$#" -eq 1 ] || { echo "uso: $0 final.mp4" >&2; exit 2; }
IN=$1
[ -f "$IN" ] || { echo "arquivo não encontrado: $IN" >&2; exit 1; }

ffprobe -v error -count_frames \
  -show_entries format=duration,size,bit_rate:stream=index,codec_name,profile,width,height,pix_fmt,r_frame_rate,nb_read_frames,sample_rate,channels \
  -of json "$IN"
ffmpeg -v error -i "$IN" -f null -
ffmpeg -hide_banner -i "$IN" -map 0:a:0 -af ebur128=peak=true -f null - 2>&1 | tail -n 16

MOOV=$(grep -m1 -oba 'moov' "$IN" | cut -d: -f1)
MDAT=$(grep -m1 -oba 'mdat' "$IN" | cut -d: -f1)
if [ -n "${MOOV:-}" ] && [ -n "${MDAT:-}" ] && [ "$MOOV" -lt "$MDAT" ]; then
  echo "faststart: OK (moov=$MOOV antes de mdat=$MDAT)"
else
  echo "faststart: FALHOU" >&2
  exit 1
fi
