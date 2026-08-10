#!/usr/bin/env bash
# doctor.sh — wrapper. O diagnóstico é ÚNICO para as três skills de vídeo.
# Canônico: ~/.hermes/skills/video-analise/scripts/doctor.sh
# (wrapper e não symlink para sobreviver a cópia/zip do repositório)
set -euo pipefail
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for CAND in "$AQUI/../../video-analise/scripts/doctor.sh" "$HOME/.hermes/skills/video-analise/scripts/doctor.sh"; do
  [ -f "$CAND" ] && exec bash "$CAND" --perfil dublagem "$@"
done
echo "❌ doctor canônico não encontrado (esperado em video-analise/scripts/doctor.sh)" >&2
exit 1
