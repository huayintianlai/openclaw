#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional


ROOT = Path("/Users/xiaojiujiu2/.openclaw")
WORKSPACE = ROOT / "workspace"
REPORT_PATH = WORKSPACE / "acceptance_latest.json"
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
ACCEPT_TOKEN_RE = re.compile(r"ACCEPT-[A-Z-]+-OK")


def load_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def command_env() -> dict[str, str]:
    env = os.environ.copy()
    dot_env = load_env_file(ROOT / ".env")
    env.update(dot_env)
    env.setdefault("MEM0_TELEMETRY", "false")
    return env


def run(cmd: list[str], timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        env=command_env(),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def extract_json_blob(text: str) -> dict:
    starts = [
        re.search(r"\{\s*\"runId\"", text),
        re.search(r"\{\s*\"status\"", text),
        re.search(r"\{\s*\"payloads\"", text),
    ]
    match = next((item for item in starts if item), None)
    if not match:
        raise ValueError("No JSON payload found")
    decoder = json.JSONDecoder()
    payload, _ = decoder.raw_decode(text[match.start():])
    return payload


def sanitize_output(text: str) -> str:
    text = text.replace("\x00", "")
    return ANSI_ESCAPE_RE.sub("", text)


def extract_accept_token(text: str) -> Optional[str]:
    match = ACCEPT_TOKEN_RE.search(text)
    return match.group(0) if match else None


def run_agent(agent: str, message: str, local: bool = False, timeout: int = 300) -> dict:
    cmd = ["openclaw", "agent"]
    if local:
        cmd.append("--local")
    cmd.extend(["--agent", agent, "--message", message, "--json"])
    completed = run(cmd, timeout=timeout)
    combined_output = sanitize_output(
        "\n".join(part for part in [completed.stdout, completed.stderr] if part)
    )
    try:
        payload = extract_json_blob(combined_output)
    except ValueError:
        accept_token = extract_accept_token(message)
        echoed_token = extract_accept_token(combined_output)
        if completed.returncode == 0 and accept_token and echoed_token == accept_token:
            payload = {
                "result": {
                    "payloads": [{"text": echoed_token, "mediaUrl": None}],
                    "meta": {"fallback": "accept-token"},
                }
            }
        else:
            raise
    if "result" not in payload and "payloads" in payload:
        payload = {"result": payload}
    return {
        "agent": agent,
        "local": local,
        "exit_code": completed.returncode,
        "payloads": payload["result"]["payloads"],
        "meta": payload["result"]["meta"],
    }


def main() -> int:
    report: dict[str, object] = {"checks": []}

    health = run(["openclaw", "health"], timeout=60)
    report["checks"].append(
        {
            "name": "gateway_health",
            "ok": health.returncode == 0,
            "stdout": health.stdout.strip(),
        }
    )

    prompts = [
        (
            "xiaodong",
            False,
            "这是验收测试。请只输出一句：ACCEPT-XD-OK。不要调用工具。",
        ),
        (
            "xiaoguan",
            False,
            "这是验收测试。请只输出一句：ACCEPT-XG-OK。不要调用工具。",
        ),
        (
            "finance",
            False,
            "这是验收测试。请只输出一句：ACCEPT-FIN-OK。不要调用工具。",
        ),
        (
            "echo",
            False,
            "这是验收测试。请只输出一句：ACCEPT-ECHO-OK。不要调用工具。",
        ),
        (
            "aduan",
            False,
            "这是验收测试。请只输出一句：ACCEPT-ADUAN-OK。不要调用工具。",
        ),
        (
            "xiaodong_crossborder_scout",
            True,
            "这是验收测试。请只输出一句：ACCEPT-SCOUT-OK。不要调用工具。",
        ),
        (
            "xiaodong_ai_scout",
            True,
            "这是验收测试。请只输出一句：ACCEPT-AI-SCOUT-OK。不要调用工具。",
        ),
        (
            "aduan_growth",
            True,
            "这是验收测试。请只输出一句：ACCEPT-ADG-OK。不要调用工具。",
        ),
        (
            "aduan_learner",
            True,
            "这是验收测试。请只输出一句：ACCEPT-ADL-OK。不要调用工具。",
        ),
        (
            "aduan_reflector",
            True,
            "这是验收测试。请只输出一句：ACCEPT-ADR-OK。不要调用工具。",
        ),
    ]

    for agent, local, prompt in prompts:
        try:
            result = run_agent(agent, prompt, local=local, timeout=180)
            payload_text = result["payloads"][-1].get("text", "") if result["payloads"] else ""
            expected_token = extract_accept_token(prompt)
            report["checks"].append(
                {
                    "name": f"agent_{agent}",
                    "ok": bool(expected_token and expected_token in payload_text),
                    "local": local,
                    "payloads": result["payloads"],
                    "expected": expected_token,
                }
            )
        except Exception as exc:  # pragma: no cover
            report["checks"].append(
                {
                    "name": f"agent_{agent}",
                    "ok": False,
                    "local": local,
                    "error": str(exc),
                }
            )

    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(REPORT_PATH)
    failed = [check for check in report["checks"] if not check.get("ok")]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
