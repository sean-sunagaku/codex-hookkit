from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from codex_hookkit import validate

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
PYTHON_HOOKS = EXAMPLES / "python_hooks"


HOOK_EXAMPLES = {
    "permission_request": "permission_request_payload.json",
    "post_compact": "post_compact_payload.json",
    "post_tool_use": "post_tool_use_payload.json",
    "pre_compact": "pre_compact_payload.json",
    "pre_tool_use": "pre_tool_use_payload.json",
    "session_start": "session_start_payload.json",
    "stop": "stop_payload.json",
    "subagent_start": "subagent_start_payload.json",
    "subagent_stop": "subagent_stop_payload.json",
    "user_prompt_submit": "user_prompt_submit_payload.json",
}


SCHEMA_NAMES = {
    "permission_request": "permission-request",
    "post_compact": "post-compact",
    "post_tool_use": "post-tool-use",
    "pre_compact": "pre-compact",
    "pre_tool_use": "pre-tool-use",
    "session_start": "session-start",
    "stop": "stop",
    "subagent_start": "subagent-start",
    "subagent_stop": "subagent-stop",
    "user_prompt_submit": "user-prompt-submit",
}


def run_hook(pattern: str, name: str, payload_name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PYTHON_HOOKS / pattern / f"{name}.py")],
        input=(EXAMPLES / payload_name).read_text(encoding="utf-8"),
        text=True,
        capture_output=True,
        check=False,
    )


def test_exit_status_python_hook_examples_run_matching_payloads() -> None:
    for hook_name, payload_name in HOOK_EXAMPLES.items():
        result = run_hook("exit_status", hook_name, payload_name)
        if hook_name == "permission_request":
            assert result.returncode == 2
            assert "Blocked direct secret file access" in result.stderr
        else:
            assert result.returncode == 0, (hook_name, result.stderr)


def test_pre_tool_use_python_hook_blocks_secret_access() -> None:
    payload = (EXAMPLES / "pre_tool_use_payload.json").read_text(encoding="utf-8")
    payload = payload.replace('"cmd": "pwd"', '"cmd": "cat .env"')
    result = subprocess.run(
        [sys.executable, str(PYTHON_HOOKS / "exit_status" / "pre_tool_use.py")],
        input=payload,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "Blocked direct secret file access" in result.stderr


def test_structured_output_python_hook_examples_emit_valid_json() -> None:
    for hook_name, payload_name in HOOK_EXAMPLES.items():
        result = run_hook("structured_output", hook_name, payload_name)
        assert result.returncode == 0, (hook_name, result.stderr)
        validate(json_loads(result.stdout), SCHEMA_NAMES[hook_name], direction="output")


def json_loads(text: str) -> object:
    import json

    return json.loads(text)
