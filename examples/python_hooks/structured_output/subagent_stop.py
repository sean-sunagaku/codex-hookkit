#!/usr/bin/env python3
"""SubagentStop hook using typed input and structured output."""

from __future__ import annotations

from codex_hookkit import SubagentStopInput, SubagentStopOutput


def main() -> int:
    SubagentStopInput.from_stdin()
    SubagentStopOutput.minimal().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
