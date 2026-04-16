---
name: mobile-xhs
description: |
  Xiaohongshu mobile execution patterns for discovery, search, and lead observation. Builds on mobile-core.
---

# Mobile XHS Skill

- Use `mobile-core` first.
- Default devices: `echo-xhs-1`, then `echo-xhs-2`.
- Preferred flow: `search_in_app` with `app: "xhs"`.
- XHS is WiFi-guarded. Do not launch it while WiFi is on. Only pass `precondition: { "wifi": "off", "auto_disable": true }` when the user explicitly approves cutting WiFi first.
- For pure observation, run `mobile_observe` immediately after search and summarize from the returned `elements_summary`.
- Do not publish or send messages from XHS without explicit approval.
