#!/usr/bin/env python3
"""SessionStart hook using structured JSON output."""

from __future__ import annotations

from codex_hookkit import HookPayload, SessionStartOutput


def main() -> int:
    HookPayload.from_stdin(schema="session-start")
    SessionStartOutput.minimal().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
