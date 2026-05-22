#!/usr/bin/env python3
"""PermissionRequest hook using typed input and exit status."""

from __future__ import annotations

from codex_hookkit import PermissionRequestInput, SecretPolicy, deny


def main() -> int:
    payload = PermissionRequestInput.from_stdin()
    decision = SecretPolicy.default().evaluate(payload)
    if decision.denied:
        return deny.stderr_exit(decision.reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
