from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

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


def test_scaffold_outputs_import_first_hook() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "codex_hookkit.cli", "scaffold"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "from codex_hookkit import HookPayload, SecretPolicy, deny" in result.stdout
    assert "HookPayload.from_stdin(schema='pre-tool-use')" in result.stdout


def test_scaffold_outputs_codex_review_hooks() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "codex_hookkit.cli", "scaffold", "--kind", "codex-review-hooks"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "PostToolUse" in output["hooks"]
    assert "Stop" in output["hooks"]
    assert "request-review" in result.stdout
    assert "run-review" in result.stdout


def test_scaffold_writes_output_file(tmp_path: Path) -> None:
    output = tmp_path / "hooks" / "secret_guard.py"
    result = subprocess.run(
        [sys.executable, "-m", "codex_hookkit.cli", "scaffold", "--output", str(output)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert output.exists()
    assert "def main() -> int:" in output.read_text(encoding="utf-8")


def test_schemas_can_print_file_style_names() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "codex_hookkit.cli", "schemas", "--direction", "both"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "pre-tool-use.command.input.schema.json" in result.stdout
    assert "pre-tool-use.command.output.schema.json" in result.stdout
