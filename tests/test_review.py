from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from codex_hookkit import PostToolUseInput, StopInput

ROOT = Path(__file__).resolve().parents[1]
HELPERS_PATH = ROOT / "examples" / "python_hooks" / "codex_review" / "review_helpers.py"
SPEC = importlib.util.spec_from_file_location("codex_review_helpers", HELPERS_PATH)
assert SPEC is not None and SPEC.loader is not None
review_helpers = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = review_helpers
SPEC.loader.exec_module(review_helpers)

ACTIVE_ENV = review_helpers.ACTIVE_ENV
discover_checks = review_helpers.discover_checks
marker_path = review_helpers.marker_path
request_review = review_helpers.request_review
run_checks = review_helpers.run_checks
run_review = review_helpers.run_review


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

    payload = PostToolUseInput.from_dict(post_tool_payload(tmp_path))
    marker = request_review(payload, state_dir=".state")

    assert marker is not None
    assert marker.files == ["app.py"]
    assert marker_path(tmp_path, ".state").exists()


def test_run_review_dry_run_prints_prompt(tmp_path: Path, capsys) -> None:
    init_repo(tmp_path)
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'sample'\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    request_review(PostToolUseInput.from_dict(post_tool_payload(tmp_path)))

    result = run_review(
        StopInput.from_dict(stop_payload(tmp_path)),
        dry_run=True,
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "Review the current uncommitted code changes" in captured.out
    assert "- app.py" in captured.out
    assert "Local verification checks to run" in captured.out
    assert "uv run ruff format --check ." in captured.out
    assert "uv run ruff check ." in captured.out
    assert "uv run pytest -q" in captured.out


def test_discover_checks_for_python_project(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'sample'\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()

    checks = discover_checks(tmp_path, ["app.py"])

    assert [check.name for check in checks] == ["fmt", "lint", "test"]
    assert [check.command for check in checks] == [
        ["uv", "run", "ruff", "format", "--check", "."],
        ["uv", "run", "ruff", "check", "."],
        ["uv", "run", "pytest", "-q"],
    ]


def test_run_checks_captures_failures(tmp_path: Path) -> None:
    results = run_checks(
        tmp_path,
        [
            review_helpers.Check(
                "test",
                [sys.executable, "-c", "import sys; print('broken'); sys.exit(3)"],
            )
        ],
    )

    assert len(results) == 1
    assert results[0].returncode == 3
    assert not results[0].ok
    assert "broken" in results[0].stdout


def test_review_hooks_skip_when_nested(tmp_path: Path, monkeypatch) -> None:
    init_repo(tmp_path)
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")
    monkeypatch.setenv(ACTIVE_ENV, "1")

    marker = request_review(PostToolUseInput.from_dict(post_tool_payload(tmp_path)))

    assert marker is None


def test_review_cli_dry_run(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")
    request_payload = json.dumps(post_tool_payload(tmp_path))
    stop_payload_text = json.dumps(stop_payload(tmp_path))

    request_result = subprocess.run(
        [sys.executable, "examples/python_hooks/codex_review/request_review.py"],
        input=request_payload,
        text=True,
        capture_output=True,
        check=False,
    )
    review_result = subprocess.run(
        [sys.executable, "examples/python_hooks/codex_review/run_review.py", "--dry-run"],
        input=stop_payload_text,
        text=True,
        capture_output=True,
        check=False,
    )

    assert request_result.returncode == 0
    assert review_result.returncode == 0
    assert "- app.py" in review_result.stdout


def test_run_review_can_skip_checks(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'sample'\n", encoding="utf-8")
    request_review(PostToolUseInput.from_dict(post_tool_payload(tmp_path)))
    prompt_path = tmp_path / "prompt.txt"
    fake_codex = tmp_path / "fake_codex"
    fake_codex.write_text(
        "#!/usr/bin/env python3\n"
        "import pathlib\n"
        "import sys\n"
        f"pathlib.Path({str(prompt_path)!r}).write_text(sys.argv[-1], encoding='utf-8')\n",
        encoding="utf-8",
    )
    fake_codex.chmod(0o755)

    result = run_review(
        StopInput.from_dict(stop_payload(tmp_path)),
        codex_bin=str(fake_codex),
        run_local_checks=False,
    )

    assert result == 0
    assert "Local verification checks were disabled." in prompt_path.read_text(encoding="utf-8")
