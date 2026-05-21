from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from pydantic import ValidationError

from codex_hookkit import (
    PermissionRequestOutput,
    PostCompactOutput,
    PostToolUseOutput,
    PreCompactOutput,
    PreToolUseOutput,
    SessionStartOutput,
    StopOutput,
    SubagentStartOutput,
    SubagentStopOutput,
    UserPromptSubmitOutput,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]


def load_generator_module() -> object:
    path = ROOT / "tools" / "generate_pydantic_outputs.py"
    spec = importlib.util.spec_from_file_location("generate_pydantic_outputs", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_outputs_are_in_sync() -> None:
    generator = load_generator_module()
    rendered = generator.render_module(sorted(generator.EVENT_NAMES))
    current = (ROOT / "src" / "codex_hookkit" / "outputs.py").read_text(encoding="utf-8")
    assert current == rendered


def test_output_helpers_match_upstream_schemas() -> None:
    outputs = [
        (PermissionRequestOutput.allow(), "permission-request"),
        (PermissionRequestOutput.deny("blocked"), "permission-request"),
        (PostCompactOutput.minimal(), "post-compact"),
        (PostToolUseOutput.minimal(), "post-tool-use"),
        (PreCompactOutput.minimal(), "pre-compact"),
        (PreToolUseOutput.allow(), "pre-tool-use"),
        (PreToolUseOutput.deny("blocked"), "pre-tool-use"),
        (SessionStartOutput.minimal(), "session-start"),
        (StopOutput.minimal(), "stop"),
        (SubagentStartOutput.minimal(), "subagent-start"),
        (SubagentStopOutput.minimal(), "subagent-stop"),
        (UserPromptSubmitOutput.minimal(), "user-prompt-submit"),
    ]

    for output, schema_name in outputs:
        validate(output.to_dict(), schema_name, direction="output")


def test_output_models_forbid_extra_fields() -> None:
    with pytest.raises(ValidationError):
        PreToolUseOutput(unknown_field=True)
