# Knowledge System Follow-up (2026-03-14)

## Already done tonight

- Local OpenClaw knowledge plugin now has:
  - `knowledge_search`
  - `knowledge_ingest_file`
  - `knowledge_get_file`
  - `knowledge_return_file`
- Mem0 tuning updated:
  - stricter long-term memory prompt
  - `searchThreshold=0.35`
  - `topK=8`
- Remote `haystack-api` hotfix is live on `47.108.68.217`
- Verified live:
  - image ingest
  - PDF ingest
  - PPTX ingest
  - semantic search
  - file metadata
  - original file download / hash consistency

## Manual / daylight follow-up

### 1. Live channel resend not exercised against real users

Reason:
- `knowledge_return_file` is wired for Feishu + Telegram, but I did not intentionally send test files into real chats while you were asleep.

What to test tomorrow:
- In a safe chat, ask an agent to:
  1. `knowledge_ingest_file` on a sample file
  2. `knowledge_search` for that file
  3. `knowledge_return_file` with the returned `file_id`
- Confirm the original attachment is re-sent in:
  - Feishu
  - Telegram

### 2. Remote container is running via hotfixed app copy, not a freshly rebuilt image

Current state:
- Host files under `/www/haystack-api/` are updated
- Running container was updated with `docker cp /app/app.py`
- `docker-compose` rebuild was blocked by Docker build DNS resolution to the PyPI mirror

Recommended follow-up on server:

```bash
cd /www/haystack-api
docker-compose build --no-cache
docker-compose up -d
```

If DNS still fails during build, check Docker daemon DNS / resolver first.

### 3. Scanned PDF image-page fallback is code-ready but not active in the running v1 image

Current state:
- App code supports optional `PyMuPDF` fallback
- Running container does not have `fitz`, so scanned-only PDF pages will not OCR tonight
- Text PDFs work and were verified

To fully enable scanned PDF fallback:
- rebuild with the new `Dockerfile`, or
- install `pymupdf` inside the image/container and redeploy properly

### 4. Legacy `.ppt` is still not supported

Current state:
- `.pptx` works
- old binary `.ppt` returns an explicit error

Recommended policy:
- convert `.ppt` to `.pptx` before ingest, or
- later add a LibreOffice headless conversion path on the server
