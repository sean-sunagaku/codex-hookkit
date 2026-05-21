#!/usr/bin/env python3
"""PostCompact hook using structured JSON output."""

from __future__ import annotations

from codex_hookkit import HookPayload, PostCompactOutput


def main() -> int:
    HookPayload.from_stdin(schema="post-compact")
    PostCompactOutput.minimal().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
