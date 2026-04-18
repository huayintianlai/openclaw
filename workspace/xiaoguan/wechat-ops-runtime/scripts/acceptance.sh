#!/bin/zsh
set -euo pipefail

ROOT="/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime"
CLI="$ROOT/bin/wechat-ops"
WORKER="$ROOT/bin/xiaoguan-wechat-worker"
PYTHONPATH="$ROOT"
LOCK_DIR="$ROOT/state/operation.lock"

run_cmd() {
  local label="$1"
  shift
  echo
  echo "== $label =="
  rm -rf "$LOCK_DIR"
  "$@"
}

run_cmd "health" "$CLI" health
run_cmd "daemon status" "$CLI" daemon status
run_cmd "worker status" "$CLI" worker status
run_cmd "session current" "$CLI" session current
run_cmd "unread list" "$CLI" unread list
run_cmd "chat read-visible-messages" "$CLI" chat read-visible-messages
run_cmd "moments scan" "$CLI" moments scan
run_cmd "watch unread (1 iteration)" "$CLI" watch unread --iterations 1

echo
echo "== daemon watchers once =="
rm -rf "$LOCK_DIR"
DAEMON_STATUS_OUT="$(mktemp)"
if "$CLI" daemon status >"$DAEMON_STATUS_OUT" 2>/dev/null; then
  cat "$DAEMON_STATUS_OUT"
else
  "$CLI" daemon run --watches unread,chat_visible,moments --once
fi
rm -f "$DAEMON_STATUS_OUT"

echo
echo "== runtime-state watchers =="
/usr/bin/python3 - <<'PY'
import json
path="/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/state/runtime-state.json"
try:
    data=json.load(open(path))
    print(json.dumps(data.get("watchers"), ensure_ascii=False, indent=2))
    print(json.dumps(data.get("queues"), ensure_ascii=False, indent=2))
except FileNotFoundError:
    print({"missing": path})
PY

echo
echo "== target mismatch safety simulation =="
PYTHONPATH="$PYTHONPATH" /usr/bin/python3 - <<'PY'
from wechat_ops.runtime import WeChatOpsRuntime

rt = WeChatOpsRuntime()
rt.open_chat = lambda name: {"ok": True, "opened": name, "opened_contact": "错误联系人", "window": {"app": "微信", "window_id": 180, "title": "微信"}}
rt._platform_health_check = lambda: {"ok": True, "window": {"app": "微信", "window_id": 180, "title": "微信"}}
rt.user_activity_state = lambda: {"ok": True, "idle_seconds": 10.0, "min_idle_seconds": 3.0, "human_active": False}
rt._session_current_from_target = lambda target: {
    "ok": True,
    "current_contact": "错误联系人",
    "view": "chat_detail",
    "last_incoming_message": "你好",
    "window": target,
}
result = rt.send_text("测试消息", name="KentZ")
print(result)
if result.get("error_code") != "target_mismatch":
    raise SystemExit("expected target_mismatch")
PY

echo
echo "== new incoming safety simulation =="
PYTHONPATH="$PYTHONPATH" /usr/bin/python3 - <<'PY'
from wechat_ops.runtime import WeChatOpsRuntime

rt = WeChatOpsRuntime()
rt._platform_health_check = lambda: {"ok": True, "window": {"app": "微信", "window_id": 180, "title": "微信"}}
rt.open_chat = lambda name: {"ok": True, "opened": name, "opened_contact": name, "window": {"app": "微信", "window_id": 180, "title": "微信"}}
rt.user_activity_state = lambda: {"ok": True, "idle_seconds": 10.0, "min_idle_seconds": 3.0, "human_active": False}
state = {"count": 0}
def fake_session(target):
    state["count"] += 1
    return {
        "ok": True,
        "current_contact": "KentZ",
        "view": "chat_detail",
        "last_incoming_message": "旧消息" if state["count"] < 3 else "新消息",
        "window": target,
    }
rt._session_current_from_target = fake_session
rt.focus_window = lambda target: type("R", (), {"ok": True})()
class Result:
    def __init__(self, ok=True, stdout="", stderr=""):
        self.ok = ok
        self.stdout = stdout
        self.stderr = stderr
rt._peek = lambda *args, **kwargs: Result(True, "", "")
rt.inspect_compose_state = lambda target: {
    "ok": True,
    "view": "chat_detail",
    "current_contact": "KentZ",
    "input_focused": True,
    "search_focused": False,
    "draft_text": "",
    "last_incoming_message": "新消息",
}
prepared = rt.prepare_send("KentZ", "你好，测试消息")
result = rt.commit_send(prepared["tx_id"])
print(result)
if result.get("error_code") != "new_incoming_message":
    raise SystemExit("expected new_incoming_message")
PY

echo
echo "== draft mismatch safety simulation =="
PYTHONPATH="$PYTHONPATH" /usr/bin/python3 - <<'PY'
from wechat_ops.runtime import WeChatOpsRuntime

rt = WeChatOpsRuntime()
rt._platform_health_check = lambda: {"ok": True, "window": {"app": "微信", "window_id": 180, "title": "微信"}}
rt.open_chat = lambda name: {"ok": True, "opened": name, "opened_contact": name, "window": {"app": "微信", "window_id": 180, "title": "微信"}}
rt.user_activity_state = lambda: {"ok": True, "idle_seconds": 10.0, "min_idle_seconds": 3.0, "human_active": False}
rt._session_current_from_target = lambda target: {"ok": True, "current_contact": "KentZ", "view": "chat_detail", "last_incoming_message": "旧消息", "window": target}
rt.focus_window = lambda target: type("R", (), {"ok": True})()
class Result:
    def __init__(self, ok=True, stdout="", stderr=""):
        self.ok = ok
        self.stdout = stdout
        self.stderr = stderr
rt._peek = lambda *args, **kwargs: Result(True, "", "")
state = {"count": 0}
def fake_compose(target):
    state["count"] += 1
    if state["count"] <= 3:
        return {
            "ok": True,
            "view": "chat_detail",
            "current_contact": "KentZ",
            "input_focused": True,
            "search_focused": False,
            "draft_text": "" if state["count"] == 1 else "你好测试",
            "last_incoming_message": "旧消息",
        }
    return {
        "ok": True,
        "view": "chat_detail",
        "current_contact": "KentZ",
        "input_focused": True,
        "search_focused": False,
        "draft_text": "错误文本",
        "last_incoming_message": "旧消息",
    }
rt.inspect_compose_state = fake_compose
prepared = rt.prepare_send("KentZ", "你好测试")
result = rt.commit_send(prepared["tx_id"])
print(result)
if result.get("error_code") != "draft_not_cleared":
    raise SystemExit("expected draft_not_cleared")
PY

echo
echo "== human active safety simulation =="
PYTHONPATH="$PYTHONPATH" /usr/bin/python3 - <<'PY'
from wechat_ops.runtime import WeChatOpsRuntime

rt = WeChatOpsRuntime()
rt.open_chat = lambda name: {"ok": True, "opened": name, "opened_contact": name, "window": {"app": "微信", "window_id": 180, "title": "微信"}}
rt._platform_health_check = lambda: {"ok": True, "window": {"app": "微信", "window_id": 180, "title": "微信"}}
rt.user_activity_state = lambda: {"ok": True, "idle_seconds": 0.2, "min_idle_seconds": 3.0, "human_active": True}
rt._session_current_from_target = lambda target: {"ok": True, "current_contact": "KentZ", "view": "chat_detail", "last_incoming_message": "你好", "window": target}
result = rt.send_text("测试消息", name="KentZ")
print(result)
if result.get("error_code") != "human_active":
    raise SystemExit("expected human_active")
PY

echo
echo "== worker queue smoke =="
PYTHONPATH="$PYTHONPATH" /usr/bin/python3 - <<'PY'
import json
import tempfile
from pathlib import Path

from wechat_ops.config import WeChatOpsConfig
from wechat_ops.runtime import WeChatOpsRuntime
from wechat_ops.worker import WeChatOpsWorker

with tempfile.TemporaryDirectory() as tmpdir:
    config = WeChatOpsConfig.load(Path(tmpdir))
    runtime = WeChatOpsRuntime(config)
    runtime.enqueue_job(
        job_type="unread.snapshot.changed",
        source="watcher:unread",
        cursor=1,
        signature="demo-signature",
        payload={"items": [{"name": "客户A", "unread_count": 1, "preview": "你好"}]},
    )
    worker = WeChatOpsWorker(config)
    rc = worker.run(once=True)
    if rc != 0:
        raise SystemExit(f"worker run failed: {rc}")
    result_files = sorted(config.results_pending_dir.glob("*.json"))
    if not result_files:
        raise SystemExit("expected results_pending output")
    print(json.dumps(json.load(open(result_files[0])), ensure_ascii=False, indent=2))
PY

echo
echo "acceptance complete"
