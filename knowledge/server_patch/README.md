# Knowledge Server Patch

This directory mirrors the remote `/www/haystack-api` service so the deployed
knowledge API changes stay inspectable in the local workspace.

Files:

- `app.py`: file ingest, metadata storage, Qdrant indexing, search, and file retrieval
- `Dockerfile`: Python runtime with PDF, PPTX, and scanned-PDF dependencies
- `docker-compose.yml`: host-network deployment used by the current server
- `run_local.sh`: local entrypoint for the `127.0.0.1:8002` knowledge + OpenAI-compatible proxy
- `deep_healthcheck.sh`: validates `/health`, embeddings, chat completions, Qdrant, and knowledge search
- `memory_e2e_check.js`: full Mem0 add/search/delete verification against the live runtime
- `watchdog.sh`: periodic self-healing probe that restarts the local service when required
- `install_launchd.sh`: installs the launchd service and watchdog on macOS

Current behavior after deployment:

- Supports ingest for `pdf`, `pptx`, and image files
- Stores original files under `data/files/...`
- Stores derived chunk metadata under `data/derived/...`
- Stores file metadata in `data/kb.sqlite`
- Returns file metadata from `/files/{file_id}/meta`
- Returns original files from `/files/{file_id}`

Known limitation:

- Legacy binary `.ppt` files still need conversion to `.pptx`

## Local production service

This runtime uses `127.0.0.1:8002` for two responsibilities:

- knowledge file APIs (`/ingest/file`, `/search`, `/files/...`)
- OpenAI-compatible proxy APIs used by Mem0 (`/openai/v1/embeddings`, `/openai/v1/chat/completions`)

Install the service and watchdog on this Mac:

```bash
./knowledge/server_patch/install_launchd.sh
```

Manual checks:

```bash
./knowledge/server_patch/deep_healthcheck.sh
node ./knowledge/server_patch/memory_e2e_check.js
```

Installed launchd labels:

- `ai.openclaw.knowledge-server`
- `ai.openclaw.knowledge-watchdog`

The watchdog performs cheap dependency probes every minute and a full Mem0
write/read/delete verification every 15 minutes by default.
