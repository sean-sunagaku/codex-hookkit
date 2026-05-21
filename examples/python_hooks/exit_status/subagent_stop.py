#!/usr/bin/env python3
"""SubagentStop hook using exit status."""

from __future__ import annotations

from codex_hookkit import HookPayload


def main() -> int:
    payload = HookPayload.from_stdin(schema="subagent-stop")
    _ = payload.raw["agent_transcript_path"]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
