#!/usr/bin/env python3
"""PreToolUse hook using exit status.

Return 0 to allow the tool call. Return 2 and write a reason to stderr to
block it.
"""

from __future__ import annotations

from codex_hookkit import HookPayload, SecretPolicy, deny


def main() -> int:
    payload = HookPayload.from_stdin(schema="pre-tool-use")
    decision = SecretPolicy.default().evaluate(payload)
    if decision.denied:
        return deny.stderr_exit(decision.reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
