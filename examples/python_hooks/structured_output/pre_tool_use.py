#!/usr/bin/env python3
"""PreToolUse hook using structured JSON output."""

from __future__ import annotations

from codex_hookkit import HookPayload, SecretPolicy, allow, deny, dump_json


def main() -> int:
    payload = HookPayload.from_stdin(schema="pre-tool-use")
    decision = SecretPolicy.default().evaluate(payload)
    if decision.denied:
        dump_json(deny.pre_tool_use_json(decision.reason))
    else:
        dump_json(allow.pre_tool_use_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
