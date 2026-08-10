#!/usr/bin/env bash
# Uso: processar-voz-rap.sh entrada.mp3 saida.wav [semitons=-1.5] [tempo=1.0]
# Cadeia validada para Edge Andrew Multilingual: formante preservado e double discreto.
set -euo pipefail

if [ "$#" -lt 2 ] || [ "$#" -gt 4 ]; then
  echo "uso: $0 entrada.mp3 saida.wav [semitons=-1.5] [tempo=1.0]" >&2
  exit 2
fi

IN=$1
OUT=$2
ST=${3:--1.5}
TEMPO=${4:-1.0}
[ -f "$IN" ] || { echo "entrada não encontrada: $IN" >&2; exit 1; }
FILTERS=$(ffmpeg -hide_banner -filters 2>/dev/null)
grep -qw rubberband <<<"$FILTERS" || {
  echo "ffmpeg sem filtro rubberband; rode scripts/doctor.sh" >&2
  exit 1
}

PITCH=$(awk -v st="$ST" 'BEGIN { if (st !~ /^-?[0-9]+([.][0-9]+)?$/) exit 2; printf "%.9f", exp(log(2) * st / 12) }') || {
  echo "semitons inválidos: $ST" >&2; exit 2;
}
awk -v t="$TEMPO" 'BEGIN { exit !(t >= 0.85 && t <= 1.15) }' || {
  echo "tempo $TEMPO fora da faixa 0.85–1.15; regenere/refraseie em vez de deformar a voz" >&2
  exit 3
}

FILTER="[0:a]aformat=sample_rates=48000:channel_layouts=mono,"
FILTER+="silenceremove=start_periods=1:start_duration=0.02:start_threshold=-48dB:start_silence=0.015,"
FILTER+="areverse,silenceremove=start_periods=1:start_duration=0.02:start_threshold=-48dB:start_silence=0.030,areverse,"
FILTER+="rubberband=tempo=${TEMPO}:pitch=${PITCH}:transients=smooth:detector=soft:phase=laminar:window=long:smoothing=on:formant=preserved:pitchq=quality:channels=together,"
FILTER+="highpass=f=68,lowpass=f=11800,equalizer=f=170:t=q:w=1.05:g=2.6,"
FILTER+="equalizer=f=300:t=q:w=1.15:g=1.2,equalizer=f=520:t=q:w=1.1:g=-1.2,"
FILTER+="equalizer=f=2550:t=q:w=1.0:g=1.8,equalizer=f=7100:t=q:w=1.1:g=-1.8,"
FILTER+="deesser=i=0.18:m=0.45:f=0.30,"
FILTER+="acompressor=threshold=0.095:ratio=3.6:attack=7:release=95:makeup=1.85:knee=2.8,"
FILTER+="asoftclip=type=tanh:threshold=0.92:output=0.95:oversample=4,asplit=3[main][dl][dr];"
FILTER+="[main]pan=stereo|c0=0.96*c0|c1=0.96*c0[m];"
FILTER+="[dl]rubberband=pitch=0.992:formant=preserved:pitchq=quality,highpass=f=130,lowpass=f=6800,adelay=18,volume=0.125,pan=stereo|c0=c0|c1=0*c0[l];"
FILTER+="[dr]rubberband=pitch=1.008:formant=preserved:pitchq=quality,highpass=f=130,lowpass=f=6400,adelay=31,volume=0.105,pan=stereo|c0=0*c0|c1=c0[r];"
FILTER+="[m][l][r]amix=inputs=3:normalize=0,asoftclip=type=tanh:threshold=0.96:output=0.96:oversample=4[out]"

mkdir -p "$(dirname "$OUT")"
ffmpeg -y -v error -i "$IN" -filter_complex "$FILTER" -map '[out]' \
  -ar 48000 -c:a pcm_s24le "$OUT"
echo "ok: $OUT (pitch ${ST} st, tempo ${TEMPO}x, 48 kHz, formante preservado, double 18/31 ms)"
