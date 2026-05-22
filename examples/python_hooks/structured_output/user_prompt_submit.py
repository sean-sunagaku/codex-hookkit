#!/usr/bin/env python3
"""UserPromptSubmit hook using typed input and structured output."""

from __future__ import annotations

from codex_hookkit import UserPromptSubmitInput, UserPromptSubmitOutput


def main() -> int:
    UserPromptSubmitInput.from_stdin()
    UserPromptSubmitOutput.minimal().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
