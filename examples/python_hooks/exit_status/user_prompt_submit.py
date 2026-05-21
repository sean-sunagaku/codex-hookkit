#!/usr/bin/env python3
"""UserPromptSubmit hook using exit status."""

from __future__ import annotations

from codex_hookkit import HookPayload


def main() -> int:
    payload = HookPayload.from_stdin(schema="user-prompt-submit")
    _ = payload.raw["prompt"]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
