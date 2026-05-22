#!/usr/bin/env python3
"""Update vendored Codex hook schemas from openai/codex."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

REPO = "openai/codex"
SCHEMA_DIR = "codex-rs/hooks/schema/generated"
DEFAULT_DEST = Path("third_party/openai-codex-hook-schemas")


@dataclass(frozen=True)
class SchemaSnapshot:
    repo: str
    schema_dir: str
    commit: str
    destination: Path
    schema_count: int


def current_head(repo: str = REPO) -> str:
    output = subprocess.check_output(
        ["git", "ls-remote", f"https://github.com/{repo}.git", "HEAD"],
        text=True,
    )
    return output.split()[0]


def download_schema_snapshot(
    destination: str | Path = DEFAULT_DEST,
    *,
    commit: str | None = None,
    repo: str = REPO,
    schema_dir: str = SCHEMA_DIR,
) -> SchemaSnapshot:
    resolved_commit = commit or current_head(repo)
    dest = Path(destination)
    generated = dest / "generated"
    generated.mkdir(parents=True, exist_ok=True)

    api = f"https://api.github.com/repos/{repo}/contents/{schema_dir}?ref={resolved_commit}"
    with urllib.request.urlopen(api, timeout=30) as response:
        entries = json.load(response)

    wrote = 0
    for item in entries:
        name = item["name"]
        if not name.endswith(".schema.json"):
            continue
        with urllib.request.urlopen(item["download_url"], timeout=30) as response:
            (generated / name).write_bytes(response.read())
        wrote += 1

    snapshot = SchemaSnapshot(
        repo=repo,
        schema_dir=schema_dir,
        commit=resolved_commit,
        destination=dest,
        schema_count=wrote,
    )
    (dest / "UPSTREAM.md").write_text(upstream_doc(snapshot), encoding="utf-8")
    return snapshot


def upstream_doc(snapshot: SchemaSnapshot) -> str:
    return f"""# openai/codex hook schemas

Vendored snapshot of generated Codex hook JSON schemas.

- Upstream: https://github.com/{snapshot.repo}
- Path: `{snapshot.schema_dir}`
- Commit: `{snapshot.commit}`
- Schema files: {snapshot.schema_count}

Update with:

```sh
uv run python tools/update_codex_hook_schemas.py
```
"""


def main() -> int:
    commit = sys.argv[1] if len(sys.argv) > 1 else None
    snapshot = download_schema_snapshot(DEFAULT_DEST, commit=commit)
    print(f"updated {snapshot.schema_count} schema files from {snapshot.repo}@{snapshot.commit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
