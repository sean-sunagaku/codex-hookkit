from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path

from codex_hookkit import validate

ROOT = Path(__file__).resolve().parents[1]


def secret_command() -> str:
    return "cat " + chr(46) + "env"


def payload(event: str, *, cwd: Path, command: str = "pwd") -> dict[str, object]:
    base = {
        "cwd": str(cwd),
        "model": "gpt-5",
        "permission_mode": "default",
        "session_id": "session",
        "transcript_path": None,
        "turn_id": "turn",
    }
    if event == "PreToolUse":
        return {
            **base,
            "hook_event_name": "PreToolUse",
            "tool_input": {"cmd": command},
            "tool_name": "shell",
            "tool_use_id": "tool-use",
        }
    if event == "PermissionRequest":
        return {
            **base,
            "hook_event_name": "PermissionRequest",
            "tool_input": {"cmd": command},
            "tool_name": "shell",
        }
    if event == "PostToolUse":
        return {
            **base,
            "hook_event_name": "PostToolUse",
            "tool_input": {"cmd": command},
            "tool_name": "shell",
            "tool_response": {"exit_code": 0, "stdout": "ok\n"},
            "tool_use_id": "tool-use",
        }
    if event == "Stop":
        return {
            **base,
            "hook_event_name": "Stop",
            "last_assistant_message": "Done.",
            "stop_hook_active": False,
        }
    raise AssertionError(event)


def run_configured_hook(command: str, data: dict[str, object]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        shlex.split(command),
        input=json.dumps(data),
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
        timeout=30,
    )


def with_dry_run(command: str) -> str:
    if "run_review.py'" in command:
        return command.replace("run_review.py'", "run_review.py --dry-run'")
    return command + " --dry-run"


def init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


def command_for(config: dict[str, object], event: str) -> str:
    hooks = config["hooks"]
    assert isinstance(hooks, dict)
    entries = hooks[event]
    assert isinstance(entries, list)
    hook_list = entries[0]["hooks"]
    assert isinstance(hook_list, list)
    return hook_list[0]["command"]


def test_minimal_secret_guard_example_runs() -> None:
    command = "uv run python examples/minimal_secret_guard.py"

    allow_result = run_configured_hook(command, payload("PreToolUse", cwd=ROOT))
    assert allow_result.returncode == 0, allow_result.stderr

    deny_result = run_configured_hook(
        command, payload("PreToolUse", cwd=ROOT, command=secret_command())
    )
    assert deny_result.returncode == 2
    assert "Blocked direct secret file access" in deny_result.stderr


def test_examples_hooks_json_commands_run(tmp_path: Path) -> None:
    (tmp_path / ".codex").mkdir()
    (tmp_path / ".codex" / "hooks.json").write_text(
        (ROOT / "examples" / "hooks.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    init_repo(tmp_path)
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")

    config = json.loads((tmp_path / ".codex" / "hooks.json").read_text(encoding="utf-8"))

    pre_allow = run_configured_hook(
        command_for(config, "PreToolUse"), payload("PreToolUse", cwd=tmp_path)
    )
    assert pre_allow.returncode == 0, pre_allow.stderr
    assert pre_allow.stdout == ""

    pre_deny = run_configured_hook(
        command_for(config, "PreToolUse"),
        payload("PreToolUse", cwd=tmp_path, command=secret_command()),
    )
    assert pre_deny.returncode == 2
    assert "Blocked direct secret file access" in pre_deny.stderr

    permission = run_configured_hook(
        command_for(config, "PermissionRequest"),
        payload("PermissionRequest", cwd=tmp_path, command=secret_command()),
    )
    assert permission.returncode == 0, permission.stderr
    permission_json = json.loads(permission.stdout)
    validate(permission_json, "permission-request", direction="output")
    assert permission_json["hookSpecificOutput"]["decision"]["behavior"] == "deny"

    post = run_configured_hook(
        command_for(config, "PostToolUse"), payload("PostToolUse", cwd=tmp_path)
    )
    assert post.returncode == 0, post.stderr
    marker = tmp_path / ".codex-hookkit" / "pending-review.json"
    assert marker.exists()
    assert "app.py" in json.loads(marker.read_text(encoding="utf-8"))["files"]

    clean = tmp_path / "clean"
    clean.mkdir()
    init_repo(clean)
    stop_no_marker = run_configured_hook(command_for(config, "Stop"), payload("Stop", cwd=clean))
    assert stop_no_marker.returncode == 0, stop_no_marker.stderr

    dry_run = run_configured_hook(
        with_dry_run(command_for(config, "Stop")), payload("Stop", cwd=tmp_path)
    )
    assert dry_run.returncode == 0, dry_run.stderr
    assert "Review the current uncommitted code changes" in dry_run.stdout
    assert "app.py" in dry_run.stdout


def test_project_hooks_json_commands_run(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")

    config = json.loads((ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8"))

    pre_allow = run_configured_hook(
        command_for(config, "PreToolUse"), payload("PreToolUse", cwd=tmp_path)
    )
    assert pre_allow.returncode == 0, pre_allow.stderr
    assert pre_allow.stdout == ""

    pre_deny = run_configured_hook(
        command_for(config, "PreToolUse"),
        payload("PreToolUse", cwd=tmp_path, command=secret_command()),
    )
    assert pre_deny.returncode == 2
    assert "Blocked direct secret file access" in pre_deny.stderr

    permission = run_configured_hook(
        command_for(config, "PermissionRequest"),
        payload("PermissionRequest", cwd=tmp_path, command=secret_command()),
    )
    assert permission.returncode == 2
    assert "Blocked direct secret file access" in permission.stderr

    post = run_configured_hook(
        command_for(config, "PostToolUse"), payload("PostToolUse", cwd=tmp_path)
    )
    assert post.returncode == 0, post.stderr
    marker = tmp_path / ".codex-hookkit" / "pending-review.json"
    assert marker.exists()
    assert "app.py" in json.loads(marker.read_text(encoding="utf-8"))["files"]

    dry_run = run_configured_hook(
        with_dry_run(command_for(config, "Stop")), payload("Stop", cwd=tmp_path)
    )
    assert dry_run.returncode == 0, dry_run.stderr
    assert "Review the current uncommitted code changes" in dry_run.stdout
    assert "app.py" in dry_run.stdout


def test_codex_review_hooks_json_commands_run(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")

    config = json.loads((ROOT / "examples" / "codex_review_hooks.json").read_text(encoding="utf-8"))

    post = run_configured_hook(
        command_for(config, "PostToolUse"), payload("PostToolUse", cwd=tmp_path)
    )
    assert post.returncode == 0, post.stderr
    marker = tmp_path / ".codex-hookkit" / "pending-review.json"
    assert marker.exists()
    assert "app.py" in json.loads(marker.read_text(encoding="utf-8"))["files"]

    dry_run = run_configured_hook(
        with_dry_run(command_for(config, "Stop")), payload("Stop", cwd=tmp_path)
    )
    assert dry_run.returncode == 0, dry_run.stderr
    assert "Review the current uncommitted code changes" in dry_run.stdout
    assert "app.py" in dry_run.stdout
