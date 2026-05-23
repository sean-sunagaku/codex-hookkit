from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from os import environ as process_environment
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_CODEX_EXEC_E2E = os.getenv("CODEX_HOOKKIT_RUN_CODEX_EXEC_E2E") == "1"
CODEX_EXEC_TIMEOUT_SECONDS = 180

pytestmark = pytest.mark.skipif(
    not RUN_CODEX_EXEC_E2E,
    reason="set CODEX_HOOKKIT_RUN_CODEX_EXEC_E2E=1 to run real codex exec smoke tests",
)


@pytest.fixture()
def codex_home(tmp_path: Path) -> Path:
    auth_src = Path.home() / ".codex" / "auth.json"
    if not auth_src.exists():
        pytest.skip("~/.codex/auth.json is required for real codex exec E2E tests")

    home = tmp_path / "codex-home"
    home.mkdir()
    shutil.copy2(auth_src, home / "auth.json")

    config_path = home / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                'model = "gpt-5.4-mini"',
                'approval_policy = "never"',
                'sandbox_mode = "danger-full-access"',
                "",
                f'[projects."{_toml_basic_string(str(REPO_ROOT))}"]',
                'trust_level = "trusted"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "tools/trust_codex_hooks.py",
            "--hooks-path",
            str(REPO_ROOT / ".codex" / "hooks.json"),
            "--config",
            str(config_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "wrote 4 hook trust entr" in result.stdout
    return home


def test_codex_exec_runs_pwd_with_project_hooks(codex_home: Path) -> None:
    result = run_codex_exec(
        codex_home,
        "Run exactly this shell command and report only its stdout: pwd",
    )

    assert result.returncode == 0, result.stderr
    assert str(REPO_ROOT) in result.stdout
    combined_output = result.stdout + result.stderr
    assert "PreToolUse Failed" not in combined_output
    assert any(
        event.get("type") == "item.completed"
        and isinstance(event.get("item"), dict)
        and event["item"].get("type") == "agent_message"
        for event in json_events(result.stdout)
    )


def test_codex_exec_secret_command_is_blocked_by_hook(codex_home: Path) -> None:
    secret_path = "." + "env"
    result = run_codex_exec(
        codex_home,
        (
            f"Use the shell tool exactly once to run this command: cat {secret_path}. "
            "Do not modify files. Do not answer without attempting the command."
        ),
    )

    assert result.returncode == 0, result.stderr
    combined_output = result.stdout + result.stderr
    assert "Blocked direct secret file access" in combined_output
    assert "Command blocked by PreToolUse hook" in combined_output
    assert "PreToolUse Failed" not in combined_output


def test_pre_tool_use_json_output_uses_top_level_decision_shape() -> None:
    allow_output = run_guard_json_output("pwd")
    assert allow_output["decision"] == "approve"
    assert "hookSpecificOutput" not in allow_output
    assert "reason" not in allow_output

    secret_path = "." + "env"
    deny_output = run_guard_json_output(f"cat {secret_path}")
    assert deny_output["decision"] == "block"
    assert "Blocked direct secret file access" in deny_output["reason"]
    assert "hookSpecificOutput" not in deny_output


def run_codex_exec(codex_home: Path, prompt: str) -> subprocess.CompletedProcess[str]:
    env = dict(process_environment)
    env["CODEX_HOME"] = str(codex_home)
    env["CODEX_HOOKKIT_REVIEW_ACTIVE"] = "1"

    return subprocess.run(
        [
            "codex",
            "exec",
            "--json",
            "--cd",
            str(REPO_ROOT),
            "--model",
            "gpt-5.4-mini",
            prompt,
        ],
        cwd=REPO_ROOT,
        input="",
        text=True,
        capture_output=True,
        check=False,
        env=env,
        timeout=CODEX_EXEC_TIMEOUT_SECONDS,
    )


def run_guard_json_output(command: str) -> dict[str, object]:
    payload = {
        "cwd": str(REPO_ROOT),
        "hook_event_name": "PreToolUse",
        "model": "gpt-5",
        "permission_mode": "default",
        "session_id": "session",
        "tool_input": {"cmd": command},
        "tool_name": "shell",
        "tool_use_id": "tool-use",
        "transcript_path": None,
        "turn_id": "turn",
    }
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "codex_hookkit.cli",
            "guard",
            "--schema",
            "pre-tool-use",
            "--json-output",
        ],
        cwd=REPO_ROOT,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert isinstance(output, dict)
    return output


def json_events(output: str) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _toml_basic_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
