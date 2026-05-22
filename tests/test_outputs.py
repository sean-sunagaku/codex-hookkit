from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from fixtures import HOOK_SCHEMA_NAMES, hook_payload
from pydantic import ValidationError

from codex_hookkit import (
    PermissionRequestInput,
    PermissionRequestOutput,
    PostCompactInput,
    PostCompactOutput,
    PostToolUseInput,
    PostToolUseOutput,
    PreCompactInput,
    PreCompactOutput,
    PreToolUseInput,
    PreToolUseOutput,
    SessionStartInput,
    SessionStartOutput,
    StopInput,
    StopOutput,
    StructuredInput,
    SubagentStartInput,
    SubagentStartOutput,
    SubagentStopInput,
    SubagentStopOutput,
    UserPromptSubmitInput,
    UserPromptSubmitOutput,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]


def load_generator_module() -> object:
    path = ROOT / "tools" / "generate_pydantic_models.py"
    spec = importlib.util.spec_from_file_location("generate_pydantic_models", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_inputs_and_outputs_are_in_sync() -> None:
    generator = load_generator_module()
    for direction, target in {
        "input": ROOT / "src" / "codex_hookkit" / "inputs.py",
        "output": ROOT / "src" / "codex_hookkit" / "outputs.py",
    }.items():
        rendered = generator.render_module(sorted(generator.EVENT_NAMES), direction=direction)
        current = target.read_text(encoding="utf-8")
        assert current == rendered


def test_input_models_match_upstream_schemas() -> None:
    input_classes = {
        "permission_request": PermissionRequestInput,
        "post_compact": PostCompactInput,
        "post_tool_use": PostToolUseInput,
        "pre_compact": PreCompactInput,
        "pre_tool_use": PreToolUseInput,
        "session_start": SessionStartInput,
        "stop": StopInput,
        "subagent_start": SubagentStartInput,
        "subagent_stop": SubagentStopInput,
        "user_prompt_submit": UserPromptSubmitInput,
    }

    for hook_name, input_class in input_classes.items():
        payload = input_class.from_dict(hook_payload(hook_name))
        assert isinstance(payload, StructuredInput)
        validate(payload.to_dict(), HOOK_SCHEMA_NAMES[hook_name], direction="input")


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
