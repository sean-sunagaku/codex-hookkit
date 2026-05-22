#!/usr/bin/env python3
"""PreCompact hook using typed input and exit status."""

from __future__ import annotations

from codex_hookkit import PreCompactInput


def main() -> int:
    PreCompactInput.from_stdin()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
