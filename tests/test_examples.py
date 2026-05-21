from __future__ import annotations

import json
from pathlib import Path

from codex_hookkit import validate


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def load_example(name: str) -> object:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def test_pre_tool_use_examples_match_upstream_schema() -> None:
    validate(load_example("pre_tool_use_payload.json"), "pre-tool-use", direction="input")
    validate(load_example("pre_tool_use_allow.json"), "pre-tool-use", direction="output")
    validate(load_example("pre_tool_use_deny.json"), "pre-tool-use", direction="output")


def test_permission_request_examples_match_upstream_schema() -> None:
    validate(load_example("permission_request_payload.json"), "permission-request", direction="input")
    validate(load_example("permission_request_allow.json"), "permission-request", direction="output")
    validate(load_example("permission_request_deny.json"), "permission-request", direction="output")
