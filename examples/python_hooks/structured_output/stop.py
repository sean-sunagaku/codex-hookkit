#!/usr/bin/env python3
"""Stop hook using structured JSON output."""

from __future__ import annotations

from codex_hookkit import HookPayload, dump_json, validate


def main() -> int:
    HookPayload.from_stdin(schema="stop")
    output = {"continue": True}
    validate(output, "stop", direction="output")
    dump_json(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
