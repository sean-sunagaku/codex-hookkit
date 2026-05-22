#!/usr/bin/env python3
"""PermissionRequest hook using typed input and structured output."""

from __future__ import annotations

from codex_hookkit import PermissionRequestInput, PermissionRequestOutput, SecretPolicy


def main() -> int:
    payload = PermissionRequestInput.from_stdin()
    decision = SecretPolicy.default().evaluate(payload)
    if decision.denied:
        PermissionRequestOutput.deny(decision.reason).write()
    else:
        PermissionRequestOutput.allow().write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
