#!/usr/bin/env python3
"""SubagentStart hook using typed input and structured output."""

from __future__ import annotations

from codex_hookkit import SubagentStartInput, SubagentStartOutput


def main() -> int:
    SubagentStartInput.from_stdin()
    SubagentStartOutput.minimal().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
