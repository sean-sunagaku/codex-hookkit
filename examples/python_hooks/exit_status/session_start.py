#!/usr/bin/env python3
"""SessionStart hook using exit status."""

from __future__ import annotations

from codex_hookkit import HookPayload


def main() -> int:
    payload = HookPayload.from_stdin(schema="session-start")
    _ = payload.raw["source"]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
