#!/usr/bin/env bash
# doctor.sh — diagnóstico do ambiente das skills de vídeo do Hermes (FASE 1, base).
#
# NÃO INSTALA NADA. Só verifica e reporta. É o "imap doctor" das skills de vídeo:
# roda ANTES de prometer resultado ao Álvaro (PLANO_HERMES.md §1.3 passo 0).
#
# Uso:
#   ./doctor.sh [--curto|--json] [--perfil analise|criacao|dublagem]
#
# Saída:
#   0 = tudo que a BASE precisa está presente (ffmpeg + yt-dlp utilizável)
#   1 = falta algo essencial da base
#   2 = erro de uso

set -uo pipefail

MODO="completo"
PERFIL="analise"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --curto) MODO="curto"; shift ;;
    --json) MODO="json"; shift ;;
    --perfil)
      [ "$#" -ge 2 ] || { echo "uso: $0 [--curto|--json] [--perfil analise|criacao|dublagem]" >&2; exit 2; }
      PERFIL=$2
      shift 2
      ;;
    *) echo "uso: $0 [--curto|--json] [--perfil analise|criacao|dublagem]" >&2; exit 2 ;;
  esac
done
case "$PERFIL" in analise|criacao|dublagem) ;; *) echo "perfil inválido: $PERFIL" >&2; exit 2 ;; esac

VENV_PY="$HOME/.hermes/hermes-agent/venv/bin/python3"
[ -x "$VENV_PY" ] || VENV_PY="$(command -v python3 || true)"

# ---- coleta -----------------------------------------------------------------
# Cada linha de RES: chave|nivel|estado|detalhe
#   nivel: base (bloqueia a fase 1) | fase2 (pipeline completo, ainda não é agora)
#   estado: ok | aviso | falta
RES=()
add() { RES+=("$1|$2|$3|$4"); }

ver_bin() { command -v "$1" >/dev/null 2>&1; }

HAS_FFMPEG=0; HAS_FFPROBE=0; HAS_YTDLP=0; HAS_EDGE=0; HAS_RUBBERBAND=0; HAS_DEMUCS=0; HAS_NUMPY=0

# --- ffmpeg / ffprobe
if ver_bin ffmpeg; then
  HAS_FFMPEG=1
  FFV=$(ffmpeg -version 2>/dev/null | head -1 | awk '{print $3}')
  # NOTA: capturar a lista UMA vez. `ffmpeg | grep -q` com `set -o pipefail` mata o
  # ffmpeg com SIGPIPE (141) e o teste dá falso-negativo silencioso.
  LISTA_FILTROS=$(ffmpeg -hide_banner -filters 2>/dev/null)
  LISTA_ENCODERS=$(ffmpeg -hide_banner -encoders 2>/dev/null)
  FILTROS=""
  for f in zoompan xfade subtitles ass loudnorm; do
    grep -qw -- "$f" <<<"$LISTA_FILTROS" && FILTROS="$FILTROS $f"
  done
  VAAPI=$(grep -c 'h264_vaapi' <<<"$LISTA_ENCODERS" || true)
  DET="v$FFV · filtros:${FILTROS:- nenhum}"
  [ "${VAAPI:-0}" -gt 0 ] && DET="$DET · VAAPI(h264) sim" || DET="$DET · VAAPI não"
  add ffmpeg base ok "$DET"
else
  add ffmpeg base falta "ausente — hermes postinstall normalmente instala"
fi
if ver_bin ffprobe; then
  HAS_FFPROBE=1
  add ffprobe base ok "$(ffprobe -version 2>/dev/null | head -1 | awk '{print $3}')"
else
  add ffprobe base falta "ausente"
fi

# --- yt-dlp (gotcha nº 1 do README §3.4: o do apt está quebrado para YouTube)
YTDLP_BIN=""
for cand in "$HOME/.local/bin/yt-dlp" "$HOME/.local/share/uv/tools/yt-dlp/bin/yt-dlp" "$(command -v yt-dlp || true)"; do
  [ -n "$cand" ] && [ -x "$cand" ] && { YTDLP_BIN="$cand"; break; }
done
if [ -n "$YTDLP_BIN" ]; then
  YTV=$("$YTDLP_BIN" --version 2>/dev/null | head -1)
  YTANO=${YTV%%.*}
  if [ "${YTANO:-0}" -ge 2025 ] 2>/dev/null; then
    HAS_YTDLP=1
    add yt-dlp base ok "$YTV ($YTDLP_BIN)"
  else
    add yt-dlp base aviso "$YTV ($YTDLP_BIN) — versão do apt, QUEBRADA para YouTube ('Requested format is not available'). Substituir por: uv tool install yt-dlp"
  fi
else
  add yt-dlp base falta "ausente"
fi

# --- transcrição
if [ -n "$VENV_PY" ] && "$VENV_PY" -c 'import numpy' 2>/dev/null; then
  HAS_NUMPY=1
  add numpy base ok "módulo disponível em $VENV_PY"
else
  add numpy base falta "necessário para analisar BPM/onsets"
fi
if [ -n "$VENV_PY" ] && "$VENV_PY" -c 'import faster_whisper' 2>/dev/null; then
  add faster-whisper fase2 ok "módulo python disponível em $VENV_PY"
else
  add faster-whisper fase2 falta "não instalado (transcrição é da fase seguinte)"
fi
ver_bin whisper && add whisper-cli fase2 ok "$(command -v whisper)" \
                || add whisper-cli fase2 falta "CLI ausente — faster_whisper cobre o caso"

# --- TTS (edge, grátis — decisão §7.6 do PLANO_HERMES)
EDGE_BIN=""
for cand in "$HOME/.hermes/hermes-agent/venv/bin/edge-tts" "$(command -v edge-tts || true)"; do
  [ -n "$cand" ] && [ -x "$cand" ] && { EDGE_BIN="$cand"; break; }
done
if [ -n "$EDGE_BIN" ]; then
  HAS_EDGE=1
  add edge-tts base ok "$EDGE_BIN"
else
  add edge-tts base falta "ausente — é o motor de voz padrão (sem custo)"
fi
ver_bin piper && add piper fase2 ok "$(command -v piper)" || add piper fase2 falta "TTS offline opcional"

# --- OCR (legendas queimadas)
if ver_bin tesseract; then
  IDIOMAS=$(tesseract --list-langs 2>/dev/null | tail -n +2 | tr '\n' ' ')
  add tesseract fase2 ok "$(tesseract --version 2>&1 | head -1 | awk '{print $2}') · idiomas: ${IDIOMAS:-?}"
else
  add tesseract fase2 falta "ausente — OCR de legenda queimada"
fi

# --- resto do pipeline (fase seguinte, só inventário)
for mod in demucs scenedetect librosa; do
  if [ -n "$VENV_PY" ] && "$VENV_PY" -c "import $mod" 2>/dev/null; then
    [ "$mod" = demucs ] && HAS_DEMUCS=1
    add "$mod" fase2 ok "módulo python disponível"
  else
    add "$mod" fase2 falta "não instalado"
  fi
done
if [ "${LISTA_FILTROS:-}" ] && grep -qw -- rubberband <<<"$LISTA_FILTROS"; then
  HAS_RUBBERBAND=1
  add rubberband fase2 ok "filtro FFmpeg disponível (tempo/pitch + formante preservado)"
elif ver_bin rubberband; then
  HAS_RUBBERBAND=1
  add rubberband fase2 ok "CLI disponível: $(command -v rubberband)"
else
  add rubberband fase2 falta "nem filtro FFmpeg nem CLI disponíveis"
fi

# --- runtimes
[ -n "$VENV_PY" ] && add python3 base ok "$("$VENV_PY" --version 2>&1 | awk '{print $2}') ($VENV_PY)" \
                  || add python3 base falta "ausente"
ver_bin uv    && add uv    base ok "$(uv --version 2>/dev/null | awk '{print $2}')" || add uv base aviso "ausente — é o caminho recomendado para o yt-dlp novo"
ver_bin node  && add node  fase2 ok "$(node --version)" || add node fase2 falta "ausente"

# --- credenciais (presença apenas; NUNCA imprimir valor)
ENVF="$HOME/.hermes/.env"
if [ -f "$ENVF" ]; then
  for chave in GROQ_API_KEY DEEPSEEK_API_KEY; do
    if grep -qE "^${chave}=.+" "$ENVF" 2>/dev/null; then
      add "$chave" base ok "presente no ~/.hermes/.env (valor não exibido)"
    else
      add "$chave" base aviso "ausente no ~/.hermes/.env"
    fi
  done
  # decisão §7.1/§7.5: Grok 4.5 via API do Cursor é o fallback de visão — ainda NÃO configurado de propósito
  if grep -qE "^(CURSOR_API_KEY|XAI_API_KEY)=.+" "$ENVF" 2>/dev/null; then
    add fallback-visao fase2 ok "chave de fallback (Cursor/Grok) presente"
  else
    add fallback-visao fase2 falta "fallback de visão (Grok 4.5 via API do Cursor) previsto e NÃO configurado — decisão §7.5, config é passo futuro"
  fi
else
  add env-hermes base aviso "~/.hermes/.env não encontrado"
fi

# --- disco e pastas de trabalho
LIVRE=$(df -BG --output=avail "$HOME" 2>/dev/null | tail -1 | tr -dc '0-9')
if [ "${LIVRE:-0}" -ge 20 ]; then
  add disco base ok "${LIVRE} GB livres em \$HOME"
else
  add disco base aviso "${LIVRE:-?} GB livres — pipeline de vídeo quer 20 GB+"
fi
STUDIO="$HOME/Documentos/Video_Studio"
if [ -d "$STUDIO" ]; then
  add video-studio base ok "$STUDIO"
else
  add video-studio base aviso "$STUDIO não existe (baixar-video.sh cria sozinho)"
fi

# ---- saída ------------------------------------------------------------------
n_falta_base=0; n_aviso=0; n_falta_f2=0
for l in "${RES[@]}"; do
  IFS='|' read -r k niv est det <<<"$l"
  [ "$est" = falta ] && [ "$niv" = base ]  && n_falta_base=$((n_falta_base+1))
  [ "$est" = falta ] && [ "$niv" = fase2 ] && n_falta_f2=$((n_falta_f2+1))
  [ "$est" = aviso ] && n_aviso=$((n_aviso+1))
done

FALTANDO_PERFIL=()
[ "$HAS_FFMPEG" -eq 1 ] || FALTANDO_PERFIL+=(ffmpeg)
[ "$HAS_FFPROBE" -eq 1 ] || FALTANDO_PERFIL+=(ffprobe)
case "$PERFIL" in
  analise)
    [ "$HAS_YTDLP" -eq 1 ] || FALTANDO_PERFIL+=(yt-dlp-atual)
    [ "$HAS_NUMPY" -eq 1 ] || FALTANDO_PERFIL+=(numpy)
    ;;
  criacao)
    [ "$HAS_EDGE" -eq 1 ] || FALTANDO_PERFIL+=(edge-tts)
    [ "$HAS_RUBBERBAND" -eq 1 ] || FALTANDO_PERFIL+=(rubberband)
    ;;
  dublagem)
    [ "$HAS_EDGE" -eq 1 ] || FALTANDO_PERFIL+=(edge-tts)
    [ "$HAS_RUBBERBAND" -eq 1 ] || FALTANDO_PERFIL+=(rubberband)
    [ "$HAS_DEMUCS" -eq 1 ] || FALTANDO_PERFIL+=(demucs)
    ;;
esac
PERFIL_OK=false
[ "${#FALTANDO_PERFIL[@]}" -eq 0 ] && PERFIL_OK=true

if [ "$MODO" = json ]; then
  printf '{\n  "perfil": "%s",\n  "perfil_ok": %s,\n  "faltando_perfil": %d,\n  "base_ok": %s,\n  "faltando_base": %d,\n  "avisos": %d,\n  "faltando_fase2": %d,\n  "itens": [\n' \
    "$PERFIL" "$PERFIL_OK" "${#FALTANDO_PERFIL[@]}" "$([ $n_falta_base -eq 0 ] && echo true || echo false)" "$n_falta_base" "$n_aviso" "$n_falta_f2"
  primeiro=1
  for l in "${RES[@]}"; do
    IFS='|' read -r k niv est det <<<"$l"
    [ $primeiro -eq 0 ] && printf ',\n'; primeiro=0
    det_esc=${det//\"/\\\"}
    printf '    {"item": "%s", "nivel": "%s", "estado": "%s", "detalhe": "%s"}' "$k" "$niv" "$est" "$det_esc"
  done
  printf '\n  ]\n}\n'
  [ "$PERFIL_OK" = true ] && exit 0 || exit 1
fi

icone() { case "$1" in ok) printf '✅';; aviso) printf '⚠️ ';; falta) printf '❌';; esac; }

if [ "$MODO" = completo ]; then
  echo "🩺 doctor — skills de vídeo do Hermes · perfil $PERFIL ($(date '+%Y-%m-%d %H:%M'))"
  echo
  echo "── BASE (precisa estar de pé agora) ──"
  for l in "${RES[@]}"; do
    IFS='|' read -r k niv est det <<<"$l"
    [ "$niv" = base ] && printf '%s %-18s %s\n' "$(icone "$est")" "$k" "$det"
  done
  echo
  echo "── PIPELINE COMPLETO (fase seguinte — só inventário) ──"
  for l in "${RES[@]}"; do
    IFS='|' read -r k niv est det <<<"$l"
    [ "$niv" = fase2 ] && printf '%s %-18s %s\n' "$(icone "$est")" "$k" "$det"
  done
  echo
fi

if [ "$PERFIL_OK" = true ]; then
  echo "Resumo: perfil $PERFIL OK · ${n_aviso} aviso(s) · ${n_falta_f2} item(ns) opcionais/avançados ausentes."
  exit 0
else
  echo "Resumo: ❌ perfil $PERFIL bloqueado por: ${FALTANDO_PERFIL[*]}"
  echo "Este script não instala nada."
  exit 1
fi
