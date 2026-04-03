#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${OPENCLAW_RUNTIME_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
APP_DIR="${OPENCLAW_KNOWLEDGE_APP_DIR:-${ROOT_DIR}/knowledge/server_patch}"
ENV_FILE="${ROOT_DIR}/.env"
PORT="${PORT:-8002}"
HOST="${HOST:-127.0.0.1}"
LOG_DIR="${ROOT_DIR}/logs"
STATE_DIR="${ROOT_DIR}/state/knowledge-server"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"

mkdir -p "${LOG_DIR}" "${STATE_DIR}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="$(command -v python3 || true)"
fi

if [[ -z "${PYTHON_BIN}" || ! -x "${PYTHON_BIN}" ]]; then
  echo "knowledge-server: no usable python3 interpreter found" >&2
  exit 1
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

export API_TOKEN="${API_TOKEN:-${KNOWLEDGE_API_TOKEN:-}}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-${MEM0_OPENAI_API_KEY:-}}"
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://api.openai.com/v1}"
export QDRANT_URL="${QDRANT_URL:-https://qdrant.99uwen.com}"
export QDRANT_COLLECTION="${QDRANT_COLLECTION:-${KNOWLEDGE_QDRANT_COLLECTION:-company-kb-local-v1}}"
export EMBEDDING_PROVIDER="${EMBEDDING_PROVIDER:-${KNOWLEDGE_EMBEDDING_PROVIDER:-openai}}"
export EMBEDDING_MODEL="${EMBEDDING_MODEL:-${KNOWLEDGE_EMBEDDING_MODEL:-text-embedding-3-small}}"
export EMBEDDING_DIM="${EMBEDDING_DIM:-${KNOWLEDGE_EMBEDDING_DIM:-1536}}"
export VISION_PROVIDER="${VISION_PROVIDER:-${KNOWLEDGE_VISION_PROVIDER:-gemini}}"
export VISION_MODEL="${VISION_MODEL:-${KNOWLEDGE_VISION_MODEL:-gemini-2.5-pro}}"
export GEMINI_BASE_URL="${GEMINI_BASE_URL:-${KNOWLEDGE_GEMINI_BASE_URL:-https://generativelanguage.googleapis.com/v1beta/openai}}"
export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1,qdrant.99uwen.com}"
export no_proxy="${no_proxy:-${NO_PROXY}}"
export PYTHONUNBUFFERED=1

missing=()
[[ -n "${API_TOKEN}" ]] || missing+=("KNOWLEDGE_API_TOKEN")
[[ -n "${OPENAI_API_KEY}" ]] || missing+=("MEM0_OPENAI_API_KEY/OPENAI_API_KEY")
[[ -n "${QDRANT_URL:-}" ]] || missing+=("QDRANT_URL")
[[ -n "${QDRANT_API_KEY:-}" ]] || missing+=("QDRANT_API_KEY")

if [[ ${#missing[@]} -gt 0 ]]; then
  printf 'knowledge-server: missing required settings: %s\n' "${missing[*]}" >&2
  exit 1
fi

"${PYTHON_BIN}" - <<'PY'
import importlib
import os
import sys

required = ["fastapi", "uvicorn", "pypdf", "pptx", "httpx", "requests"]
missing = []
for name in required:
    try:
        importlib.import_module(name)
    except Exception as exc:
        missing.append(f"{name}: {exc}")

try:
    import fitz  # noqa: F401
except Exception as exc:
    missing.append(f"fitz: {exc}")

if missing:
    print("knowledge-server: python runtime check failed", file=sys.stderr)
    for item in missing:
        print(f"  - {item}", file=sys.stderr)
    sys.exit(1)

print(
    "knowledge-server: preflight ok",
    f"host={os.environ.get('HOST', '127.0.0.1')}",
    f"port={os.environ.get('PORT', '8002')}",
    f"collection={os.environ.get('QDRANT_COLLECTION')}",
)
PY

UVICORN_ARGS=(
  "${PYTHON_BIN}"
  -m
  uvicorn
  app:app
  --app-dir
  "${APP_DIR}"
  --host
  "${HOST}"
  --port
  "${PORT}"
  --log-level
  info
)

exec "${UVICORN_ARGS[@]}"
