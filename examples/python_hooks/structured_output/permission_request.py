#!/usr/bin/env python3
"""PermissionRequest hook using structured JSON output."""

from __future__ import annotations

from codex_hookkit import HookPayload, SecretPolicy, allow, deny, dump_json


def main() -> int:
    payload = HookPayload.from_stdin(schema="permission-request")
    decision = SecretPolicy.default().evaluate(payload)
    if decision.denied:
        dump_json(deny.permission_request_json(decision.reason))
    else:
        dump_json(allow.permission_request_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
