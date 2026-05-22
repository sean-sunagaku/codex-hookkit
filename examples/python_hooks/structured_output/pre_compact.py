#!/usr/bin/env python3
"""PreCompact hook using typed input and structured output."""

from __future__ import annotations

from codex_hookkit import PreCompactInput, PreCompactOutput


def main() -> int:
    PreCompactInput.from_stdin()
    PreCompactOutput.minimal().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
