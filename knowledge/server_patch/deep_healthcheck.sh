#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${OPENCLAW_RUNTIME_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
ENV_FILE="${ROOT_DIR}/.env"
BASE_URL="${BASE_URL:-http://127.0.0.1:${PORT:-8002}}"
TMP_DIR="${ROOT_DIR}/state/knowledge-server"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
mkdir -p "${TMP_DIR}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="$(command -v python3 || true)"
fi

if [[ -f "${ENV_FILE}" ]]; then
  eval "$(
    python3 - "${ENV_FILE}" <<'PY'
import shlex
import sys
from pathlib import Path

for raw_line in Path(sys.argv[1]).read_text().splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    print(f"export {key}={shlex.quote(value)}")
PY
  )"
fi

API_TOKEN="${API_TOKEN:-${KNOWLEDGE_API_TOKEN:-}}"
OPENAI_TOKEN="${MEM0_OPENAI_API_KEY:-${OPENAI_API_KEY:-}}"
QDRANT_URL="${QDRANT_URL:-https://qdrant.99uwen.com}"
EMBED_MODEL="${MEM0_EMBEDDER_MODEL:-text-embedding-3-small}"
CHAT_MODEL="${MEM0_LLM_MODEL:-gpt-4o-mini}"

curl_json() {
  local output_file="$1"
  shift
  local attempt
  local max_attempts=3
  for attempt in $(seq 1 "${max_attempts}"); do
    if curl -fsS --max-time 30 "$@" >"${output_file}"; then
      return 0
    fi
    if [[ "${attempt}" -lt "${max_attempts}" ]]; then
      sleep 2
    fi
  done
  return 1
}

health_file="${TMP_DIR}/deep-health-health.json"
embed_file="${TMP_DIR}/deep-health-embed.json"
chat_file="${TMP_DIR}/deep-health-chat.json"
qdrant_file="${TMP_DIR}/deep-health-qdrant.json"
search_file="${TMP_DIR}/deep-health-search.json"

curl_json "${health_file}" "${BASE_URL}/health"
"${PYTHON_BIN}" - <<'PY' "${health_file}"
import json, sys
payload = json.load(open(sys.argv[1]))
if payload.get("status") != "ok":
    raise SystemExit("health endpoint not ok")
print("knowledge-server: /health ok")
PY

curl_json \
  "${embed_file}" \
  -X POST "${BASE_URL}/openai/v1/embeddings" \
  -H "Authorization: Bearer ${OPENAI_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"${EMBED_MODEL}\",\"input\":\"openclaw knowledge deep healthcheck\"}"
"${PYTHON_BIN}" - <<'PY' "${embed_file}"
import json, sys
payload = json.load(open(sys.argv[1]))
if not payload.get("data"):
    raise SystemExit("embeddings response missing data")
print("knowledge-server: embeddings ok")
PY

curl_json \
  "${chat_file}" \
  -X POST "${BASE_URL}/openai/v1/chat/completions" \
  -H "Authorization: Bearer ${OPENAI_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"${CHAT_MODEL}\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply with OK only.\"}],\"max_tokens\":5}"
"${PYTHON_BIN}" - <<'PY' "${chat_file}"
import json, sys
payload = json.load(open(sys.argv[1]))
choices = payload.get("choices") or []
if not choices:
    raise SystemExit("chat response missing choices")
print("knowledge-server: chat completions ok")
PY

curl_json "${qdrant_file}" -H "api-key: ${QDRANT_API_KEY}" "${QDRANT_URL%/}/collections"
"${PYTHON_BIN}" - <<'PY' "${qdrant_file}"
import json, sys
payload = json.load(open(sys.argv[1]))
if payload.get("status") != "ok":
    raise SystemExit("qdrant collections not ok")
print("knowledge-server: qdrant ok")
PY

curl_json \
  "${search_file}" \
  -X POST "${BASE_URL}/search" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -F "query=knowledge deep healthcheck" \
  -F "access_level=global" \
  -F "limit=1" \
  -F "min_score=0"
"${PYTHON_BIN}" - <<'PY' "${search_file}"
import json, sys
payload = json.load(open(sys.argv[1]))
if payload.get("status") != "success":
    raise SystemExit("knowledge search not successful")
print("knowledge-server: search ok")
PY

echo "knowledge-server: deep healthcheck passed"
