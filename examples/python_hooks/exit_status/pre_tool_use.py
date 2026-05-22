#!/usr/bin/env python3
"""PreToolUse hook using typed input and exit status."""

from __future__ import annotations

import sys
from pathlib import Path

from codex_hookkit import PreToolUseInput, deny

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from secret_guard_policy import SecretGuardPolicy  # noqa: E402


def main() -> int:
    payload = PreToolUseInput.from_stdin()
    decision = SecretGuardPolicy.default().evaluate(payload)
    if decision.denied:
        return deny.stderr_exit(decision.reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
