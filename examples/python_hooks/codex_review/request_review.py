#!/usr/bin/env python3
"""PostToolUse example that marks changed code for a later Codex review."""

from __future__ import annotations

import sys
from pathlib import Path

from codex_hookkit import PostToolUseInput, deny

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_helpers import request_review  # noqa: E402


def main() -> int:
    try:
        payload = PostToolUseInput.from_stdin()
    except Exception as exc:
        return deny.stderr_exit(f"Invalid Codex hook payload: {exc}")

    request_review(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
