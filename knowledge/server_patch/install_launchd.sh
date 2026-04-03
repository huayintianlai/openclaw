#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LAUNCH_AGENTS_DIR="${HOME}/Library/LaunchAgents"
INSTALL_DIR="${HOME}/.openclaw-services/knowledge-server"
SERVICE_LABEL="ai.openclaw.knowledge-server"
WATCHDOG_LABEL="ai.openclaw.knowledge-watchdog"
SERVICE_PLIST="${LAUNCH_AGENTS_DIR}/${SERVICE_LABEL}.plist"
WATCHDOG_PLIST="${LAUNCH_AGENTS_DIR}/${WATCHDOG_LABEL}.plist"
SERVICE_RUNNER="${INSTALL_DIR}/run_local.sh"
WATCHDOG_RUNNER="${INSTALL_DIR}/watchdog.sh"
DEEP_HEALTHCHECK_RUNNER="${INSTALL_DIR}/deep_healthcheck.sh"
MEMORY_E2E_RUNNER="${INSTALL_DIR}/memory_e2e_check.js"
APP_COPY="${INSTALL_DIR}/app.py"
INSTALL_DATA_DIR="${INSTALL_DIR}/data"
LOG_DIR="${ROOT_DIR}/logs"
STATE_DIR="${ROOT_DIR}/state/knowledge-server"
GATEWAY_PLIST="${LAUNCH_AGENTS_DIR}/ai.openclaw.gateway.plist"
USER_ID="$(id -u)"
SERVICE_STDOUT="/tmp/${SERVICE_LABEL}.launchd.log"
SERVICE_STDERR="/tmp/${SERVICE_LABEL}.launchd.err.log"
WATCHDOG_STDOUT="/tmp/${WATCHDOG_LABEL}.launchd.log"
WATCHDOG_STDERR="/tmp/${WATCHDOG_LABEL}.launchd.err.log"

mkdir -p "${LAUNCH_AGENTS_DIR}" "${LOG_DIR}" "${STATE_DIR}" "${INSTALL_DIR}"

cp "${ROOT_DIR}/knowledge/server_patch/run_local.sh" "${SERVICE_RUNNER}"
cp "${ROOT_DIR}/knowledge/server_patch/watchdog.sh" "${WATCHDOG_RUNNER}"
cp "${ROOT_DIR}/knowledge/server_patch/deep_healthcheck.sh" "${DEEP_HEALTHCHECK_RUNNER}"
cp "${ROOT_DIR}/knowledge/server_patch/memory_e2e_check.js" "${MEMORY_E2E_RUNNER}"
cp "${ROOT_DIR}/knowledge/server_patch/app.py" "${APP_COPY}"
chmod +x "${SERVICE_RUNNER}" "${WATCHDOG_RUNNER}" "${DEEP_HEALTHCHECK_RUNNER}" "${MEMORY_E2E_RUNNER}"

if [[ ! -f "${INSTALL_DATA_DIR}/kb.sqlite" && -d "${ROOT_DIR}/knowledge/server_patch/data" ]]; then
  mkdir -p "${INSTALL_DATA_DIR}"
  rsync -a "${ROOT_DIR}/knowledge/server_patch/data/" "${INSTALL_DATA_DIR}/"
fi

/usr/bin/python3 - <<'PY' "${INSTALL_DATA_DIR}"
import sqlite3
import sys
from pathlib import Path

install_data_dir = Path(sys.argv[1])
db_path = install_data_dir / "kb.sqlite"
if not db_path.exists():
    raise SystemExit(0)

conn = sqlite3.connect(db_path)
try:
    rows = conn.execute("SELECT file_id, sha256, filename FROM files").fetchall()
    for _, sha256_value, filename in rows:
      storage_path = install_data_dir / "files" / sha256_value / filename
      conn.execute(
          "UPDATE files SET storage_path = ? WHERE sha256 = ? AND filename = ?",
          (str(storage_path), sha256_value, filename),
      )
    conn.commit()
finally:
    conn.close()
PY

plist_env() {
  local key="$1"
  /usr/libexec/PlistBuddy -c "Print :EnvironmentVariables:${key}" "${GATEWAY_PLIST}" 2>/dev/null || true
}

PATH_VALUE="$(plist_env PATH)"
HOME_VALUE="$(plist_env HOME)"
HTTP_PROXY_VALUE="$(plist_env HTTP_PROXY)"
HTTPS_PROXY_VALUE="$(plist_env HTTPS_PROXY)"
ALL_PROXY_VALUE="$(plist_env ALL_PROXY)"
NO_PROXY_VALUE="$(plist_env NO_PROXY)"

PATH_VALUE="${PATH_VALUE:-${PATH}}"
HOME_VALUE="${HOME_VALUE:-${HOME}}"
NO_PROXY_VALUE="${NO_PROXY_VALUE:-localhost,127.0.0.1,qdrant.99uwen.com}"

cat >"${SERVICE_PLIST}" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${SERVICE_LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${SERVICE_RUNNER}</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>HOME</key>
    <string>${HOME_VALUE}</string>
    <key>OPENCLAW_RUNTIME_ROOT</key>
    <string>${ROOT_DIR}</string>
    <key>OPENCLAW_KNOWLEDGE_APP_DIR</key>
    <string>${INSTALL_DIR}</string>
    <key>PATH</key>
    <string>${PATH_VALUE}</string>
    <key>HTTP_PROXY</key>
    <string>${HTTP_PROXY_VALUE}</string>
    <key>HTTPS_PROXY</key>
    <string>${HTTPS_PROXY_VALUE}</string>
    <key>ALL_PROXY</key>
    <string>${ALL_PROXY_VALUE}</string>
    <key>NO_PROXY</key>
    <string>${NO_PROXY_VALUE}</string>
  </dict>
  <key>WorkingDirectory</key>
  <string>${HOME_VALUE}</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>ThrottleInterval</key>
  <integer>5</integer>
  <key>StandardOutPath</key>
  <string>${SERVICE_STDOUT}</string>
  <key>StandardErrorPath</key>
  <string>${SERVICE_STDERR}</string>
</dict>
</plist>
PLIST

cat >"${WATCHDOG_PLIST}" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${WATCHDOG_LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${WATCHDOG_RUNNER}</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>HOME</key>
    <string>${HOME_VALUE}</string>
    <key>OPENCLAW_RUNTIME_ROOT</key>
    <string>${ROOT_DIR}</string>
    <key>OPENCLAW_KNOWLEDGE_APP_DIR</key>
    <string>${INSTALL_DIR}</string>
    <key>PATH</key>
    <string>${PATH_VALUE}</string>
    <key>HTTP_PROXY</key>
    <string>${HTTP_PROXY_VALUE}</string>
    <key>HTTPS_PROXY</key>
    <string>${HTTPS_PROXY_VALUE}</string>
    <key>ALL_PROXY</key>
    <string>${ALL_PROXY_VALUE}</string>
    <key>NO_PROXY</key>
    <string>${NO_PROXY_VALUE}</string>
  </dict>
  <key>WorkingDirectory</key>
  <string>${HOME_VALUE}</string>
  <key>RunAtLoad</key>
  <true/>
  <key>StartInterval</key>
  <integer>60</integer>
  <key>StandardOutPath</key>
  <string>${WATCHDOG_STDOUT}</string>
  <key>StandardErrorPath</key>
  <string>${WATCHDOG_STDERR}</string>
</dict>
</plist>
PLIST

plutil -lint "${SERVICE_PLIST}" >/dev/null
plutil -lint "${WATCHDOG_PLIST}" >/dev/null

launchctl bootout "gui/${USER_ID}" "${SERVICE_PLIST}" >/dev/null 2>&1 || true
launchctl bootout "gui/${USER_ID}" "${WATCHDOG_PLIST}" >/dev/null 2>&1 || true

launchctl bootstrap "gui/${USER_ID}" "${SERVICE_PLIST}"
launchctl bootstrap "gui/${USER_ID}" "${WATCHDOG_PLIST}"
launchctl kickstart -k "gui/${USER_ID}/${SERVICE_LABEL}"
launchctl kickstart -k "gui/${USER_ID}/${WATCHDOG_LABEL}"

echo "Installed ${SERVICE_LABEL} and ${WATCHDOG_LABEL}"
echo "Service plist: ${SERVICE_PLIST}"
echo "Watchdog plist: ${WATCHDOG_PLIST}"
echo "Install dir: ${INSTALL_DIR}"
echo "Service stdout: ${SERVICE_STDOUT}"
echo "Service stderr: ${SERVICE_STDERR}"
