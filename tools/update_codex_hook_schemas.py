#!/usr/bin/env python3
"""Update vendored Codex hook schemas from openai/codex."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = "openai/codex"
SCHEMA_DIR = "codex-rs/hooks/schema/generated"
DEST = Path("third_party/openai-codex-hook-schemas")


def main() -> int:
    commit = sys.argv[1] if len(sys.argv) > 1 else current_head()
    generated = DEST / "generated"
    generated.mkdir(parents=True, exist_ok=True)

    api = f"https://api.github.com/repos/{REPO}/contents/{SCHEMA_DIR}?ref={commit}"
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

    (DEST / "UPSTREAM.md").write_text(upstream_doc(commit, wrote), encoding="utf-8")
    print(f"updated {wrote} schema files from {REPO}@{commit}")
    return 0


def current_head() -> str:
    output = subprocess.check_output(
        ["git", "ls-remote", f"https://github.com/{REPO}.git", "HEAD"],
        text=True,
    )
    return output.split()[0]


def upstream_doc(commit: str, count: int) -> str:
    return f"""# openai/codex hook schemas

Vendored snapshot of generated Codex hook JSON schemas.

- Upstream: https://github.com/{REPO}
- Path: `{SCHEMA_DIR}`
- Commit: `{commit}`
- Schema files: {count}

Update with:

```sh
uv run python tools/update_codex_hook_schemas.py
```
"""


if __name__ == "__main__":
    raise SystemExit(main())
