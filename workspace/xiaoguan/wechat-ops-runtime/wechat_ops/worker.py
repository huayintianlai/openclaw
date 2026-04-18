from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from .config import WeChatOpsConfig
from .runtime import WeChatOpsRuntime, json_safe, now_iso, parse_iso


UTC = timezone.utc


class WeChatOpsWorker:
    def __init__(self, config: Optional[WeChatOpsConfig] = None) -> None:
        self.runtime = WeChatOpsRuntime(config or WeChatOpsConfig.load())
        self.config = self.runtime.config

    def load_state(self) -> Dict[str, Any]:
        return self.runtime._read_json_file(self.config.worker_state_file, {})

    def save_state(self, payload: Dict[str, Any]) -> None:
        self.runtime._write_json_file(self.config.worker_state_file, payload)

    def touch_state(
        self,
        *,
        status: str,
        current_job_id: Optional[str] = None,
        processed_jobs: Optional[int] = None,
        last_error: Optional[str] = None,
    ) -> Dict[str, Any]:
        state = self.load_state()
        if processed_jobs is None:
            processed_jobs = int(state.get("processed_jobs", 0))
        payload = {
            "pid": os.getpid(),
            "status": status,
            "current_job_id": current_job_id,
            "processed_jobs": processed_jobs,
            "last_error": last_error,
            "last_heartbeat_at": now_iso(),
            "updated_at": now_iso(),
        }
        self.save_state(payload)
        return payload

    @contextmanager
    def lock(self):
        lock_dir = self.config.worker_lock_dir
        pid_file = lock_dir / "pid"
        started = time.time()
        while True:
            try:
                lock_dir.mkdir()
                pid_file.write_text(str(os.getpid()))
                break
            except FileExistsError:
                existing_pid = pid_file.read_text().strip() if pid_file.exists() else ""
                if existing_pid.isdigit():
                    try:
                        os.kill(int(existing_pid), 0)
                    except OSError:
                        shutil.rmtree(lock_dir, ignore_errors=True)
                        continue
                if time.time() - started >= self.config.operation_lock_timeout_seconds:
                    raise RuntimeError("worker_busy")
                time.sleep(0.2)
        try:
            yield
        finally:
            state = self.load_state()
            if state:
                state["status"] = "stopped"
                state["updated_at"] = now_iso()
                self.save_state(state)
            shutil.rmtree(lock_dir, ignore_errors=True)

    def reclaim_stale_processing(self) -> int:
        reclaimed = 0
        now = datetime.now(tz=UTC)
        for path in sorted(self.config.jobs_processing_dir.glob("*.json")):
            job = self.runtime._read_json_file(path, {})
            claimed_at = parse_iso(job.get("claimed_at"))
            if not claimed_at:
                continue
            if (now - claimed_at).total_seconds() <= self.config.processing_lease_seconds:
                continue
            job.pop("claimed_at", None)
            job.pop("worker_pid", None)
            self.runtime._write_json_file(self.config.jobs_pending_dir / path.name, job)
            path.unlink(missing_ok=True)
            reclaimed += 1
        if reclaimed:
            self.runtime.append_event("worker_reclaimed_jobs", {"count": reclaimed})
        return reclaimed

    def claim_next_job(self) -> Optional[Dict[str, Any]]:
        for path in sorted(self.config.jobs_pending_dir.glob("*.json")):
            job = self.runtime._read_json_file(path, {})
            if not job:
                continue
            job["claimed_at"] = now_iso()
            job["worker_pid"] = os.getpid()
            target = self.config.jobs_processing_dir / path.name
            try:
                path.replace(target)
            except FileNotFoundError:
                continue
            self.runtime._write_json_file(target, job)
            return {"job": job, "path": target}
        return None

    def write_result(
        self,
        *,
        job: Dict[str, Any],
        status: str,
        payload: Dict[str, Any],
        failed: bool = False,
    ) -> Dict[str, Any]:
        result = {
            "result_id": uuid4().hex,
            "job_id": job["job_id"],
            "type": job["type"],
            "created_at": now_iso(),
            "source": job["source"],
            "cursor": job["cursor"],
            "signature": job["signature"],
            "status": status,
            "payload": json_safe(payload),
        }
        base = self.config.results_failed_dir if failed else self.config.results_pending_dir
        self.runtime._write_json_file(base / f"{result['result_id']}.json", result)
        return result

    def _handle_unread_snapshot(self, job: Dict[str, Any]) -> Dict[str, Any]:
        items = job["payload"].get("items", [])
        payload_summary = job["payload"].get("summary", {})
        return {
            "summary": {
                "unread_count": len(items),
                "visible_unread_session_count": payload_summary.get(
                    "visible_unread_session_count",
                    len(items),
                ),
                "app_has_unread_badge": payload_summary.get(
                    "app_has_unread_badge",
                    job["payload"].get("app_has_unread_badge", False),
                ),
                "app_unread_badge_count": payload_summary.get(
                    "app_unread_badge_count",
                    job["payload"].get("app_unread_badge_count"),
                ),
                "names": [item.get("name") for item in items],
            },
            "watcher_payload": job["payload"],
        }

    def _handle_chat_visible_delta(self, job: Dict[str, Any]) -> Dict[str, Any]:
        added = job["payload"].get("added_messages", [])
        return {
            "summary": {
                "added_count": len(added),
                "speakers": sorted({item.get("speaker") for item in added if item.get("speaker")}),
            },
            "watcher_payload": job["payload"],
        }

    def _handle_moments_unseen(self, job: Dict[str, Any]) -> Dict[str, Any]:
        items = job["payload"].get("items", [])
        return {
            "summary": {
                "card_count": len(items),
                "authors": sorted({item.get("author") for item in items if item.get("author")}),
            },
            "watcher_payload": job["payload"],
        }

    def _handle_watcher_health(self, job: Dict[str, Any]) -> Dict[str, Any]:
        state = job["payload"].get("state", {})
        return {
            "summary": {
                "watcher": job["payload"].get("watcher"),
                "status": job["payload"].get("status"),
                "error_code": state.get("last_error_code"),
            },
            "watcher_payload": job["payload"],
        }

    def process_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        handlers = {
            "unread.snapshot.changed": self._handle_unread_snapshot,
            "chat.visible.delta": self._handle_chat_visible_delta,
            "moments.cards.unseen": self._handle_moments_unseen,
            "watcher.health.changed": self._handle_watcher_health,
        }
        handler = handlers.get(job["type"])
        if handler is None:
            raise RuntimeError(f"unsupported_job_type:{job['type']}")
        return handler(job)

    def finalize_job(
        self,
        *,
        job: Dict[str, Any],
        path: Path,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        if error is not None:
            retry_count = int(job.get("retry_count", 0)) + 1
            job["retry_count"] = retry_count
            job.pop("claimed_at", None)
            job.pop("worker_pid", None)
            if retry_count >= int(job.get("max_retries", 3)):
                self.write_result(
                    job=job,
                    status="failed",
                    payload={"error": error, "watcher_payload": job.get("payload", {})},
                    failed=True,
                )
                self.runtime._write_json_file(self.config.jobs_done_dir / path.name, job)
                path.unlink(missing_ok=True)
                self.runtime.append_event(
                    "worker_job_failed",
                    {"job_id": job["job_id"], "type": job["type"], "error": error},
                )
                return
            self.runtime._write_json_file(self.config.jobs_pending_dir / path.name, job)
            path.unlink(missing_ok=True)
            self.runtime.append_event(
                "worker_job_requeued",
                {"job_id": job["job_id"], "type": job["type"], "retry_count": retry_count},
            )
            return

        if result is not None:
            self.write_result(job=job, status="ready", payload=result)
            self.runtime._write_json_file(self.config.jobs_done_dir / path.name, job)
            path.unlink(missing_ok=True)
            self.runtime.append_event(
                "worker_job_done",
                {"job_id": job["job_id"], "type": job["type"]},
            )

    def run(self, *, once: bool = False) -> int:
        with self.lock():
            self.reclaim_stale_processing()
            processed = int(self.load_state().get("processed_jobs", 0))
            while True:
                claim = self.claim_next_job()
                if claim is None:
                    self.touch_state(status="idle", processed_jobs=processed)
                    if once:
                        return 0
                    time.sleep(self.config.poll_interval_seconds)
                    continue
                job = claim["job"]
                path = claim["path"]
                self.touch_state(
                    status="running",
                    current_job_id=job["job_id"],
                    processed_jobs=processed,
                )
                try:
                    result = self.process_job(job)
                except Exception as exc:  # pragma: no cover - defensive runtime path
                    self.touch_state(
                        status="error",
                        current_job_id=job["job_id"],
                        processed_jobs=processed,
                        last_error=str(exc),
                    )
                    self.finalize_job(job=job, path=path, error=str(exc))
                    if once:
                        return 1
                    continue

                processed += 1
                self.touch_state(
                    status="running",
                    current_job_id=job["job_id"],
                    processed_jobs=processed,
                )
                self.finalize_job(job=job, path=path, result=result)
                if once:
                    self.touch_state(status="idle", processed_jobs=processed)
                    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xiaoguan-wechat-worker")
    parser.add_argument("command", choices=["run"])
    parser.add_argument("--once", action="store_true")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    worker = WeChatOpsWorker()
    if args.command == "run":
        return worker.run(once=args.once)
    return 2


if __name__ == "__main__":
    sys.exit(main())
