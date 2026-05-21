#!/usr/bin/env python3
"""PermissionRequest hook using exit status."""

from __future__ import annotations

from codex_hookkit import HookPayload, SecretPolicy, deny


def main() -> int:
    payload = HookPayload.from_stdin(schema="permission-request")
    decision = SecretPolicy.default().evaluate(payload)
    if decision.denied:
        return deny.stderr_exit(decision.reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
