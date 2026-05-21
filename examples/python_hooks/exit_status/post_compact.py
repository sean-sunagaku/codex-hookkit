#!/usr/bin/env python3
"""PostCompact hook using exit status."""

from __future__ import annotations

from codex_hookkit import HookPayload


def main() -> int:
    payload = HookPayload.from_stdin(schema="post-compact")
    _ = payload.raw["trigger"]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
