---
name: mobile-publish
description: |
  Guardrailed mobile publishing workflows. Builds on mobile-core and requires explicit approval for dangerous actions.
---

# Mobile Publish Skill

- Treat every publish/send/submit action as `danger`.
- Always gather a pre-action snapshot and a post-draft snapshot.
- If approval is missing, return the pending approval event instead of guessing.
- Prefer drafting on `xiaodong-main` or `echo-xhs-1`, then hand off for human review.
