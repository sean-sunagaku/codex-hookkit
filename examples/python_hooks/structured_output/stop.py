#!/usr/bin/env python3
"""Stop hook using structured JSON output."""

from __future__ import annotations

from codex_hookkit import HookPayload, StopOutput


def main() -> int:
    HookPayload.from_stdin(schema="stop")
    StopOutput.minimal().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
