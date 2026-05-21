#!/usr/bin/env python3
"""SubagentStop hook using structured JSON output."""

from __future__ import annotations

from codex_hookkit import HookPayload, SubagentStopOutput


def main() -> int:
    HookPayload.from_stdin(schema="subagent-stop")
    SubagentStopOutput.minimal().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
