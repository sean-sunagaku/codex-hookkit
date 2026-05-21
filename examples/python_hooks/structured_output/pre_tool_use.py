#!/usr/bin/env python3
"""PreToolUse hook using structured JSON output."""

from __future__ import annotations

from codex_hookkit import HookPayload, PreToolUseOutput, SecretPolicy


def main() -> int:
    payload = HookPayload.from_stdin(schema="pre-tool-use")
    decision = SecretPolicy.default().evaluate(payload)
    if decision.denied:
        PreToolUseOutput.deny(decision.reason).write()
    else:
        PreToolUseOutput.allow().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
