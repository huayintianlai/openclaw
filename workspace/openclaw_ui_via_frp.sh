#!/usr/bin/env bash
set -euo pipefail

FRP_HOST="${FRP_HOST:-frp5.ccszxc.site}"
FRP_PORT="${FRP_PORT:-37847}"
REMOTE_USER="${REMOTE_USER:-xiaojiujiu2}"
LOCAL_PORT="${LOCAL_PORT:-18789}"
REMOTE_HOST="${REMOTE_HOST:-127.0.0.1}"
REMOTE_PORT="${REMOTE_PORT:-18789}"

usage() {
  cat <<'EOF'
Usage:
  openclaw_ui_via_frp.sh [--background] [--open]

Environment overrides:
  FRP_HOST      FRP server host        default: frp5.ccszxc.site
  FRP_PORT      FRP SSH port           default: 37847
  REMOTE_USER   macOS username         default: xiaojiujiu2
  LOCAL_PORT    local forwarded port   default: 18789
  REMOTE_HOST   remote gateway host    default: 127.0.0.1
  REMOTE_PORT   remote gateway port    default: 18789

Notes:
  1. Run this script on your local machine, not on the Mac mini itself.
  2. Keep the process alive while using the OpenClaw UI.
  3. Then open: http://127.0.0.1:<LOCAL_PORT>/ui/
EOF
}

background=0
open_browser=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --background)
      background=1
      shift
      ;;
    --open)
      open_browser=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

target_url="http://127.0.0.1:${LOCAL_PORT}/ui/"
ssh_args=(
  -p "${FRP_PORT}"
  "${REMOTE_USER}@${FRP_HOST}"
  -N
  -L "${LOCAL_PORT}:${REMOTE_HOST}:${REMOTE_PORT}"
)

echo "OpenClaw UI tunnel target: ${target_url}"
echo "FRP SSH endpoint: ${REMOTE_USER}@${FRP_HOST}:${FRP_PORT}"

if [[ "${background}" -eq 1 ]]; then
  ssh -f "${ssh_args[@]}"
  echo "Tunnel started in background."
  if [[ "${open_browser}" -eq 1 ]]; then
    if command -v open >/dev/null 2>&1; then
      open "${target_url}"
    else
      echo "Browser auto-open is only configured for macOS ('open')."
    fi
  fi
  exit 0
fi

if [[ "${open_browser}" -eq 1 ]] && command -v open >/dev/null 2>&1; then
  open "${target_url}"
fi

exec ssh "${ssh_args[@]}"
