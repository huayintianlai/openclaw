---
name: wechat-ops-core
description: Operate and observe macOS WeChat through a local wechat-ops runtime backed by Peekaboo, including health checks, session inspection, unread scans, watcher mode, and safe chat actions.
homepage: https://peekaboo.boo
metadata: {"clawdbot":{"emoji":"💬","os":["darwin"],"requires":{"bins":["peekaboo","python3"]},"install":[{"id":"brew","kind":"brew","formula":"steipete/tap/peekaboo","bins":["peekaboo"],"label":"Install Peekaboo (brew)"}]}}
---

# wechat-ops-core

Use this skill when you need **generic WeChat automation** on macOS: runtime health checks, current-session inspection, unread scans, moments scans, or watcher/daemon management.

This skill is the **public bottom layer**. It does not contain sales prompts, customer whitelists, or private business rules.

## Runtime Layout

- Local runtime root:
  `/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime`
- CLI entrypoint:
  `/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/bin/wechat-ops`
- Worker entrypoint:
  `/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/bin/xiaoguan-wechat-worker`
- Xiaoguan workspace wrapper:
  `/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/bin/wechat-ops`
- Config file:
  `/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/config/wechat-ops.json`

For ClawHub publication, package the same runtime as a standalone `wechat-ops` binary/CLI. Keep this skill thin.

## Core Commands

- Health:
  `.../bin/wechat-ops health`
- Current session:
  `.../bin/wechat-ops session current`
- Read visible group messages with speaker/time/text:
  `.../bin/wechat-ops chat read-visible-messages`
- List unread chats:
  `.../bin/wechat-ops unread list`
- Watch unread state:
  `.../bin/wechat-ops watch unread`
- Scan visible moments feed:
  `.../bin/wechat-ops moments scan`
- Prepare / verify / commit a send transaction:
  `.../bin/wechat-ops chat prepare-send --name "联系人" --text "你好"`
  `.../bin/wechat-ops chat verify-send --tx <id>`
  `.../bin/wechat-ops chat commit-send --tx <id>`
- Run daemon:
  `.../bin/wechat-ops daemon run`
- Start / inspect / stop daemon:
  `.../bin/wechat-ops daemon start --watches unread,chat_visible,moments`
  `.../bin/wechat-ops daemon status`
  `.../bin/wechat-ops daemon stop`
- Start / inspect / stop worker:
  `.../bin/wechat-ops worker start`
  `.../bin/wechat-ops worker status`
  `.../bin/wechat-ops worker stop`

## Usage Rules

- In Xiaoguan's workspace, you are explicitly allowed to execute the local `wechat-ops` wrapper directly for internal WeChat runtime work.
- Keep the agent-facing command surface small. Default to `health`, `session current`, `chat read-visible-messages`, `unread list/watch`, `moments scan`, and the three send-transaction commands.
- Prefer `health` before any destructive or stateful operation.
- Prefer `session current` before any send transaction so you know which page/view the runtime sees.
- Never use `cmd+k` as a WeChat chat-search shortcut. It can trigger Feishu global search and cover the WeChat window. The runtime must search by focusing the WeChat window and clicking/focusing the in-window search box only.
- Use watcher/daemon mode for continuous monitoring. Runtime writes watcher state files plus `jobs/` and `results/` queues under `state/`.
- Prefer `daemon start` and `worker start` for long-running background use. They launch background processes and write logs under `logs/`.
- The daemon and `watch ...` flows acquire the WeChat control lock per polling cycle, not for the entire process lifetime, so foreground inspection commands can still run while background services are alive.
- `unread list` and `watch unread` try to scan the visible left conversation rail even when you are inside a chat detail page.
- Treat unread semantics carefully:
  - `app_unread_badge_count` / `app_has_unread_badge` come from the left chat icon's top-right badge and represent the chat module's global unread hint.
  - `items[*].has_unread_badge` / `items[*].unread_badge_count` come only from the contact avatar's top-right badge.
  - `items[*].preview` is only preview text. Strings like `[999+条]` or `[@所有人]` inside preview text are not unread badge counts.
  - If the user asks “有几个未读会话”, count `summary.visible_unread_session_count` or `items` length, not preview patterns.
- `chat read-visible-messages` is the only supported way for agents to read visible group messages. Do not recreate this with ad hoc OCR prompts.
- Prefer the runtime's structured metadata:
  - `chat_kind` tells you whether the current chat should be treated as `group_chat`, `private_chat`, or `unknown_chat`
  - `stability` tells you whether the returned observation won a multi-sample consensus
- Do not embed sales language, whitelist policy, or CRM behavior into this public skill.
- If runtime commands fail with structured errors, trust those errors over ad hoc screenshot guessing. Do not switch to manual `peekaboo` experimentation unless the skill explicitly instructs that as a supported diagnostic path.

## Failure Semantics

The runtime returns structured JSON. On failures, the response must include:

- `phase`
- `current_view`
- `current_contact`
- `error_code`
- `recommended_next_step`

Common top-level failure modes include:

- `permission_denied`
- `window_not_found`
- `view_unknown`
- `ocr_failed`
- `send_failed`
- `target_mismatch`
- `human_active`
- `unstable_view`
- `timeout`

Before sending, the runtime verifies that the requested target contact matches the currently opened conversation title after only whitespace and bracket normalization. It does not allow loose substring matches, so group chats or similarly named chats are rejected with `target_mismatch`.
Before sending, the runtime also requires a short stable window and a minimum local input idle time. If a human is actively moving the mouse or typing, sending is rejected with `human_active`.
When the runtime does not know the current view or target for sure, the correct behavior is to stop, return the structured failure, and avoid speculative claims about whether a message was sent or which chat is open.
The agent must not ask the user to manually inspect whether a message was sent as the primary fallback. The primary fallback is always to report facts and the next deterministic runtime step.

## References

- Interface contract:
  [references/runtime-contract.md](references/runtime-contract.md)
- Reliability model:
  [references/reliability-model.md](references/reliability-model.md)
