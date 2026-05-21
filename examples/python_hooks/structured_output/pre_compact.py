#!/usr/bin/env python3
"""PreCompact hook using structured JSON output."""

from __future__ import annotations

from codex_hookkit import HookPayload, PreCompactOutput


def main() -> int:
    HookPayload.from_stdin(schema="pre-compact")
    PreCompactOutput.minimal().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
