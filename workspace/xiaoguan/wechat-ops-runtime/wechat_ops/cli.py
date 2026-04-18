from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from contextlib import contextmanager
from typing import Iterable, List

from .config import WeChatOpsConfig
from .runtime import WeChatOpsRuntime, canonicalize_json, json_safe, now_iso


def print_json(payload):
    print(json.dumps(json_safe(payload), ensure_ascii=False, indent=2))


def operation_busy_payload():
    return {
        "ok": False,
        "error_code": "operation_busy",
        "phase": "health_check",
        "current_view": "unknown_view",
        "current_contact": "__UNKNOWN__",
        "recommended_next_step": "retry_after_idle",
        "message": "another wechat-ops command is already controlling WeChat",
    }


@contextmanager
def operation_lock(runtime: WeChatOpsRuntime, command_name: str):
    lock_dir = runtime.config.operation_lock_dir
    pid_file = lock_dir / "pid"
    meta_file = lock_dir / "meta.json"
    started = time.time()

    while True:
        try:
            lock_dir.mkdir()
            pid_file.write_text(str(os.getpid()))
            meta_file.write_text(
                json.dumps({"pid": os.getpid(), "command": command_name, "started_at": time.time()})
            )
            break
        except FileExistsError:
            existing_pid = pid_file.read_text().strip() if pid_file.exists() else ""
            if existing_pid.isdigit():
                try:
                    os.kill(int(existing_pid), 0)
                except OSError:
                    import shutil

                    shutil.rmtree(lock_dir, ignore_errors=True)
                    continue
            if time.time() - started >= runtime.config.operation_lock_timeout_seconds:
                raise RuntimeError("operation_busy")
            time.sleep(0.2)

    try:
        yield
    finally:
        import shutil

        shutil.rmtree(lock_dir, ignore_errors=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wechat-ops", description="WeChat automation runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("health")

    session = sub.add_parser("session")
    session_sub = session.add_subparsers(dest="session_command", required=True)
    session_sub.add_parser("current")

    analyze = sub.add_parser("analyze")
    analyze.add_argument("--prompt", required=True)

    chat = sub.add_parser("chat")
    chat_sub = chat.add_subparsers(dest="chat_command", required=True)
    open_cmd = chat_sub.add_parser("open")
    open_cmd.add_argument("--name", required=True)
    chat_sub.add_parser("read-last")
    chat_sub.add_parser("read-visible-messages")
    prepare_cmd = chat_sub.add_parser("prepare-send")
    prepare_cmd.add_argument("--name", required=True)
    prepare_cmd.add_argument("--text", required=True)
    verify_cmd = chat_sub.add_parser("verify-send")
    verify_cmd.add_argument("--tx", required=True)
    commit_cmd = chat_sub.add_parser("commit-send")
    commit_cmd.add_argument("--tx", required=True)
    abort_cmd = chat_sub.add_parser("abort-send")
    abort_cmd.add_argument("--tx", required=True)
    abort_cmd.add_argument("--reason", default="aborted")
    chat_sub.add_parser("inspect-input")
    chat_sub.add_parser("inspect-target")
    chat_sub.add_parser("inspect-search")
    chat_sub.add_parser("inspect-last-incoming")
    send_cmd = chat_sub.add_parser("send")
    send_cmd.add_argument("--name")
    send_cmd.add_argument("--text", required=True)

    unread = sub.add_parser("unread")
    unread_sub = unread.add_subparsers(dest="unread_command", required=True)
    unread_sub.add_parser("list")

    moments = sub.add_parser("moments")
    moments_sub = moments.add_subparsers(dest="moments_command", required=True)
    moments_sub.add_parser("scan")

    watch = sub.add_parser("watch")
    watch_sub = watch.add_subparsers(dest="watch_command", required=True)
    for target in ("unread", "session", "moments", "chat-visible"):
        target_parser = watch_sub.add_parser(target)
        target_parser.add_argument("--iterations", type=int, default=0)

    daemon = sub.add_parser("daemon")
    daemon_sub = daemon.add_subparsers(dest="daemon_command", required=True)
    daemon_run = daemon_sub.add_parser("run")
    daemon_run.add_argument(
        "--watches",
        default="unread,chat_visible,moments",
        help="comma-separated watcher names",
    )
    daemon_run.add_argument("--once", action="store_true")
    daemon_start = daemon_sub.add_parser("start")
    daemon_start.add_argument(
        "--watches",
        default="unread,chat_visible,moments",
        help="comma-separated watcher names",
    )
    daemon_sub.add_parser("status")
    daemon_sub.add_parser("stop")

    worker = sub.add_parser("worker")
    worker_sub = worker.add_subparsers(dest="worker_command", required=True)
    worker_sub.add_parser("start")
    worker_sub.add_parser("status")
    worker_sub.add_parser("stop")

    cleanup = sub.add_parser("cleanup")
    cleanup_sub = cleanup.add_subparsers(dest="cleanup_command", required=True)
    cleanup_sub.add_parser("artifacts")
    return parser


def exit_with(payload, code=0):
    print_json(payload)
    raise SystemExit(code)


def _pid_alive(pid) -> bool:
    try:
        pid_value = int(pid or 0)
    except (TypeError, ValueError):
        return False
    if pid_value <= 0:
        return False
    try:
        os.kill(pid_value, 0)
    except OSError:
        return False
    return True


def _spawn_background(command: List[str], *, log_path, cwd: str) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as handle:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
        )
    return int(process.pid)


def _wait_for_service_status(status_fn, *, timeout_seconds: float = 4.0, poll_seconds: float = 0.2) -> dict:
    deadline = time.time() + timeout_seconds
    latest = status_fn()
    while time.time() < deadline:
        if latest.get("healthy"):
            return latest
        time.sleep(poll_seconds)
        latest = status_fn()
    return latest


def _stop_pid(pid: int) -> bool:
    if not _pid_alive(pid):
        return True
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return True
    for _ in range(20):
        if not _pid_alive(pid):
            return True
        time.sleep(0.2)
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        return True
    for _ in range(10):
        if not _pid_alive(pid):
            return True
        time.sleep(0.1)
    return not _pid_alive(pid)


def _service_payload(name: str, *, status: dict, log_path, launched_pid=None, action="status") -> dict:
    result = {
        "ok": True,
        "service": name,
        "action": action,
        "healthy": status.get("healthy", False),
        "status": status.get("status", "stopped"),
        "pid": status.get("pid"),
        "last_heartbeat_at": status.get("last_heartbeat_at"),
        "log_path": str(log_path),
    }
    if name == "daemon":
        result["watches"] = status.get("watches", [])
    else:
        result["current_job_id"] = status.get("current_job_id")
        result["processed_jobs"] = status.get("processed_jobs", 0)
    if launched_pid is not None:
        result["launched_pid"] = launched_pid
    result["recommended_next_step"] = None if status.get("healthy", False) else f"start_{name}"
    return result


def _daemon_command(runtime: WeChatOpsRuntime) -> str:
    return str(runtime.config.root_dir / "bin" / "wechat-ops")


def _worker_command(runtime: WeChatOpsRuntime) -> str:
    return str(runtime.config.root_dir / "bin" / "xiaoguan-wechat-worker")


def _start_daemon(runtime: WeChatOpsRuntime, watches: Iterable[str]) -> dict:
    status = runtime.daemon_status()
    pid = status.get("pid")
    if pid and _pid_alive(pid):
        if status.get("healthy"):
            return _service_payload(
                "daemon",
                status=status,
                log_path=runtime.config.daemon_log_file,
                action="already_running",
            )
        _stop_pid(int(pid))
        shutil.rmtree(runtime.config.lock_dir, ignore_errors=True)

    watches_arg = ",".join(sorted({item.replace("-", "_") for item in watches}))
    launched_pid = _spawn_background(
        [_daemon_command(runtime), "daemon", "run", "--watches", watches_arg],
        log_path=runtime.config.daemon_log_file,
        cwd=str(runtime.config.root_dir),
    )
    status = _wait_for_service_status(runtime.daemon_status)
    if status.get("pid") is None:
        status["pid"] = launched_pid
    return _service_payload(
        "daemon",
        status=status,
        log_path=runtime.config.daemon_log_file,
        launched_pid=launched_pid,
        action="start",
    )


def _stop_daemon(runtime: WeChatOpsRuntime) -> dict:
    status = runtime.daemon_status()
    pid = status.get("pid")
    stopped = _stop_pid(int(pid)) if pid and _pid_alive(pid) else True
    shutil.rmtree(runtime.config.lock_dir, ignore_errors=True)
    refreshed = runtime.load_daemon_state()
    refreshed["status"] = "stopped"
    refreshed["updated_at"] = now_iso()
    runtime.save_daemon_state(refreshed)
    return {
        **_service_payload(
            "daemon",
            status=runtime.daemon_status(),
            log_path=runtime.config.daemon_log_file,
            action="stop",
        ),
        "stopped": stopped,
    }


def _start_worker(runtime: WeChatOpsRuntime) -> dict:
    status = runtime.worker_status()
    pid = status.get("pid")
    if pid and _pid_alive(pid):
        if status.get("healthy"):
            return _service_payload(
                "worker",
                status=status,
                log_path=runtime.config.worker_log_file,
                action="already_running",
            )
        _stop_pid(int(pid))
        shutil.rmtree(runtime.config.worker_lock_dir, ignore_errors=True)

    launched_pid = _spawn_background(
        [_worker_command(runtime), "run"],
        log_path=runtime.config.worker_log_file,
        cwd=str(runtime.config.root_dir),
    )
    status = _wait_for_service_status(runtime.worker_status)
    if status.get("pid") is None:
        status["pid"] = launched_pid
    return _service_payload(
        "worker",
        status=status,
        log_path=runtime.config.worker_log_file,
        launched_pid=launched_pid,
        action="start",
    )


def _stop_worker(runtime: WeChatOpsRuntime) -> dict:
    status = runtime.worker_status()
    pid = status.get("pid")
    stopped = _stop_pid(int(pid)) if pid and _pid_alive(pid) else True
    shutil.rmtree(runtime.config.worker_lock_dir, ignore_errors=True)
    refreshed = runtime.load_worker_state()
    refreshed["status"] = "stopped"
    refreshed["updated_at"] = now_iso()
    runtime._write_json_file(runtime.config.worker_state_file, refreshed)
    return {
        **_service_payload(
            "worker",
            status=runtime.worker_status(),
            log_path=runtime.config.worker_log_file,
            action="stop",
        ),
        "stopped": stopped,
    }


def command_uses_outer_operation_lock(args) -> bool:
    if args.command in {"watch", "daemon", "worker"}:
        return False
    return True


def run_watch(runtime: WeChatOpsRuntime, target: str, iterations: int) -> None:
    count = 0
    previous = None
    watcher_name = target.replace("-", "_")
    while iterations == 0 or count < iterations:
        try:
            with operation_lock(runtime, f"watch:{target}"):
                if target == "session":
                    current = runtime.session_current()
                else:
                    current = runtime.run_watch_cycle(watcher_name, enqueue_jobs=False)["payload"]
        except RuntimeError as exc:
            if str(exc) != "operation_busy":
                raise
            current = operation_busy_payload()
        if previous is None or canonicalize_json(previous) != canonicalize_json(current):
            print_json(current)
            previous = current
        count += 1
        if iterations == 0 or count < iterations:
            time.sleep(runtime.config.poll_interval_seconds)


def run_daemon(runtime: WeChatOpsRuntime, watches: Iterable[str], once: bool) -> None:
    requested_watches = {item.replace("-", "_") for item in watches}
    runtime.acquire_lock()
    try:
        while True:
            try:
                with operation_lock(runtime, f"daemon:{','.join(sorted(requested_watches))}"):
                    runtime.cleanup_artifacts()
                    runtime.daemon_cycle(
                        watches=requested_watches,
                        enqueue_jobs=True,
                    )
            except RuntimeError as exc:
                if str(exc) != "operation_busy":
                    raise
                if once:
                    raise
                runtime.touch_daemon_state(watches=requested_watches, status="running")
                runtime.append_event(
                    "daemon_cycle_skipped",
                    {"reason": "operation_busy", "watches": sorted(requested_watches)},
                )
            if once:
                break
            time.sleep(runtime.config.poll_interval_seconds)
    finally:
        runtime.cleanup_temp_files()
        runtime.release_lock()


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    runtime = WeChatOpsRuntime(WeChatOpsConfig.load())
    command_name = " ".join(argv or sys.argv[1:])

    if args.command == "cleanup" and args.cleanup_command == "artifacts":
        exit_with(runtime.cleanup_artifacts())

    try:
        if command_uses_outer_operation_lock(args):
            with operation_lock(runtime, command_name):
                return _run_main(runtime, args, parser)
        return _run_main(runtime, args, parser)
    except RuntimeError as exc:
        if str(exc) == "operation_busy":
            exit_with(operation_busy_payload(), 1)
        raise


def _run_main(runtime: WeChatOpsRuntime, args, parser: argparse.ArgumentParser) -> int:
    if args.command == "health":
        payload = runtime.health_check()
        exit_with(payload, 0 if payload.get("ok") else 1)

    if args.command == "session" and args.session_command == "current":
        payload = runtime.session_current()
        exit_with(payload, 0 if payload.get("ok") else 1)

    if args.command == "analyze":
        health = runtime.health_check()
        target = health.get("window")
        payload = runtime.analyze_view(args.prompt, target=target) if target else health
        exit_with(payload, 0 if payload.get("ok") else 1)

    if args.command == "chat":
        if args.chat_command == "open":
            payload = runtime.open_chat(args.name)
            exit_with(payload, 0 if payload.get("ok") else 1)
        if args.chat_command == "read-last":
            health = runtime.health_check()
            target = health.get("window")
            payload = runtime.read_last_incoming_message(target=target) if target else health
            exit_with(payload, 0 if payload.get("ok") else 1)
        if args.chat_command == "read-visible-messages":
            payload = runtime.read_visible_messages()
            exit_with(payload, 0 if payload.get("ok") else 1)
        if args.chat_command == "prepare-send":
            payload = runtime.prepare_send(args.name, args.text)
            exit_with(payload, 0 if payload.get("ok") else 1)
        if args.chat_command == "verify-send":
            payload = runtime.verify_send(args.tx)
            exit_with(payload, 0 if payload.get("ok") else 1)
        if args.chat_command == "commit-send":
            payload = runtime.commit_send(args.tx)
            exit_with(payload, 0 if payload.get("ok") else 1)
        if args.chat_command == "abort-send":
            payload = runtime.abort_send(args.tx, reason=args.reason)
            exit_with(payload, 0 if payload.get("ok") else 1)
        if args.chat_command == "inspect-input":
            payload = runtime.inspect_input()
            exit_with(payload, 0 if payload.get("ok") else 1)
        if args.chat_command == "inspect-target":
            payload = runtime.inspect_target()
            exit_with(payload, 0 if payload.get("ok") else 1)
        if args.chat_command == "inspect-search":
            payload = runtime.inspect_search()
            exit_with(payload, 0 if payload.get("ok") else 1)
        if args.chat_command == "inspect-last-incoming":
            payload = runtime.inspect_last_incoming()
            exit_with(payload, 0 if payload.get("ok") else 1)
        if args.chat_command == "send":
            payload = runtime.send_text(args.text, name=args.name)
            exit_with(payload, 0 if payload.get("ok") else 1)

    if args.command == "unread" and args.unread_command == "list":
        payload = runtime.unread_list()
        exit_with(payload, 0 if payload.get("ok") else 1)

    if args.command == "moments" and args.moments_command == "scan":
        payload = runtime.moments_scan()
        exit_with(payload, 0 if payload.get("ok") else 1)

    if args.command == "watch":
        run_watch(runtime, args.watch_command, args.iterations)
        return 0

    if args.command == "daemon" and args.daemon_command == "run":
        watches = {item.strip() for item in args.watches.split(",") if item.strip()}
        run_daemon(runtime, watches, args.once)
        return 0
    if args.command == "daemon" and args.daemon_command == "start":
        watches = {item.strip() for item in args.watches.split(",") if item.strip()}
        payload = _start_daemon(runtime, watches)
        exit_with(payload, 0 if payload.get("healthy") else 1)
    if args.command == "daemon" and args.daemon_command == "status":
        payload = _service_payload(
            "daemon",
            status=runtime.daemon_status(),
            log_path=runtime.config.daemon_log_file,
            action="status",
        )
        exit_with(payload, 0 if payload.get("healthy") else 1)
    if args.command == "daemon" and args.daemon_command == "stop":
        payload = _stop_daemon(runtime)
        exit_with(payload, 0 if payload.get("stopped") else 1)

    if args.command == "worker" and args.worker_command == "start":
        payload = _start_worker(runtime)
        exit_with(payload, 0 if payload.get("healthy") else 1)
    if args.command == "worker" and args.worker_command == "status":
        payload = _service_payload(
            "worker",
            status=runtime.worker_status(),
            log_path=runtime.config.worker_log_file,
            action="status",
        )
        exit_with(payload, 0 if payload.get("healthy") else 1)
    if args.command == "worker" and args.worker_command == "stop":
        payload = _stop_worker(runtime)
        exit_with(payload, 0 if payload.get("stopped") else 1)

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
