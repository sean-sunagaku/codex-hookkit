#!/usr/bin/env python3
"""UserPromptSubmit hook using structured JSON output."""

from __future__ import annotations

from codex_hookkit import HookPayload, UserPromptSubmitOutput


def main() -> int:
    HookPayload.from_stdin(schema="user-prompt-submit")
    UserPromptSubmitOutput.minimal().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
