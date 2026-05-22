#!/usr/bin/env python3
"""PostCompact hook using typed input and exit status."""

from __future__ import annotations

from codex_hookkit import PostCompactInput


def main() -> int:
    PostCompactInput.from_stdin()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
