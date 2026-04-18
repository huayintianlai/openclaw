from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


def _default_root() -> Path:
    return Path("/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime")


@dataclass
class WeChatOpsConfig:
    root_dir: Path = field(default_factory=_default_root)
    desktop_dir: Path = field(default_factory=lambda: Path.home() / "Desktop")
    account_id: str = "default"
    peekaboo_bin: str = "/opt/homebrew/bin/peekaboo"
    env_file: str = os.path.expanduser("~/.openclaw/.env")
    app_candidates: List[str] = field(
        default_factory=lambda: ["微信", "WeChat", "com.tencent.xinWeChat"]
    )
    input_x: int = 1520
    input_y: int = 966
    timeout_seconds: int = 20
    unread_timeout_seconds: int = 10
    poll_interval_seconds: int = 8
    artifact_ttl_hours: int = 24
    desktop_artifact_ttl_minutes: int = 15
    keep_failed_samples: int = 20
    min_user_idle_seconds: float = 3.0
    stable_chat_attempts: int = 2
    stable_chat_delay_ms: int = 700
    tx_ttl_hours: int = 6
    send_chunk_max_chars: int = 24
    send_chunk_delay_ms: int = 160
    operation_lock_timeout_seconds: int = 8
    watcher_failure_threshold: int = 3
    moments_seen_ttl_hours: int = 168
    queue_retention_hours: int = 168
    processing_lease_seconds: int = 60
    observation_attempts: int = 2
    observation_delay_ms: int = 250

    @property
    def config_file(self) -> Path:
        return self.root_dir / "config" / "wechat-ops.json"

    @property
    def state_dir(self) -> Path:
        return self.root_dir / "state"

    @property
    def artifacts_dir(self) -> Path:
        return self.root_dir / "artifacts"

    @property
    def logs_dir(self) -> Path:
        return self.root_dir / "logs"

    @property
    def temp_dir(self) -> Path:
        return self.artifacts_dir / "tmp"

    @property
    def failure_dir(self) -> Path:
        return self.artifacts_dir / "failures"

    @property
    def state_file(self) -> Path:
        return self.state_dir / "runtime-state.json"

    @property
    def events_file(self) -> Path:
        return self.state_dir / "events.jsonl"

    @property
    def lock_dir(self) -> Path:
        return self.state_dir / "daemon.lock"

    @property
    def daemon_state_file(self) -> Path:
        return self.state_dir / "daemon-state.json"

    @property
    def operation_lock_dir(self) -> Path:
        return self.state_dir / "operation.lock"

    @property
    def worker_lock_dir(self) -> Path:
        return self.state_dir / "worker.lock"

    @property
    def worker_state_file(self) -> Path:
        return self.state_dir / "worker-state.json"

    @property
    def tx_dir(self) -> Path:
        return self.state_dir / "transactions"

    @property
    def watchers_dir(self) -> Path:
        return self.state_dir / "watchers"

    @property
    def jobs_dir(self) -> Path:
        return self.state_dir / "jobs"

    @property
    def jobs_pending_dir(self) -> Path:
        return self.jobs_dir / "pending"

    @property
    def jobs_processing_dir(self) -> Path:
        return self.jobs_dir / "processing"

    @property
    def jobs_done_dir(self) -> Path:
        return self.jobs_dir / "done"

    @property
    def results_dir(self) -> Path:
        return self.state_dir / "results"

    @property
    def results_pending_dir(self) -> Path:
        return self.results_dir / "pending"

    @property
    def results_consumed_dir(self) -> Path:
        return self.results_dir / "consumed"

    @property
    def results_failed_dir(self) -> Path:
        return self.results_dir / "failed"

    @property
    def moments_seen_file(self) -> Path:
        return self.watchers_dir / "moments-seen.json"

    @property
    def probe_path(self) -> Path:
        return self.temp_dir / "probe.png"

    @property
    def see_path(self) -> Path:
        return self.temp_dir / "see.png"

    @property
    def navrail_path(self) -> Path:
        return self.temp_dir / "navrail.png"

    @property
    def sidebar_path(self) -> Path:
        return self.temp_dir / "sidebar.png"

    @property
    def content_path(self) -> Path:
        return self.temp_dir / "content.png"

    @property
    def vision_ocr_script(self) -> Path:
        return self.root_dir / "scripts" / "vision_ocr.swift"

    @property
    def daemon_log_file(self) -> Path:
        return self.logs_dir / "daemon.log"

    @property
    def worker_log_file(self) -> Path:
        return self.logs_dir / "worker.log"

    def watcher_state_path(self, watcher: str) -> Path:
        return self.watchers_dir / f"{watcher}.json"

    @classmethod
    def load(cls, root_dir: Path | None = None) -> "WeChatOpsConfig":
        config = cls(root_dir=root_dir or _default_root())
        data = cls._load_json(config.config_file)
        if data:
            config = cls._merge(config, data)
        config.ensure_dirs()
        return config

    @staticmethod
    def _load_json(path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        return json.loads(path.read_text())

    @classmethod
    def _merge(cls, base: "WeChatOpsConfig", overrides: Dict[str, Any]) -> "WeChatOpsConfig":
        merged = cls(
            root_dir=Path(overrides.get("root_dir", str(base.root_dir))),
            desktop_dir=Path(overrides.get("desktop_dir", str(base.desktop_dir))),
            account_id=overrides.get("account_id", base.account_id),
            peekaboo_bin=overrides.get("peekaboo_bin", base.peekaboo_bin),
            env_file=overrides.get("env_file", base.env_file),
            app_candidates=overrides.get("app_candidates", list(base.app_candidates)),
            input_x=int(overrides.get("input_x", base.input_x)),
            input_y=int(overrides.get("input_y", base.input_y)),
            timeout_seconds=int(overrides.get("timeout_seconds", base.timeout_seconds)),
            unread_timeout_seconds=int(
                overrides.get("unread_timeout_seconds", base.unread_timeout_seconds)
            ),
            poll_interval_seconds=int(
                overrides.get("poll_interval_seconds", base.poll_interval_seconds)
            ),
            artifact_ttl_hours=int(
                overrides.get("artifact_ttl_hours", base.artifact_ttl_hours)
            ),
            desktop_artifact_ttl_minutes=int(
                overrides.get(
                    "desktop_artifact_ttl_minutes",
                    base.desktop_artifact_ttl_minutes,
                )
            ),
            keep_failed_samples=int(
                overrides.get("keep_failed_samples", base.keep_failed_samples)
            ),
            min_user_idle_seconds=float(
                overrides.get("min_user_idle_seconds", base.min_user_idle_seconds)
            ),
            stable_chat_attempts=int(
                overrides.get("stable_chat_attempts", base.stable_chat_attempts)
            ),
            stable_chat_delay_ms=int(
                overrides.get("stable_chat_delay_ms", base.stable_chat_delay_ms)
            ),
            tx_ttl_hours=int(overrides.get("tx_ttl_hours", base.tx_ttl_hours)),
            send_chunk_max_chars=int(
                overrides.get("send_chunk_max_chars", base.send_chunk_max_chars)
            ),
            send_chunk_delay_ms=int(
                overrides.get("send_chunk_delay_ms", base.send_chunk_delay_ms)
            ),
            operation_lock_timeout_seconds=int(
                overrides.get(
                    "operation_lock_timeout_seconds",
                    base.operation_lock_timeout_seconds,
                )
            ),
            watcher_failure_threshold=int(
                overrides.get(
                    "watcher_failure_threshold",
                    base.watcher_failure_threshold,
                )
            ),
            moments_seen_ttl_hours=int(
                overrides.get("moments_seen_ttl_hours", base.moments_seen_ttl_hours)
            ),
            queue_retention_hours=int(
                overrides.get("queue_retention_hours", base.queue_retention_hours)
            ),
            processing_lease_seconds=int(
                overrides.get(
                    "processing_lease_seconds",
                    base.processing_lease_seconds,
                )
            ),
            observation_attempts=int(
                overrides.get("observation_attempts", base.observation_attempts)
            ),
            observation_delay_ms=int(
                overrides.get("observation_delay_ms", base.observation_delay_ms)
            ),
        )
        return merged

    def ensure_dirs(self) -> None:
        for path in (
            self.root_dir,
            self.state_dir,
            self.artifacts_dir,
            self.temp_dir,
            self.failure_dir,
            self.logs_dir,
            self.tx_dir,
            self.watchers_dir,
            self.jobs_dir,
            self.jobs_pending_dir,
            self.jobs_processing_dir,
            self.jobs_done_dir,
            self.results_dir,
            self.results_pending_dir,
            self.results_consumed_dir,
            self.results_failed_dir,
            self.config_file.parent,
        ):
            path.mkdir(parents=True, exist_ok=True)
