#!/usr/bin/env bash
# Liga uma sessão do Claude Code na nuvem à frota (acer, server-desktop, pcque001imap)
# pelo Tailscale em modo userspace — o container não tem TUN nem UDP, então o tráfego
# passa pelos relays DERP sobre HTTPS, pelo proxy da sessão.
#
# Pré-requisitos (feitos pelo Álvaro, uma vez, nas configurações do ambiente na nuvem):
#   TS_AUTHKEY           chave de autenticação reutilizável + efêmera, com tag:claude-nuvem
#   FROTA_SSH_KEY_B64    chave privada dedicada em base64 (`base64 -w0 ~/.ssh/claude_nuvem`)
#   Network access       *.tailscale.com liberado
# O passo a passo completo está no README, seção "Frota a partir da nuvem".
#
# Uso:
#   scripts/conectar-frota.sh            instala se faltar, entra na tailnet, configura `ssh acer`
#   scripts/conectar-frota.sh --status   mostra os pares vistos
#   scripts/conectar-frota.sh --sair     sai da tailnet e derruba o tailscaled
set -euo pipefail

SOCK=/tmp/tailscaled.sock
NOME_NO=${TS_HOSTNAME:-claude-nuvem}
CHAVE=$HOME/.ssh/id_frota

ts() { tailscale --socket="$SOCK" "$@"; }

instalar() {
  if command -v tailscale >/dev/null && command -v tailscaled >/dev/null; then
    return
  fi
  local arq tmp
  case "$(uname -m)" in
    x86_64) arq=amd64 ;;
    aarch64) arq=arm64 ;;
    *) echo "arquitetura sem pacote estático: $(uname -m)" >&2; exit 1 ;;
  esac
  tmp=$(mktemp -d)
  local pacote
  pacote=$(curl -fsSL 'https://pkgs.tailscale.com/stable/?mode=json' |
    python3 -c "import json,sys; print(json.load(sys.stdin)['Tarballs']['$arq'])")
  curl -fsSL "https://pkgs.tailscale.com/stable/$pacote" | tar -xz -C "$tmp"
  install -m 755 "$tmp"/tailscale_*/tailscale "$tmp"/tailscale_*/tailscaled /usr/local/bin/
  rm -rf "$tmp"
}

subir() {
  : "${TS_AUTHKEY:?TS_AUTHKEY ausente — cadastre nas variáveis do ambiente e abra uma sessão nova}"
  if ! pgrep -x tailscaled >/dev/null; then
    # state=mem: nada fica no disco; com chave efêmera o nó some da tailnet ao desligar.
    nohup tailscaled --tun=userspace-networking --state=mem: --socket="$SOCK" \
      >/tmp/tailscaled.log 2>&1 &
    for _ in $(seq 40); do [ -S "$SOCK" ] && break; sleep 0.5; done
  fi
  ts up --authkey="$TS_AUTHKEY" --hostname="$NOME_NO" --accept-dns=false --timeout=60s
}

configurar_ssh() {
  : "${FROTA_SSH_KEY_B64:?FROTA_SSH_KEY_B64 ausente — cadastre nas variáveis do ambiente}"
  command -v ssh >/dev/null || { echo "ssh ausente: apt-get install -y openssh-client" >&2; exit 1; }
  mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
  (umask 077 && printf '%s' "$FROTA_SSH_KEY_B64" | base64 -d >"$CHAVE")
  # Bloco próprio no topo do config: a primeira ocorrência de cada opção vence no ssh.
  local cfg=$HOME/.ssh/config bloco resto
  bloco=$(cat <<EOF
# >>> frota (scripts/conectar-frota.sh)
Host acer server-desktop pcque001imap
  ProxyCommand tailscale --socket=$SOCK nc %h %p
  IdentityFile $CHAVE
  IdentitiesOnly yes
  StrictHostKeyChecking accept-new
  UserKnownHostsFile $HOME/.ssh/known_hosts_frota
Host acer
  User acer
# <<< frota
EOF
)
  touch "$cfg"
  resto=$(sed '/^# >>> frota/,/^# <<< frota/d' "$cfg")
  printf '%s\n%s\n' "$bloco" "$resto" >"$cfg"
  chmod 600 "$cfg"
}

case "${1:-}" in
  --status) ts status; exit ;;
  --sair) ts logout || true; pkill -x tailscaled || true; exit ;;
  "") ;;
  *) echo "uso: $0 [--status|--sair]" >&2; exit 2 ;;
esac

instalar
subir
configurar_ssh
ts status
echo "pronto: ssh acer 'hostname && nproc'"
