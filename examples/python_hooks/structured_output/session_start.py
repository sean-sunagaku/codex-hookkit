#!/usr/bin/env python3
"""SessionStart hook using typed input and structured output."""

from __future__ import annotations

from codex_hookkit import SessionStartInput, SessionStartOutput


def main() -> int:
    SessionStartInput.from_stdin()
    SessionStartOutput.minimal().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
