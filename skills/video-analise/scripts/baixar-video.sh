#!/usr/bin/env bash
# baixar-video.sh — wrapper de yt-dlp para as skills de vídeo do Hermes (FASE 1, base).
#
# NÃO INSTALA NADA. Se o yt-dlp utilizável não existir, o script diz o que fazer e sai.
#
# Uso:
#   ./baixar-video.sh <URL> [--slug <slug>] [--cookies <navegador>] [--audio-so] [--dry-run]
#
#   --slug <slug>        nome da pasta de destino (default: derivado da URL)
#   --cookies <nav>      chrome | chromium | firefox | brave — para Instagram/conteúdo logado
#   --audio-so           baixa só a faixa de áudio (m4a) — útil para transcrição
#   --dry-run            mostra o que faria, sem baixar
#
# Destino:  ~/Documentos/Video_Studio/entradas/<slug>/
#             fonte.<ext>          o arquivo baixado
#             fonte.info.json      metadados do yt-dlp
#             download.log         log da execução
#
# (A pasta `entradas/` é a zona de pouso do material bruto. A `refs/<slug>/` do
#  PLANO_HERMES §5.1 é a pasta de ANÁLISE, criada na fase seguinte a partir daqui.)

set -uo pipefail

# ---- argumentos -------------------------------------------------------------
URL=""; SLUG=""; COOKIES=""; AUDIO_SO=0; DRYRUN=0
while [ $# -gt 0 ]; do
  case "$1" in
    --slug)
      [ "$#" -ge 2 ] && [ -n "$2" ] && [[ "$2" != -* ]] || { echo "❌ --slug exige valor" >&2; exit 2; }
      SLUG=$2; shift 2 ;;
    --cookies)
      [ "$#" -ge 2 ] && [ -n "$2" ] && [[ "$2" != -* ]] || { echo "❌ --cookies exige valor" >&2; exit 2; }
      COOKIES=$2; shift 2 ;;
    --audio-so) AUDIO_SO=1; shift ;;
    --dry-run) DRYRUN=1; shift ;;
    -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
    -*) echo "❌ opção desconhecida: $1" >&2; exit 2 ;;
    *) [ -z "$URL" ] && URL="$1" || { echo "❌ URL informada duas vezes" >&2; exit 2; }; shift ;;
  esac
done
[ -n "$URL" ] || { echo "uso: $0 <URL> [--slug s] [--cookies chrome] [--audio-so] [--dry-run]" >&2; exit 2; }

# ---- normalizar URL ---------------------------------------------------------
# Instagram cola ?igsh=…; YouTube cola ?si=…&list=… — lixo que polui o slug e
# às vezes muda o alvo do download (list= baixa a playlist inteira).
URL_LIMPA=$(python3 -c '
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
u = urlsplit(sys.argv[1])
drop = {"igsh", "igshid", "si", "feature", "list", "index", "pp"}
q = [(k, v) for k, v in parse_qsl(u.query, keep_blank_values=True)
     if k not in drop and not k.startswith("utm_")]
print(urlunsplit((u.scheme, u.netloc, u.path, urlencode(q), u.fragment)))
' "$URL") || { echo "❌ URL inválida" >&2; exit 2; }
[ "$URL_LIMPA" != "$URL" ] && echo "🧹 URL normalizada: $URL_LIMPA"

# ---- escolher o yt-dlp ------------------------------------------------------
# Gotcha (README §3.4): o yt-dlp do apt (2024.04.09) responde
# "Requested format is not available" no YouTube — extractor desatualizado.
# Preferir sempre uma instalação via uv/pipx.
YTDLP=""
for cand in "$HOME/.local/bin/yt-dlp" "$HOME/.local/share/uv/tools/yt-dlp/bin/yt-dlp" "$(command -v yt-dlp || true)"; do
  [ -n "$cand" ] && [ -x "$cand" ] && { YTDLP="$cand"; break; }
done
[ -n "$YTDLP" ] || {
  echo "❌ yt-dlp não encontrado."
  echo "   Instale (fora deste script):  uv tool install yt-dlp"
  exit 1
}
YTV=$("$YTDLP" --version 2>/dev/null | head -1)
YTANO=${YTV%%.*}
ANTIGO=0
if ! [ "${YTANO:-0}" -ge 2025 ] 2>/dev/null; then
  ANTIGO=1
  echo "⚠️  yt-dlp $YTV ($YTDLP) é a versão do apt — QUEBRADA para YouTube."
fi
case "$URL_LIMPA" in
  *youtube.com*|*youtu.be*)
    if [ "$ANTIGO" = 1 ]; then
      echo "❌ Este link é do YouTube e o yt-dlp disponível é o do apt: vai falhar com"
      echo "   'Requested format is not available'. Instale o novo antes:"
      echo "     uv tool install yt-dlp"
      echo "   (este script não instala nada de propósito)"
      # em --dry-run seguimos para mostrar slug/destino; download real é abortado
      [ "$DRYRUN" = 1 ] || exit 1
    fi ;;
esac

# ---- slug e destino ---------------------------------------------------------
if [ -z "$SLUG" ]; then
  # slug legível por plataforma; o slug é a identidade do material em todo o pipeline
  case "$URL_LIMPA" in
    *instagram.com/reel*|*instagram.com/p/*)
      SLUG="ig-$(sed -E 's#.*instagram\.com/(reel|reels|p)/([^/?]+).*#\2#' <<<"$URL_LIMPA")" ;;
    *youtube.com/shorts*)
      SLUG="yt-$(sed -E 's#.*shorts/([^/?]+).*#\1#' <<<"$URL_LIMPA")" ;;
    *youtube.com/watch*)
      SLUG="yt-$(sed -E 's#.*[?&]v=([^&]+).*#\1#' <<<"$URL_LIMPA")" ;;
    *youtu.be/*)
      SLUG="yt-$(sed -E 's#.*youtu\.be/([^/?]+).*#\1#' <<<"$URL_LIMPA")" ;;
    *tiktok.com/*/video/*)
      SLUG="tt-$(sed -E 's#.*/video/([0-9]+).*#\1#' <<<"$URL_LIMPA")" ;;
    *)
      SLUG=$(sed -E 's#https?://(www\.)?##; s#[^a-zA-Z0-9]+#-#g; s#^-+|-+$##g' <<<"$URL_LIMPA" | cut -c1-60) ;;
  esac
  SLUG=$(tr '[:upper:]' '[:lower:]' <<<"$SLUG")
fi
[ -n "$SLUG" ] || SLUG="video-$(date +%Y%m%d-%H%M%S)"
case "$SLUG" in *..*|*/*|*\\*) echo "❌ slug inseguro: $SLUG" >&2; exit 2 ;; esac
[[ "$SLUG" =~ ^[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}$ ]] || {
  echo "❌ slug inválido; use 1–80 caracteres [a-zA-Z0-9._-]" >&2
  exit 2
}
case "$COOKIES" in ""|chrome|chromium|firefox|brave) ;; *) echo "❌ navegador de cookies inválido: $COOKIES" >&2; exit 2 ;; esac
DEST="$HOME/Documentos/Video_Studio/entradas/$SLUG"

# ---- montar o comando -------------------------------------------------------
ARGS=(
  --no-playlist                 # link com &list= não vira download de playlist inteira
  --write-info-json
  --no-progress
  --retries 3
  --output "$DEST/fonte.%(ext)s"
)
if [ "$AUDIO_SO" = 1 ]; then
  ARGS+=( -f "bestaudio[ext=m4a]/bestaudio" )
else
  # mp4 quando dá; senão o melhor disponível (não força merge impossível)
  ARGS+=( -f "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b" --merge-output-format mp4 )
fi
[ -n "$COOKIES" ] && ARGS+=( --cookies-from-browser "$COOKIES" )

if [ "$DRYRUN" = 1 ]; then
  echo "🔍 dry-run — nada será baixado"
  echo "   yt-dlp : $YTDLP ($YTV)"
  echo "   slug   : $SLUG"
  echo "   destino: $DEST"
  printf '   comando: %s' "$YTDLP"; printf ' %q' "${ARGS[@]}" "$URL_LIMPA"; echo
  exit 0
fi

mkdir -p "$DEST" || { echo "❌ não consegui criar $DEST" >&2; exit 1; }
LOG="$DEST/download.log"
echo "⬇️  baixando → $DEST"
"$YTDLP" "${ARGS[@]}" "$URL_LIMPA" 2>&1 | tee "$LOG"
RC=${PIPESTATUS[0]}

# ---- diagnóstico de falha ---------------------------------------------------
if [ "$RC" -ne 0 ]; then
  echo
  echo "❌ yt-dlp falhou (rc=$RC). Log: $LOG"
  if grep -qiE 'login required|rate-limit|not available|cookies|restricted' "$LOG" 2>/dev/null; then
    case "$URL_LIMPA" in
      *instagram.com*)
        echo "   → Instagram exige sessão logada. Dois caminhos, nesta ordem:"
        echo "     1) repetir com cookies do navegador:  $0 '$URL' --cookies chrome"
        echo "     2) se ainda falhar, o Hermes abre a tool \`browser\` na sessão logada"
        echo "        e captura o arquivo (PLANO_HERMES §1.3 passo 4). Nunca responder 'não consegui'." ;;
      *)
        echo "   → conteúdo restrito. Tentar:  $0 '$URL' --cookies chrome" ;;
    esac
  fi
  exit "$RC"
fi

# ---- relatório --------------------------------------------------------------
ARQ=$(find "$DEST" -maxdepth 1 -name 'fonte.*' ! -name '*.info.json' ! -name '*.part' | head -1)
if [ -z "$ARQ" ]; then
  echo "⚠️  yt-dlp terminou com sucesso mas nenhum arquivo 'fonte.*' apareceu em $DEST"
  exit 1
fi
TAM=$(du -h "$ARQ" | cut -f1)
DUR=""
command -v ffprobe >/dev/null 2>&1 && DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$ARQ" 2>/dev/null | cut -d. -f1)
echo
echo "✅ pronto"
echo "   arquivo : $ARQ ($TAM${DUR:+, ${DUR}s})"
echo "   metadados: $DEST/fonte.info.json"
echo "   slug    : $SLUG"
