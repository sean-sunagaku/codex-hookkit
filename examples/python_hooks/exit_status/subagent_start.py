#!/usr/bin/env python3
"""SubagentStart hook using typed input and exit status."""

from __future__ import annotations

from codex_hookkit import SubagentStartInput


def main() -> int:
    SubagentStartInput.from_stdin()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
