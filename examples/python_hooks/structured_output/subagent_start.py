#!/usr/bin/env python3
"""SubagentStart hook using structured JSON output."""

from __future__ import annotations

from codex_hookkit import HookPayload, SubagentStartOutput


def main() -> int:
    HookPayload.from_stdin(schema="subagent-start")
    SubagentStartOutput.minimal().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
