#!/usr/bin/env python3
"""Stop hook using typed input and structured output."""

from __future__ import annotations

from codex_hookkit import StopInput, StopOutput


def main() -> int:
    StopInput.from_stdin()
    StopOutput.minimal().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
