"""Command line entrypoints for codex-hookkit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from codex_hookkit.core.decisions import allow, deny, dump_json
from codex_hookkit.core.inputs import (
    PermissionRequestInput,
    PostCompactInput,
    PostToolUseInput,
    PreCompactInput,
    PreToolUseInput,
    SessionStartInput,
    StopInput,
    SubagentStartInput,
    SubagentStopInput,
    UserPromptSubmitInput,
)
from codex_hookkit.core.policy import SecretPolicy
from codex_hookkit.core.review import request_review, run_review
from codex_hookkit.core.scaffold import codex_review_hooks, project_skeleton, secret_guard_hook
from codex_hookkit.core.schemas import available_schemas
from codex_hookkit.core.trust import hook_trust_entries, write_hook_trusts
from codex_hookkit.core.upstream import DEFAULT_DEST, download_schema_snapshot

INPUT_MODELS = {
    "permission-request": PermissionRequestInput,
    "post-compact": PostCompactInput,
    "post-tool-use": PostToolUseInput,
    "pre-compact": PreCompactInput,
    "pre-tool-use": PreToolUseInput,
    "session-start": SessionStartInput,
    "stop": StopInput,
    "subagent-start": SubagentStartInput,
    "subagent-stop": SubagentStopInput,
    "user-prompt-submit": UserPromptSubmitInput,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-hookkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    guard = subparsers.add_parser("guard", help="read a Codex hook payload from stdin and guard it")
    guard.add_argument("--schema", default="pre-tool-use", choices=available_schemas())
    guard.add_argument(
        "--json-output",
        action="store_true",
        help="emit Codex hook JSON output instead of using exit code 2 + stderr for denials",
    )

    schemas = subparsers.add_parser("schemas", help="list vendored hook schemas")
    schemas.add_argument(
        "--direction",
        choices=("input", "output", "both"),
        default="input",
        help="schema direction to display in the file-style names",
    )

    scaffold = subparsers.add_parser("scaffold", help="write a minimal hook skeleton")
    scaffold.add_argument(
        "--kind",
        choices=("secret-guard", "codex-review-hooks"),
        default="secret-guard",
        help="skeleton kind to write",
    )
    scaffold.add_argument("--schema", default="pre-tool-use", choices=available_schemas())
    scaffold.add_argument(
        "--output",
        "-o",
        type=Path,
        help="write the skeleton to this file instead of stdout",
    )

    init = subparsers.add_parser("init", help="write a minimal project hook skeleton")
    init.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("."),
        help="project directory to initialize",
    )
    init.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing generated skeleton files",
    )
    init.add_argument(
        "--with-review",
        action="store_true",
        help="include the optional PostToolUse/Stop Codex review hook flow",
    )

    download = subparsers.add_parser(
        "download-schemas", help="download upstream generated hook schemas"
    )
    download.add_argument("--commit", help="upstream openai/codex commit; defaults to HEAD")
    download.add_argument(
        "--dest",
        type=Path,
        default=DEFAULT_DEST,
        help="destination directory for the schema snapshot",
    )

    trust = subparsers.add_parser(
        "trust-hooks", help="write Codex hook trusted hashes into config.toml"
    )
    trust.add_argument(
        "--hooks-path",
        type=Path,
        default=Path(".codex/hooks.json"),
        help="hooks.json file to trust",
    )
    trust.add_argument(
        "--config",
        type=Path,
        default=Path.home() / ".codex" / "config.toml",
        help="Codex config.toml to update",
    )
    trust.add_argument(
        "--dry-run",
        action="store_true",
        help="print entries without writing config.toml",
    )

    request = subparsers.add_parser(
        "request-review", help="mark that changed code should receive a Stop-hook Codex review"
    )
    request.add_argument("--state-dir", default=".codex-hookkit")

    review = subparsers.add_parser("run-review", help="run a pending Stop-hook Codex review")
    review.add_argument("--state-dir", default=".codex-hookkit")
    review.add_argument("--codex-bin", default="codex")
    review.add_argument("--timeout", type=int, default=240)
    review.add_argument("--dry-run", action="store_true", help="print the review prompt only")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "schemas":
        for name in available_schemas():
            if args.direction == "both":
                print(f"{name}.command.input.schema.json")
                print(f"{name}.command.output.schema.json")
            elif args.direction == "output":
                print(f"{name}.command.output.schema.json")
            else:
                print(name)
        return 0

    if args.command == "scaffold":
        if args.kind == "codex-review-hooks":
            content = codex_review_hooks()
        else:
            content = secret_guard_hook(schema=args.schema)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content, encoding="utf-8")
        else:
            print(content, end="")
        return 0

    if args.command == "init":
        try:
            written = project_skeleton(
                args.output_dir,
                force=args.force,
                include_review=args.with_review,
            )
        except Exception as exc:
            return deny.stderr_exit(f"Failed to write Codex hook skeleton: {exc}")
        for path in written:
            print(path)
        return 0

    if args.command == "download-schemas":
        snapshot = download_schema_snapshot(args.dest, commit=args.commit)
        print(
            f"downloaded {snapshot.schema_count} schema files from "
            f"{snapshot.repo}@{snapshot.commit} to {snapshot.destination}"
        )
        return 0

    if args.command == "trust-hooks":
        try:
            if args.dry_run:
                entries = hook_trust_entries(args.hooks_path)
                for entry in entries:
                    print(f"{entry.key} {entry.current_hash}")
                return 0
            result = write_hook_trusts(args.hooks_path, config_path=args.config)
        except Exception as exc:
            return deny.stderr_exit(f"Failed to write Codex hook trust state: {exc}")
        print(f"wrote {result.count} hook trust entries to {result.config_path}")
        return 0

    if args.command == "request-review":
        try:
            payload = read_input("post-tool-use")
        except Exception as exc:
            return deny.stderr_exit(f"Invalid Codex hook payload: {exc}")
        request_review(payload, state_dir=args.state_dir)
        return 0

    if args.command == "run-review":
        try:
            payload = read_input("stop")
        except Exception as exc:
            return deny.stderr_exit(f"Invalid Codex hook payload: {exc}")
        return run_review(
            payload,
            state_dir=args.state_dir,
            codex_bin=args.codex_bin,
            dry_run=args.dry_run,
            timeout=args.timeout,
        )

    if args.command == "guard":
        try:
            payload = read_input(args.schema)
        except Exception as exc:
            return deny.stderr_exit(f"Invalid Codex hook payload: {exc}")

        decision = SecretPolicy.default().evaluate(payload)
        if decision.denied:
            if args.json_output:
                if args.schema == "permission-request":
                    dump_json(deny.permission_request_json(decision.reason))
                else:
                    dump_json(deny.pre_tool_use_json(decision.reason))
                return 0
            return deny.stderr_exit(decision.reason)

        if args.json_output:
            if args.schema == "permission-request":
                dump_json(allow.permission_request_json())
            else:
                dump_json(allow.pre_tool_use_json())
        return 0

    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


def read_input(schema: str) -> object:
    return INPUT_MODELS[schema].from_stdin()


if __name__ == "__main__":
    raise SystemExit(main())
