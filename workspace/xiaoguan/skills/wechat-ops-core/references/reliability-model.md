# Reliability Model

The runtime is responsible for production reliability. Agents should not recreate these controls.

## Required Controls

- Single daemon lock directory
- Single worker lock directory
- Permission health checks before meaningful work
- Dynamic window discovery instead of hardcoded window ids
- Fixed temp artifact paths
- Failure artifact retention with TTL cleanup
- Structured JSON responses for all commands
- Event emission only when state changes
- Per-watcher state files with `cursor`, `signature`, health flags, and last error info
- File queues for `jobs/` and `results/`
- Automatic recovery for stale processing leases and repeated watcher failures

## View Model

The runtime normalizes the current screen into:

- `chat_list`
- `chat_detail`
- `moments_feed`
- `moments_detail`
- `unknown_view`

All higher-level skills should branch on this normalized state instead of ad hoc screenshot heuristics.

## Watcher Model

- `unread`: visible unread sidebar snapshot with dedupe by normalized signature
- `chat_visible`: visible group-message snapshot with diff on `(speaker, time, text)`
- `moments`: visible moments cards with `card_signature` and `seen` marking

The runtime owns cursor advancement, signature comparison, state persistence, and queue emission. Agents must not recreate these controls in prompts.
