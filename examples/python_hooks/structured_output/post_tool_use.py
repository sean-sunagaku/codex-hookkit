#!/usr/bin/env python3
"""PostToolUse hook using structured JSON output."""

from __future__ import annotations

from codex_hookkit import HookPayload, PostToolUseOutput


def main() -> int:
    HookPayload.from_stdin(schema="post-tool-use")
    PostToolUseOutput.minimal().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
