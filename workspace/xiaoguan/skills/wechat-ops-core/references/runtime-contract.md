# Runtime Contract

The public skill talks to a local runtime CLI, not directly to `peekaboo`.

## CLI Surface

- `wechat-ops health`
  Returns runtime permission/window state plus `daemon`, `worker`, `watchers`, and `queues` health summaries.

- `wechat-ops session current`
  Returns the current view, current contact, last incoming message, `chat_kind`, artifact paths, and `stability`.

- `wechat-ops chat open --name <contact>`
  Developer/diagnostic helper. Not part of Xiaoguan's normal command surface.
  Focuses WeChat, uses the search flow, and attempts to open the target conversation.

- `wechat-ops chat read-last`
  Developer/diagnostic helper. Not part of Xiaoguan's normal command surface.
  Reads the last incoming message from the current conversation.

- `wechat-ops chat send --name <contact> --text <text>`
  Developer/diagnostic helper. Normal agent sends should use the three-step transaction commands below.
  Opens the contact if needed, verifies the opened chat title matches the requested target using strict normalized equality (no substring/group fallback), waits for a stable chat-detail confirmation, checks that local user input has been idle long enough, and only then sends text.

- `wechat-ops chat prepare-send --name <contact> --text <text>`
  Opens the target chat, captures the conversation baseline, creates a transaction, and returns `tx_id`.

- `wechat-ops chat verify-send --tx <id>`
  Re-checks the target chat, human-idle state, search/input focus state, and whether new incoming messages changed the context.

- `wechat-ops chat commit-send --tx <id>`
  Stages message chunks with read-back verification, checks for new incoming messages again, and only then commits the send.

- `wechat-ops chat abort-send --tx <id>`
  Marks the transaction aborted/frozen without continuing.

- `wechat-ops chat inspect-input`
  Returns input focus, search focus, current draft text, current contact, and view.

- `wechat-ops chat inspect-target`
  Returns the current session/target state.

- `wechat-ops chat inspect-search`
  Returns whether search mode is currently active.

- `wechat-ops chat inspect-last-incoming`
  Returns the current last incoming message from the visible chat.

- `wechat-ops unread list`
  Returns unread chats visible on the current chat-list screen plus `cursor`, `signature`, and `available`.
  Semantics are strict:
  - `app_unread_badge_count` / `app_has_unread_badge`
    come from the left chat icon's top-right badge
  - `items[*].has_unread_badge` / `items[*].unread_badge_count`
    come only from the avatar top-right badge for each visible session
  - `items[*].preview`
    is preview text only, never an unread count
  - `summary.visible_unread_session_count`
    is the correct answer for “当前左侧可见有几个未读会话”
  - `stability`
    reports how many observations were sampled and how many matched the winning result

- `wechat-ops chat read-visible-messages`
  Returns visible group-style messages plus `chat_kind` and `stability`.
  If `chat_kind=private_chat`, it should normally return `available=false` and `messages=[]` instead of inventing speakers.

- `wechat-ops moments scan`
  Returns visible cards on the current moments feed plus `feed_signature`, `cursor`, `card_signature`, and `seen`.

- `wechat-ops daemon run`
  Polls watcher state, writes `runtime-state.json`, writes watcher state files, appends event records to `events.jsonl`, and enqueues `jobs/`.

- `wechat-ops daemon start|status|stop`
  Manage the long-running daemon process. `start` launches it in the background and logs to `logs/daemon.log`.

- `wechat-ops worker start|status|stop`
  Manage the long-running worker process. `start` launches it in the background and logs to `logs/worker.log`.

- `xiaoguan-wechat-worker run`
  Claims `jobs/pending`, writes `results/pending`, and moves finished jobs into `jobs/done`.

Background daemon/watch flows do not hold the WeChat control lock forever. They acquire it per poll cycle so foreground commands such as `session current` and `unread list` can still run while services are active.

## Additional Semantics

- `chat_kind`
  - `group_chat`: runtime saw stable speaker/message structure or the contact name strongly looks like a group
  - `private_chat`: runtime saw a chat detail view but not stable group speaker structure
  - `unknown_chat`: runtime cannot classify confidently

- `stability`
  - `sample_attempts`: how many observations were collected
  - `winning_observations`: how many matched the returned result
  - `stable`: whether the winner met the minimum consensus threshold

## State Files

- Runtime state:
  `/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/state/runtime-state.json`
- Daemon state:
  `/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/state/daemon-state.json`
- Worker state:
  `/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/state/worker-state.json`
- Watcher states:
  `/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/state/watchers/*.json`
- Runtime events:
  `/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/state/events.jsonl`
- Jobs queue:
  `/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/state/jobs/{pending,processing,done}`
- Results queue:
  `/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/state/results/{pending,consumed,failed}`

## Public vs Private Boundary

Public skill:
- generic WeChat observation and action commands
- runtime health, watcher, unread, moments, chat I/O

Private extensions:
- customer whitelists
- reply prompts
- sales progression logic
- CRM / Feishu task linkage

## Failure Handling Contract

When runtime returns a structured failure such as `unknown_view`, `ocr_failed`, `timeout`, `target_mismatch`, `human_active`, or `new_incoming_message`:

- include `phase`, `current_view`, `current_contact`, `error_code`, and `recommended_next_step`
- do not speculate about the open chat or send outcome
- do not ask the user to manually inspect and confirm as the primary fallback
- do not bypass runtime with manual window-id guessing or one-off clipboard/window-title heuristics
- report the exact runtime state and propose the next deterministic diagnostic action
