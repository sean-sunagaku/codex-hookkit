#!/usr/bin/env python3
"""PostCompact hook using typed input and structured output."""

from __future__ import annotations

from codex_hookkit import PostCompactInput, PostCompactOutput


def main() -> int:
    PostCompactInput.from_stdin()
    PostCompactOutput.minimal().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
