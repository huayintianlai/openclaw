---
name: wechat-sales-orchestrator
description: Layer private sales workflows on top of the local wechat-ops runtime, including customer follow-up, whitelist handling, and future unread or moments business actions for Xiaoguan.
metadata: {"clawdbot":{"emoji":"📈","os":["darwin"],"requires":{"bins":["peekaboo","python3"]}}}
---

# wechat-sales-orchestrator

Use this skill when Xiaoguan needs to turn the generic WeChat runtime into **sales operations**.

This is a **private extension layer**. Keep it out of ClawHub. It should always call the generic runtime or `$wechat-ops-core` instead of talking to `peekaboo` directly.

## Responsibilities

- apply customer whitelists / targeting rules
- decide whether to reply, stay silent, or create a follow-up task
- attach sales prompts and CRM context
- interpret unread lists as business work queues
- interpret moments scans as sales signals

## Rules

- Start with runtime health:
  `.../bin/wechat-ops health`
- Read current session before replying:
  `.../bin/wechat-ops session current`
- For group-chat monitoring, speaker extraction, or message-time extraction, do not rely on `session current` alone.
  First run:
  `/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/bin/wechat-ops chat read-visible-messages`
- Xiaoguan-main should consume `wechat-ops-runtime/state/results/pending/*.json` as its business intake. Do not build sales logic directly on top of `events.jsonl`.
- `unread.snapshot.changed` should only become reminders or prioritization hints.
- Interpret unread payloads with the runtime's strict semantics:
  - global unread hint: `app_unread_badge_count`
  - visible unread sessions: `summary.visible_unread_session_count` or `items`
  - session unread badge: `items[*].has_unread_badge` / `items[*].unread_badge_count`
  - preview text is not unread count, even if it contains `[999+条]` or similar patterns
- Before interpreting visible chat messages, inspect `chat_kind`:
  - `group_chat`: you may reason over `messages[*].speaker/time/text`
  - `private_chat`: do not invent speakers; treat `messages=[]` as expected
  - if `stability.stable=false`, treat the observation as low-confidence and re-check before creating downstream business actions
- `chat.visible.delta` should only inspect `added_messages`; keyword/CRM matching belongs here, not in the runtime or worker.
- `moments.cards.unseen` should default to creating reminders or tasks. Do not update CRM core fields unless the business context is confirmed.
- For WeChat inspection requests, execute the local wrapper first instead of hesitating:
  `/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/bin/wechat-ops`
- Do not hardcode WeChat window ids or screenshot paths in business logic.
- Do not embed public runtime implementation details here.
- Keep prompts, whitelists, and business policy here or in private references only.
- Do not answer with “I cannot exec” or “I do not have permission” for internal WeChat runtime operations unless the wrapper command itself actually fails and you include the real error.
- If the runtime returns `unknown_view`, `ocr_failed`, `timeout`, or any other structured failure, do not fall back to ad hoc OCR speculation, manual window-id guessing, clipboard tricks, or asking the user to visually verify whether a message was sent.
- In failure mode, report only what the runtime knows for sure:
  - current phase
  - current error code
  - current view if known
  - current contact if known
  - whether a transaction reached prepared / verified / sent / frozen
  - recommended next deterministic action
- Never claim “it probably sent” or “it seems to be KentZ” unless the runtime returned a verified target/contact state.
- Never use “你自己看一眼确认是不是发出去了” as the main fallback.

## Future Extensions

- unread prioritization by customer stage
- moments lead detection and tagging
- auto-create Feishu tasks for follow-up actions
- CRM enrichment before reply generation
