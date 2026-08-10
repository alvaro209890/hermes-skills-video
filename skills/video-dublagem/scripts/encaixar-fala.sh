#!/usr/bin/env bash
# Encaixa um segmento TTS num slot com Rubber Band e gera QA JSON.
# Uso: encaixar-fala.sh entrada.wav saida.wav slot_segundos [semitons=0]
set -euo pipefail

[ "$#" -ge 3 ] && [ "$#" -le 4 ] || {
  echo "uso: $0 entrada.wav saida.wav slot_segundos [semitons=0]" >&2
  exit 2
}
IN=$1
OUT=$2
SLOT=$3
ST=${4:-0}
[ -f "$IN" ] || { echo "entrada não encontrada: $IN" >&2; exit 1; }
FILTERS=$(ffmpeg -hide_banner -filters 2>/dev/null)
grep -qw rubberband <<<"$FILTERS" || { echo "ffmpeg sem filtro rubberband" >&2; exit 1; }
awk -v s="$SLOT" 'BEGIN { exit !(s > 0) }' || { echo "slot inválido: $SLOT" >&2; exit 2; }

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
TEMPO=$(awk -v d="$DUR" -v s="$SLOT" 'BEGIN { printf "%.9f", d / s }')
PITCH=$(awk -v st="$ST" 'BEGIN { if (st !~ /^-?[0-9]+([.][0-9]+)?$/) exit 2; printf "%.9f", exp(log(2) * st / 12) }') || {
  echo "semitons inválidos: $ST" >&2
  exit 2
}
awk -v t="$TEMPO" 'BEGIN { exit !(t >= 0.90 && t <= 1.10) }' || {
  printf 'REESCREVER: segmento %.3fs não cabe em %.3fs sem tempo %.3fx (limite 0.90–1.10)\n' "$DUR" "$SLOT" "$TEMPO" >&2
  exit 3
}

mkdir -p "$(dirname "$OUT")"
ffmpeg -y -v error -i "$IN" -af \
  "aformat=sample_rates=48000:channel_layouts=mono,rubberband=tempo=${TEMPO}:pitch=${PITCH}:transients=smooth:detector=soft:phase=laminar:window=long:smoothing=on:formant=preserved:pitchq=quality:channels=together,apad=pad_dur=${SLOT},atrim=0:${SLOT},asetpts=PTS-STARTPTS" \
  -ar 48000 -c:a pcm_s24le "$OUT"

REAL=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")
DESVIO_MS=$(awk -v r="$REAL" -v s="$SLOT" 'BEGIN { d=(r-s)*1000; if (d<0) d=-d; printf "%.1f", d }')
QA="${OUT%.*}.qa.json"
printf '{\n  "entrada_s": %.6f,\n  "slot_s": %.6f,\n  "tempo": %.9f,\n  "pitch_st": %.3f,\n  "saida_s": %.6f,\n  "desvio_ms": %.1f,\n  "status": "%s"\n}\n' \
  "$DUR" "$SLOT" "$TEMPO" "$ST" "$REAL" "$DESVIO_MS" \
  "$([ "$(awk -v d="$DESVIO_MS" 'BEGIN { print (d <= 150) ? 1 : 0 }')" = 1 ] && echo ok || echo revisar)" > "$QA"
echo "ok: $OUT · tempo=${TEMPO}x · desvio=${DESVIO_MS}ms · QA=$QA"
