#!/usr/bin/env bash
# Uso: animar-painel.sh imagem.png clip.mp4 [frames=45] [in|out|impact]
set -euo pipefail

if [ "$#" -lt 2 ] || [ "$#" -gt 4 ]; then
  echo "uso: $0 imagem.png clip.mp4 [frames=45] [in|out|impact]" >&2
  exit 2
fi

IN=$1
OUT=$2
FRAMES=${3:-45}
MODE=${4:-in}
[ -f "$IN" ] || { echo "imagem nao encontrada: $IN" >&2; exit 1; }

case "$MODE" in
  in)
    VF="scale=1320:2347,zoompan=z='min(zoom+0.0019,1.105)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${FRAMES}:s=1080x1920:fps=30"
    ;;
  out)
    VF="scale=1320:2347,zoompan=z='if(eq(on,1),1.105,max(zoom-0.0019,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${FRAMES}:s=1080x1920:fps=30"
    ;;
  impact)
    VF="scale=1120:1992:force_original_aspect_ratio=increase,crop=1080:1920:x='20+10*sin(n*1.85)':y='36+9*cos(n*2.15)'"
    ;;
  *)
    echo "modo invalido: $MODE (use in, out ou impact)" >&2
    exit 2
    ;;
esac

VF="${VF},eq=contrast=1.045:saturation=1.10,unsharp=5:5:0.35,format=yuv420p"
mkdir -p "$(dirname "$OUT")"
ffmpeg -y -v error -loop 1 -i "$IN" -vf "$VF" -frames:v "$FRAMES" -r 30 \
  -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p -an "$OUT"
echo "ok: $OUT (${FRAMES} frames, modo=$MODE)"
