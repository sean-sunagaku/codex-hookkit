#!/usr/bin/env python3
"""PermissionRequest hook using structured JSON output."""

from __future__ import annotations

from codex_hookkit import HookPayload, PermissionRequestOutput, SecretPolicy


def main() -> int:
    payload = HookPayload.from_stdin(schema="permission-request")
    decision = SecretPolicy.default().evaluate(payload)
    if decision.denied:
        PermissionRequestOutput.deny(decision.reason).write()
    else:
        PermissionRequestOutput.allow().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
