#!/usr/bin/env python3
"""Minimal Codex hook example.

Codex sends one JSON payload to stdin. This script validates that payload,
checks a tiny default secret policy, and blocks by returning exit code 2 with
a stderr reason.
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
