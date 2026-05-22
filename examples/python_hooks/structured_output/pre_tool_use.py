#!/usr/bin/env python3
"""PreToolUse hook using typed input and structured output."""

from __future__ import annotations

import sys
from pathlib import Path

from codex_hookkit import PreToolUseInput, PreToolUseOutput

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from secret_guard_policy import SecretGuardPolicy  # noqa: E402


def main() -> int:
    payload = PreToolUseInput.from_stdin()
    decision = SecretGuardPolicy.default().evaluate(payload)
    if decision.denied:
        PreToolUseOutput.deny(decision.reason).write()
    else:
        PreToolUseOutput.allow().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
