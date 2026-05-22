#!/usr/bin/env python3
"""Check that generated Pydantic models are in sync with the generator."""

from __future__ import annotations

import difflib
import sys
from pathlib import Path

import generate_pydantic_models

GENERATED_FILES = (
    Path("src/codex_hookkit/core/inputs.py"),
    Path("src/codex_hookkit/core/outputs.py"),
)


def main() -> int:
    before = {path: path.read_text(encoding="utf-8") for path in GENERATED_FILES}
    generate_pydantic_models.main()
    after = {path: path.read_text(encoding="utf-8") for path in GENERATED_FILES}

    drifted = [path for path in GENERATED_FILES if before[path] != after[path]]
    if not drifted:
        return 0

    for path in drifted:
        diff = difflib.unified_diff(
            before[path].splitlines(keepends=True),
            after[path].splitlines(keepends=True),
            fromfile=f"{path} (before)",
            tofile=f"{path} (generated)",
        )
        sys.stderr.writelines(diff)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
