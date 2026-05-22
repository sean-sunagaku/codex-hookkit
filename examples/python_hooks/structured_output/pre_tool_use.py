#!/usr/bin/env python3
"""PreToolUse hook using typed input and structured output."""

from __future__ import annotations

from codex_hookkit import PreToolUseInput, PreToolUseOutput, SecretPolicy


def main() -> int:
    payload = PreToolUseInput.from_stdin()
    decision = SecretPolicy.default().evaluate(payload)
    if decision.denied:
        PreToolUseOutput.deny(decision.reason).write()
    else:
        PreToolUseOutput.allow().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
