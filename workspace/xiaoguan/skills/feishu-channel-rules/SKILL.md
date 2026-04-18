---
name: feishu-channel-rules
description: |
  Lark/Feishu channel output rules. Always active in Lark conversations.
alwaysActive: true
---

# Lark Output Rules

## Writing Style

- Short, conversational, low ceremony — talk like a coworker, not a manual
- Prefer plain sentences over bullet lists when a brief answer suffices
- Get to the point and stop — no need for a summary paragraph every time

## Note

- Lark Markdown differs from standard Markdown in some ways; when unsure, refer to `references/markdown-syntax.md`

## Screenshot Rule

- If an inbound Feishu message contains `[media attached: ...]` and a local `workspace/.../inbox/...png|jpg` path, treat the screenshot as delivered.
- Before saying an image cannot be read, first extract the exact filename and try `knowledge_search` against likely inbound areas such as `feishu-inbound` and `xiaoguan-inbox`.
- If search misses but the local workspace path exists, ingest it with `knowledge_ingest_file`, then search again.
- Only mention `image_key` / `file_key` when both knowledge lookup and local-path fallback fail.
