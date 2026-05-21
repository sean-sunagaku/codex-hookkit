#!/usr/bin/env python3
"""Update vendored Codex hook schemas from openai/codex."""

from __future__ import annotations

import sys

from codex_hookkit.upstream import DEFAULT_DEST, download_schema_snapshot


def main() -> int:
    commit = sys.argv[1] if len(sys.argv) > 1 else None
    snapshot = download_schema_snapshot(DEFAULT_DEST, commit=commit)
    print(f"updated {snapshot.schema_count} schema files from {snapshot.repo}@{snapshot.commit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
