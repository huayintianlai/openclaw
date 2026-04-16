---
name: mobile-core
description: |
  Mobile runtime orchestration skill. Use when a task should run on Android devices through the shared mobile_* tools instead of raw exec/adb commands.
---

# Mobile Core Skill

## When To Use

- The user wants an Android phone to open an app, search, observe, or prepare a draft.
- A task should run on one of the registered aliases such as `xiaodong-main`, `xiaodong-backup`, `echo-xhs-1`, or `echo-xhs-2`.
- The workflow needs device locking, artifact collection, approval gating, or backend fallback.

## Hard Rules

- Always prefer `mobile_run_task` or `mobile_act`; do not call raw `adb` or `start_phone.sh` from business logic.
- Select devices by `device_selector.alias` or labels, never by raw serial number in normal operation.
- Treat `danger` flows and write operations as approval-gated unless `approval_policy="approved"` is explicitly supplied.
- Use `mobile_observe` before exploratory work and after uncertain actions.
- Use `mobile_status` and `mobile_artifacts` to inspect outcomes instead of assuming success.
- Opening `xhs` / `xiaohongshu` is WiFi-guarded. The runtime refuses to launch it while WiFi is enabled unless the caller explicitly sets a wifi-off precondition.

## Canonical Tools

- `mobile_list_devices`
- `mobile_observe`
- `mobile_run_task`
- `mobile_act`
- `mobile_status`
- `mobile_cancel`
- `mobile_artifacts`

## Standard Device Aliases

- `xiaodong-main`: general orchestration phone
- `xiaodong-backup`: backup orchestration phone
- `echo-xhs-1`: primary Echo/XHS phone
- `echo-xhs-2`: backup Echo/XHS phone

## Common Patterns

### Search inside an app

```json
{
  "device_selector": { "alias": "echo-xhs-1" },
  "flow_id": "search_in_app",
  "inputs": {
    "app": "xhs",
    "query": "跨境电商"
  },
  "precondition": {
    "wifi": "off",
    "auto_disable": true
  },
  "approval_policy": "auto"
}
```

### Read a WeChat conversation without sending

```json
{
  "device_selector": { "alias": "xiaodong-main" },
  "flow_id": "wechat_read_only",
  "inputs": {
    "chat_name": "客户A"
  },
  "approval_policy": "auto"
}
```

### Prepare a draft but do not send

```json
{
  "device_selector": { "alias": "xiaodong-main" },
  "flow_id": "draft_message",
  "inputs": {
    "chat_name": "客户A",
    "message": "您好，我先发一版草稿给您确认。"
  },
  "risk_level": "danger",
  "approval_policy": "approved"
}
```

## Fallback Strategy

- Semantic actions first.
- If selectors fail and the request has high-level intent, allow the runtime to fall back to AutoGLM.
- Record fallback use via `mobile_status` and `mobile_artifacts`.
