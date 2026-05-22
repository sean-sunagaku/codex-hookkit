from __future__ import annotations

from fixtures import HOOK_SCHEMA_NAMES, hook_payload

from codex_hookkit import validate


def test_hook_payload_fixtures_match_upstream_input_schemas() -> None:
    for hook_name, schema_name in HOOK_SCHEMA_NAMES.items():
        validate(hook_payload(hook_name), schema_name, direction="input")
