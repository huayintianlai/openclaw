#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import requests


ROOT = Path("/Users/xiaojiujiu2/.openclaw")
ENV_FILE = ROOT / ".env"
REPORT_PATH = ROOT / "workspace" / "acceptance_xiaoguan_image_latest.json"
DEFAULT_IMAGE = ROOT / "workspace" / "xiaoguan" / "inbox" / "2026-03-23" / "om_x100b533b0bcb38a8b26586d8685ac66__01__ddb3504a-b382-45f5-bd2b-4be5c422ff64.png"
AREA = "acceptance-xiaoguan-image"

EXPECTED_CONTACT = "CD-刘-炎"
EXPECTED_LEFT = "新蛋能不能入驻"
EXPECTED_RIGHT = "暂时还不能，骚瑞"
FORBIDDEN_REPLY_SNIPPETS = [
    "读不到",
    "image_key",
    "file_key",
    "原图",
    "用户帮",
]


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def merged_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(load_env())
    return env


def extract_json_blob(text: str) -> dict:
    match = re.search(r"\{\s*\"runId\"", text)
    if not match:
        match = re.search(r"\{\s*\"payloads\"", text)
    if not match:
        raise ValueError("No JSON payload found in CLI output")
    payload, _ = json.JSONDecoder().raw_decode(text[match.start():])
    return payload


def run(cmd: list[str], timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        env=merged_env(),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def gateway_reset_main_session() -> dict:
    cmd = [
        "openclaw",
        "gateway",
        "call",
        "sessions.reset",
        "--json",
        "--params",
        json.dumps({"key": "agent:xiaoguan:main", "reason": "reset"}, ensure_ascii=False),
    ]
    completed = run(cmd, timeout=30)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr or completed.stdout)
    return json.loads(completed.stdout[completed.stdout.find("{"):])


def knowledge_health(env: dict[str, str]) -> dict:
    last_error: Optional[Exception] = None
    for _ in range(10):
        try:
            response = requests.get("http://127.0.0.1:8002/health", timeout=20)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # pragma: no cover - transient startup race
            last_error = exc
            time.sleep(1)
    raise last_error or RuntimeError("knowledge health check failed")


def ingest_image(env: dict[str, str], image_path: Path) -> dict:
    headers = {"Authorization": f"Bearer {env['KNOWLEDGE_API_TOKEN']}"}
    with image_path.open("rb") as handle:
        response = requests.post(
            "http://127.0.0.1:8002/ingest/file",
            headers=headers,
            files={"file": (image_path.name, handle, "image/png")},
            data={
                "area": AREA,
                "access_level": "global",
                "owner_type": "agent",
                "owner_id": "xiaoguan",
                "force_reindex": "true",
            },
            timeout=180,
        )
    response.raise_for_status()
    return response.json()


def knowledge_search(env: dict[str, str], query: str) -> dict:
    headers = {"Authorization": f"Bearer {env['KNOWLEDGE_API_TOKEN']}"}
    response = requests.post(
        "http://127.0.0.1:8002/search",
        headers=headers,
        data={
            "query": query,
            "area": AREA,
            "access_level": "global",
            "limit": "3",
            "min_score": "0.05",
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def run_agent_acceptance(image_path: Path) -> dict:
    prompt = (
        f"[media attached: {image_path} (image/png) | {image_path}]\n"
        f"{image_path}\n"
        f"先用 knowledge_search 在 area={AREA} 检索这张截图，必要时再结合本地路径。\n"
        "请直接回答：\n"
        f"1. 会话对象是谁\n"
        f"2. 左侧白气泡原文是什么\n"
        f"3. 右侧绿色气泡是谁发的，原文是什么\n"
        "不要说读不到，不要要求 image_key，也不要让用户帮忙。"
    )
    completed = run(
        ["openclaw", "agent", "--agent", "xiaoguan", "--message", prompt, "--json"],
        timeout=180,
    )
    payload = extract_json_blob(completed.stdout)
    result = payload.get("result", payload)
    final_payload = result["payloads"][-1]
    return {
        "exit_code": completed.returncode,
        "text": final_payload.get("text", ""),
        "payload": final_payload,
        "meta": result.get("meta", {}),
    }


def assert_contains(label: str, haystack: str, needle: str, report: list[dict]) -> None:
    report.append({"check": label, "ok": needle in haystack, "expected": needle})


def assert_not_contains(label: str, haystack: str, needle: str, report: list[dict]) -> None:
    report.append({"check": label, "ok": needle not in haystack, "forbidden": needle})


def main() -> int:
    env = load_env()
    report: dict[str, object] = {"checks": []}
    checks: list[dict] = report["checks"]  # type: ignore[assignment]

    if not DEFAULT_IMAGE.exists():
        checks.append({"check": "image_exists", "ok": False, "path": str(DEFAULT_IMAGE)})
        REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(REPORT_PATH)
        return 1

    checks.append({"check": "image_exists", "ok": True, "path": str(DEFAULT_IMAGE)})

    health = knowledge_health(env)
    checks.append({"check": "knowledge_health", "ok": health.get("status") == "ok", "health": health})

    reset_result = gateway_reset_main_session()
    checks.append({"check": "reset_main_session", "ok": bool(reset_result.get("ok")), "result": reset_result})

    ingest = ingest_image(env, DEFAULT_IMAGE)
    checks.append({"check": "knowledge_ingest", "ok": ingest.get("status") == "success", "result": ingest})

    search_by_name = knowledge_search(env, DEFAULT_IMAGE.name)
    checks.append(
        {
            "check": "knowledge_search_filename",
            "ok": len(search_by_name.get("results", [])) > 0,
            "result": search_by_name,
        }
    )
    if search_by_name.get("results"):
        top_text = search_by_name["results"][0].get("text", "")
        assert_contains("knowledge_has_contact", top_text, EXPECTED_CONTACT, checks)
        assert_contains("knowledge_has_left_text", top_text, EXPECTED_LEFT, checks)
        assert_contains("knowledge_has_right_text", top_text, EXPECTED_RIGHT, checks)
        assert_contains("knowledge_has_role_section", top_text, "角色与方向", checks)
    else:
        checks.append({"check": "knowledge_has_contact", "ok": False, "reason": "no search results"})

    agent = run_agent_acceptance(DEFAULT_IMAGE)
    checks.append({"check": "agent_exit_code", "ok": agent["exit_code"] == 0, "exit_code": agent["exit_code"]})
    checks.append({"check": "agent_payload_nonempty", "ok": bool(agent["text"].strip()), "text": agent["text"]})
    assert_contains("agent_contact", agent["text"], EXPECTED_CONTACT, checks)
    assert_contains("agent_left_text", agent["text"], EXPECTED_LEFT, checks)
    assert_contains("agent_right_text", agent["text"], "暂时还不能", checks)
    for forbidden in FORBIDDEN_REPLY_SNIPPETS:
        assert_not_contains(f"agent_forbidden_{forbidden}", agent["text"], forbidden, checks)

    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(REPORT_PATH)
    return 0 if all(check.get("ok") for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
