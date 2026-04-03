#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${OPENCLAW_RUNTIME_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
STATE_DIR="${ROOT_DIR}/state/knowledge-server"
LOG_DIR="${ROOT_DIR}/logs"
LOCK_DIR="${STATE_DIR}/watchdog.lock"
SERVICE_LABEL="ai.openclaw.knowledge-server"
FULL_E2E_INTERVAL_SECONDS="${FULL_E2E_INTERVAL_SECONDS:-900}"
BASE_URL="${BASE_URL:-http://127.0.0.1:${PORT:-8002}}"

mkdir -p "${STATE_DIR}" "${LOG_DIR}"

if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
  echo "knowledge-watchdog: another instance is already running"
  exit 0
fi

cleanup_lock() {
  rmdir "${LOCK_DIR}" >/dev/null 2>&1 || true
}
trap cleanup_lock EXIT

restart_service() {
  local uid
  uid="$(id -u)"
  echo "knowledge-watchdog: restarting ${SERVICE_LABEL}"
  launchctl kickstart -k "gui/${uid}/${SERVICE_LABEL}" >/dev/null 2>&1 || \
    launchctl kickstart -k "${SERVICE_LABEL}" >/dev/null 2>&1 || true
  wait_for_service
}

wait_for_service() {
  local attempt
  for attempt in $(seq 1 20); do
    if curl -fsS --max-time 5 "${BASE_URL}/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "knowledge-watchdog: service did not become healthy after restart"
  return 1
}

retry_once() {
  local description="$1"
  shift
  if "$@"; then
    return 0
  fi
  echo "knowledge-watchdog: ${description} failed, retrying once before restart"
  sleep 3
  "$@"
}

run_deep_check() {
  "${SCRIPT_DIR}/deep_healthcheck.sh"
}

run_memory_e2e() {
  node "${SCRIPT_DIR}/memory_e2e_check.js"
}

if ! retry_once "deep healthcheck" run_deep_check; then
  echo "knowledge-watchdog: deep healthcheck failed before restart"
  restart_service
  retry_once "deep healthcheck after restart" run_deep_check
fi

last_full_file="${STATE_DIR}/last-memory-e2e.txt"
now_epoch="$(date +%s)"
last_epoch="0"
if [[ -f "${last_full_file}" ]]; then
  last_epoch="$(cat "${last_full_file}" 2>/dev/null || echo 0)"
fi

if (( now_epoch - last_epoch >= FULL_E2E_INTERVAL_SECONDS )); then
  if ! retry_once "memory e2e" run_memory_e2e; then
    echo "knowledge-watchdog: memory e2e failed before restart"
    restart_service
    retry_once "deep healthcheck after memory restart" run_deep_check
    retry_once "memory e2e after restart" run_memory_e2e
  fi
  printf '%s\n' "${now_epoch}" >"${last_full_file}"
fi

echo "knowledge-watchdog: all checks passed"
