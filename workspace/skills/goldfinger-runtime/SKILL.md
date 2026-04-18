---
name: goldfinger-runtime
description: |
  GoldFinger Runtime execution skill. Use when an agent should launch, observe, or stop a GoldFinger browser/data capability through the local Agent Runtime CLI instead of calling control-plane APIs directly.
---

# GoldFinger Runtime Skill

- Prefer this skill whenever the task is "让 GoldFinger 去执行一项本地浏览器/获客能力".
- Always call the local CLI through `exec`; do not call GoldFinger control APIs as the primary execution path.
- Treat `run_id` as the only runtime tracking identifier. Do not invent or depend on `worker_id`.
- `stdout` from the CLI is machine-readable JSON. Parse it before making decisions.
- `stderr` is runtime log output. Use it for debugging, not as the authoritative result.
- If the CLI returns a non-zero exit code, trust the JSON error payload first.

## Canonical Commands

### Start a run

```bash
python -m src.cli.agent_runtime run --capability xhs_echo_customer_acquisition --input-json @payload.json
```

### Check status

```bash
python -m src.cli.agent_runtime status --run-id <run_id>
```

### Stop a run

```bash
python -m src.cli.agent_runtime stop --run-id <run_id>
```

## Hard Rules

- Do not use GoldFinger control-plane APIs as the main path for starting runtime jobs.
- Do not pass or reason about `worker_id` unless debugging a runtime internals issue.
- For `xhs_echo_customer_acquisition`, let Runtime apply defaults such as `filter_channel=image` unless the task explicitly requires a different value.
- If `status` returns `stop_requested`, wait for a later `status` call before assuming the run is fully cancelled.
- If environment errors such as missing `DATABASE_URL` or `REDIS_URL` occur, surface them clearly instead of retrying blindly.

## Output Expectations

- `run` returns `run_id`, `capability`, `task_package_id`, `status`, and normalized `config`.
- `status` returns `run_id`, `status`, `summary`, `stats`, `error_message`, and `metadata`.
- `stop` returns one of `cancelled`, `stop_requested`, or `not_found`.

## Typical Flow

1. Build a small JSON payload for the capability.
2. Run the CLI and capture the returned `run_id`.
3. Poll `status` until the run reaches a terminal state.
4. If needed, send `stop` using the same `run_id`.

## Scope

- This skill teaches agents how to call GoldFinger Runtime.
- It does not replace `goldfinger-control`, which still owns approval routing and human coordination.
- It does not own GoldFinger execution logic; Runtime keeps that responsibility.

