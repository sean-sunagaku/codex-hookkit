#!/usr/bin/env python3
"""PostToolUse hook using typed input and structured output."""

from __future__ import annotations

from codex_hookkit import PostToolUseInput, PostToolUseOutput


def main() -> int:
    PostToolUseInput.from_stdin()
    PostToolUseOutput.minimal().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
