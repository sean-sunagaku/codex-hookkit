from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from fixtures import HOOK_SCHEMA_NAMES, hook_payload

from codex_hookkit import validate

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
PYTHON_HOOKS = EXAMPLES / "python_hooks"


def secret_command() -> str:
    return "cat " + chr(46) + "env"


def run_hook(pattern: str, name: str, *, command: str = "pwd") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PYTHON_HOOKS / pattern / f"{name}.py")],
        input=json.dumps(hook_payload(name, command=command)),
        text=True,
        capture_output=True,
        check=False,
    )


def test_exit_status_python_hook_examples_run_matching_payloads() -> None:
    for hook_name in HOOK_SCHEMA_NAMES:
        command = secret_command() if hook_name == "permission_request" else "pwd"
        result = run_hook("exit_status", hook_name, command=command)
        if hook_name == "permission_request":
            assert result.returncode == 2
            assert "Blocked direct secret file access" in result.stderr
        else:
            assert result.returncode == 0, (hook_name, result.stderr)


def test_pre_tool_use_python_hook_blocks_secret_access() -> None:
    result = run_hook("exit_status", "pre_tool_use", command=secret_command())
    assert result.returncode == 2
    assert "Blocked direct secret file access" in result.stderr


def test_structured_output_python_hook_examples_emit_valid_json() -> None:
    for hook_name, schema_name in HOOK_SCHEMA_NAMES.items():
        result = run_hook("structured_output", hook_name)
        assert result.returncode == 0, (hook_name, result.stderr)
        validate(json.loads(result.stdout), schema_name, direction="output")
