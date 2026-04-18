#!/bin/zsh
# LEGACY: historical xiaodong-side policy script kept for reference only.
# Do not extend this script. New WeChat watcher work must land in xiaoguan/wechat-ops-runtime.
# wechat_watch_kentz.sh - xiaodong policy layer on top of shared wechat-ops runtime
# 版本: 3.0 (2026-03-24)

WORKDIR=/Users/xiaojiujiu2/.openclaw/workspace/xiaodong
LOG=$WORKDIR/wechat_watch_kentz.log
STATE=$WORKDIR/wechat_watch_kentz.state
PIDFILE=$WORKDIR/wechat_watch_kentz.pid
LOCKDIR=$WORKDIR/wechat_watch_kentz.lock
ENV_FILE=$HOME/.openclaw/.env
WECHAT_OPS=/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/bin/wechat-ops

POLL_SEC=8
COOLDOWN_SEC=35
MAX_CAPTURE_FAIL=5
ALLOWED_CONTACTS=(KentZ 张三李四)

mkdir -p "$WORKDIR"

log() {
  local level=$1
  shift
  echo "[$(date '+%F %T')] [$level] $*" >> "$LOG"
}

info()  { log INFO "$*"; }
warn()  { log WARN "$*"; }
error() { log ERROR "$*"; }

feishu_alert() {
  /opt/homebrew/bin/openclaw message send \
    --channel feishu --account xiaodong \
    --target ou_87bb675cf1a555992cf71df25f860c63 \
    --message "[微信监听告警] $1" >/dev/null 2>&1 || true
}

cleanup() {
  info "watcher stopping (PID=$$)"
  rm -f "$PIDFILE"
  rm -rf "$LOCKDIR"
  exit 0
}

trap cleanup TERM INT QUIT

acquire_lock() {
  if mkdir "$LOCKDIR" 2>/dev/null; then
    printf '%s\n' "$$" > "$PIDFILE"
    return 0
  fi

  if [[ -f "$PIDFILE" ]]; then
    local existing_pid
    existing_pid=$(cat "$PIDFILE" 2>/dev/null)
    if [[ -n "$existing_pid" ]] && kill -0 "$existing_pid" 2>/dev/null; then
      warn "another watcher is already running (pid=$existing_pid)"
      exit 0
    fi
  fi

  warn "stale lock detected, recovering"
  rm -rf "$LOCKDIR"
  mkdir "$LOCKDIR" 2>/dev/null || {
    error "failed to acquire lock"
    exit 1
  }
  printf '%s\n' "$$" > "$PIDFILE"
}

ops_json() {
  "$WECHAT_OPS" "$@" 2>/dev/null
}

json_field() {
  local payload=$1
  local expr=$2
  printf '%s' "$payload" | /usr/bin/python3 -c '
import json, sys
payload = json.load(sys.stdin)
expr = sys.argv[1]
value = payload
for part in expr.split("."):
    if isinstance(value, dict):
        value = value.get(part)
    else:
        value = None
        break
if value is None:
    sys.exit(1)
if isinstance(value, bool):
    print("true" if value else "false")
elif isinstance(value, (dict, list)):
    import json as _json
    print(_json.dumps(value, ensure_ascii=False))
else:
    print(value)
' "$expr"
}

analyze_answer() {
  local prompt=$1
  local payload answer
  payload=$(ops_json analyze --prompt "$prompt") || return 1
  answer=$(json_field "$payload" answer 2>/dev/null) || return 1
  printf '%s\n' "$answer"
}

is_allowed_contact() {
  local name=$1
  [[ -z "$name" || "$name" == "__UNKNOWN__" || "$name" == "__NONE__" ]] && return 1
  for c in "${ALLOWED_CONTACTS[@]}"; do
    [[ "$name" == *"$c"* ]] && return 0
  done
  return 1
}

if [[ -f "$ENV_FILE" ]]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

OPENAI_API_KEY=${OPENAI_API_KEY:-${MEM0_OPENAI_API_KEY:-}}
if [[ -z "$OPENAI_API_KEY" ]]; then
  error "fatal: OPENAI_API_KEY missing"
  feishu_alert "启动失败：OPENAI_API_KEY 未配置"
  exit 1
fi

LAST_MSG=""
LAST_SENT_TS=0
CAPTURE_FAIL_COUNT=0

if [[ -f "$STATE" ]]; then
  source "$STATE" 2>/dev/null || true
fi

acquire_lock

info "watcher started (v3.0, runtime=wechat-ops, poll=${POLL_SEC}s, contacts=${ALLOWED_CONTACTS[*]})"

while true; do
  NOW=$(date +%s)

  health=$(ops_json health)
  health_ok=$(json_field "$health" ok 2>/dev/null || echo false)
  if [[ "$health_ok" != "true" ]]; then
    CAPTURE_FAIL_COUNT=$((CAPTURE_FAIL_COUNT + 1))
    runtime_error=$(json_field "$health" error_code 2>/dev/null || echo "unknown")
    window_app=$(json_field "$health" window.app 2>/dev/null || echo "")
    window_id=$(json_field "$health" window.window_id 2>/dev/null || echo "")
    warn "window probe failed (app=${window_app:-unknown} window=${window_id:-unknown} fail=$CAPTURE_FAIL_COUNT error=$runtime_error)"
    if (( CAPTURE_FAIL_COUNT >= MAX_CAPTURE_FAIL )); then
      feishu_alert "微信窗口探活连续 $CAPTURE_FAIL_COUNT 次失败（app=${window_app:-unknown}, window=${window_id:-unknown}, error=$runtime_error），请检查权限或窗口状态。"
      CAPTURE_FAIL_COUNT=0
    fi
    sleep "$POLL_SEC"
    continue
  fi
  CAPTURE_FAIL_COUNT=0

  session=$(ops_json session current)
  session_ok=$(json_field "$session" ok 2>/dev/null || echo false)
  if [[ "$session_ok" != "true" ]]; then
    warn "session read failed"
    sleep "$POLL_SEC"
    continue
  fi

  contact=$(json_field "$session" current_contact 2>/dev/null || echo "__UNKNOWN__")
  view=$(json_field "$session" view 2>/dev/null || echo "unknown_view")
  incoming=$(json_field "$session" last_incoming_message 2>/dev/null || echo "__NONE__")
  contact=${contact//$'\n'/ }
  incoming=${incoming//$'\n'/ }

  if [[ "$view" != "chat_detail" ]]; then
    info "skip: not in chat_detail | view=$view"
    printf 'LAST_MSG=%q\nLAST_SENT_TS=%d\nCAPTURE_FAIL_COUNT=%d\n' \
      "$LAST_MSG" "$LAST_SENT_TS" "$CAPTURE_FAIL_COUNT" > "$STATE"
    sleep "$POLL_SEC"
    continue
  fi

  if ! is_allowed_contact "$contact"; then
    info "skip: not in whitelist | contact=$contact"
    printf 'LAST_MSG=%q\nLAST_SENT_TS=%d\nCAPTURE_FAIL_COUNT=%d\n' \
      "$LAST_MSG" "$LAST_SENT_TS" "$CAPTURE_FAIL_COUNT" > "$STATE"
    sleep "$POLL_SEC"
    continue
  fi

  if [[ -n "$incoming" && "$incoming" != "__NONE__" && "$incoming" != "__UNKNOWN__" ]]; then
    if [[ "$incoming" != "$LAST_MSG" ]]; then
      if (( NOW - LAST_SENT_TS >= COOLDOWN_SEC )); then
        if [[ "$incoming" == *收到，我在看* || "$incoming" == *小九九公司* ]]; then
          info "skip self-echo | in: $incoming"
        else
          reply=$(analyze_answer "你是小九九公司的销售同事，正在微信与客户【$contact】沟通。对方刚发：$incoming。请用自然口语中文回复，目标是推进沟通，不卑不亢、简洁专业，不超过60字，只输出回复正文。") || reply="__ERROR__"
          reply=${reply//$'\n'/ }
          if [[ -n "$reply" && "$reply" != "__NONE__" && "$reply" != "__UNKNOWN__" && "$reply" != "__ERROR__" ]]; then
            send_payload=$(ops_json chat send --name "$contact" --text "$reply")
            send_ok=$(json_field "$send_payload" ok 2>/dev/null || echo false)
            if [[ "$send_ok" == "true" ]]; then
              LAST_SENT_TS=$NOW
              LAST_MSG=$incoming
              info "replied | contact=$contact | in: $incoming | out: $reply"
            else
              send_error=$(json_field "$send_payload" error_code 2>/dev/null || echo "unknown")
              opened_contact=$(json_field "$send_payload" opened_contact 2>/dev/null || echo "")
              warn "reply failed | contact=$contact | in: $incoming | error=$send_error | opened_contact=$opened_contact"
            fi
          else
            warn "no reply generated | contact=$contact | in: $incoming"
          fi
        fi
      else
        info "cooldown | contact=$contact | in: $incoming"
      fi
    fi
  fi

  printf 'LAST_MSG=%q\nLAST_SENT_TS=%d\nCAPTURE_FAIL_COUNT=%d\n' \
    "$LAST_MSG" "$LAST_SENT_TS" "$CAPTURE_FAIL_COUNT" > "$STATE"

  sleep "$POLL_SEC"
done
