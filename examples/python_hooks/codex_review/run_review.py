#!/usr/bin/env python3
"""Stop example that runs one nested Codex review when a marker exists."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from codex_hookkit import StopInput, deny

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_helpers import run_review  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", default=".codex-hookkit")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="skip local fmt/lint/test checks before launching the nested review",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    try:
        payload = StopInput.from_stdin()
    except Exception as exc:
        return deny.stderr_exit(f"Invalid Codex hook payload: {exc}")

    return run_review(
        payload,
        state_dir=args.state_dir,
        codex_bin=args.codex_bin,
        timeout=args.timeout,
        dry_run=args.dry_run,
        run_local_checks=not args.skip_checks,
    )


if __name__ == "__main__":
    raise SystemExit(main())
