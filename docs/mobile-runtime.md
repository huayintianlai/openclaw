# Mobile Runtime

This repo now exposes a shared mobile execution layer through `mobile-runtime-plugin`.

For the full Chinese architecture explanation, deployment modes, diagrams, and design rationale, see:

- [Mobile Account Ops Architecture](./mobile-account-ops-architecture.md)

## What This Doc Is For

This page is the quick reference for the current implementation.

## Architecture

- `mobile runtime`: control plane, backend adapters, locking, task records, artifacts, approvals
- `mobile-core skill`: orchestration rules and standard flows
- business skills: `mobile-xhs`, `mobile-wechat`, `mobile-publish`

## Backends

- `mac-proxy`: ADB + AutoGLM on the Mac host
- `android-node`: preferred logical backend when a phone is paired as an OpenClaw device; currently bridges to ADB when direct node execution is unavailable

## Device Registry

The registry lives at [`devices/mobile.registry.json`](../devices/mobile.registry.json).

Agents must target business aliases such as:

- `xiaodong-main`
- `xiaodong-backup`
- `echo-xhs-1`
- `echo-xhs-2`

## Tool Surface

- `mobile_list_devices`
- `mobile_observe`
- `mobile_run_task`
- `mobile_act`
- `mobile_status`
- `mobile_cancel`
- `mobile_artifacts`

## Flow Templates

Stored under [`flows/mobile/`](../flows/mobile/):

- `search_in_app`
- `wechat_read_only`
- `draft_message`

## Runtime Notes

- Stable actions prefer UI tree selectors.
- When selector execution fails and a high-level intent exists, the runtime can fall back to AutoGLM.
- Dangerous flows return `needs_approval` unless the caller passes `approval_policy: "approved"`.
- Launching `xhs` / `xiaohongshu` is blocked while WiFi is enabled. Callers must explicitly declare a wifi-off precondition before the runtime will allow that app to open.
- Runtime state is stored under `state/mobile-runtime/`.
