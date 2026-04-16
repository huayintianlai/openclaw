# Mobile Runtime State

This directory stores the file-backed mobile control plane:

- `tasks.json`
- `locks.json`
- `approvals.json`
- `audit.jsonl`
- `artifacts/`

The plugin creates the mutable files on demand. Keep this directory present so the runtime has a stable home inside the OpenClaw instance.
