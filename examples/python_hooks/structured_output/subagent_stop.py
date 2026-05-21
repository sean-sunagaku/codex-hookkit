#!/usr/bin/env python3
"""SubagentStop hook using structured JSON output."""

from __future__ import annotations

from codex_hookkit import HookPayload, dump_json, validate


def main() -> int:
    HookPayload.from_stdin(schema="subagent-stop")
    output = {"continue": True}
    validate(output, "subagent-stop", direction="output")
    dump_json(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
