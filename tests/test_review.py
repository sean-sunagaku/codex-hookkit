from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from codex_hookkit import HookPayload, request_review, run_review
from codex_hookkit.review import ACTIVE_ENV, marker_path


def init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


def post_tool_payload(cwd: Path) -> dict[str, object]:
    return {
        "cwd": str(cwd),
        "hook_event_name": "PostToolUse",
        "model": "gpt-5",
        "permission_mode": "default",
        "session_id": "session",
        "tool_input": {"cmd": "apply_patch"},
        "tool_name": "shell",
        "tool_response": {"exit_code": 0},
        "tool_use_id": "tool-use",
        "transcript_path": None,
        "turn_id": "turn",
    }


def stop_payload(cwd: Path) -> dict[str, object]:
    return {
        "cwd": str(cwd),
        "hook_event_name": "Stop",
        "last_assistant_message": "Done.",
        "model": "gpt-5",
        "permission_mode": "default",
        "session_id": "session",
        "stop_hook_active": False,
        "transcript_path": None,
        "turn_id": "turn",
    }


def test_request_review_marks_changed_code(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")

    payload = HookPayload.from_dict(post_tool_payload(tmp_path), schema="post-tool-use")
    marker = request_review(payload, state_dir=".state")

    assert marker is not None
    assert marker.files == ["app.py"]
    assert marker_path(tmp_path, ".state").exists()


def test_run_review_dry_run_prints_prompt(tmp_path: Path, capsys) -> None:
    init_repo(tmp_path)
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")
    request_review(HookPayload.from_dict(post_tool_payload(tmp_path), schema="post-tool-use"))

    result = run_review(
        HookPayload.from_dict(stop_payload(tmp_path), schema="stop"),
        dry_run=True,
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "Review the current uncommitted code changes" in captured.out
    assert "- app.py" in captured.out


def test_review_hooks_skip_when_nested(tmp_path: Path, monkeypatch) -> None:
    init_repo(tmp_path)
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")
    monkeypatch.setenv(ACTIVE_ENV, "1")

    marker = request_review(
        HookPayload.from_dict(post_tool_payload(tmp_path), schema="post-tool-use")
    )

    assert marker is None


def test_review_cli_dry_run(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")
    request_payload = json.dumps(post_tool_payload(tmp_path))
    stop_payload_text = json.dumps(stop_payload(tmp_path))

    request_result = subprocess.run(
        [sys.executable, "-m", "codex_hookkit.cli", "request-review"],
        input=request_payload,
        text=True,
        capture_output=True,
        check=False,
    )
    review_result = subprocess.run(
        [sys.executable, "-m", "codex_hookkit.cli", "run-review", "--dry-run"],
        input=stop_payload_text,
        text=True,
        capture_output=True,
        check=False,
    )

    assert request_result.returncode == 0
    assert review_result.returncode == 0
    assert "- app.py" in review_result.stdout
