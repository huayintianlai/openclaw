---
name: mobile-wechat
description: |
  WeChat mobile execution patterns for read-only checks and draft preparation. Builds on mobile-core.
---

# Mobile WeChat Skill

- Use `mobile-core` first.
- Default device: `xiaodong-main`; fallback to `xiaodong-backup`.
- Read-only check: use `flow_id: "wechat_read_only"`.
- Draft preparation: use `flow_id: "draft_message"` and require approval.
- Never send a message through raw taps; stop at draft + snapshot unless the user explicitly approves the dangerous step.
