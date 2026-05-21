from __future__ import annotations

import json
import subprocess
import sys


BASE_PAYLOAD = {
    "cwd": "/tmp/project",
    "hook_event_name": "PreToolUse",
    "model": "gpt-5",
    "permission_mode": "default",
    "session_id": "session",
    "tool_name": "shell",
    "tool_use_id": "tool-use",
    "transcript_path": None,
    "turn_id": "turn",
}


def run_guard(command: str) -> subprocess.CompletedProcess[str]:
    payload = dict(BASE_PAYLOAD, tool_input={"cmd": command})
    return subprocess.run(
        [sys.executable, "-m", "codex_hookkit.cli", "guard"],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )


def test_guard_allows_ordinary_command() -> None:
    result = run_guard("pwd")
    assert result.returncode == 0
    assert result.stderr == ""


def test_guard_denies_secret_file_access() -> None:
    result = run_guard("cat .env")
    assert result.returncode == 2
    assert "Blocked direct secret file access" in result.stderr


def test_guard_json_output_validates() -> None:
    payload = dict(BASE_PAYLOAD, tool_input={"cmd": "cat .env"})
    result = subprocess.run(
        [sys.executable, "-m", "codex_hookkit.cli", "guard", "--json-output"],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
