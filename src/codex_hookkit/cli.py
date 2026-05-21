"""Command line entrypoints for codex-hookkit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .decisions import allow, deny, dump_json
from .payload import HookPayload
from .policy import SecretPolicy
from .scaffold import secret_guard_hook
from .schemas import available_schemas
from .upstream import DEFAULT_DEST, download_schema_snapshot


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
    guard.add_argument(
        "--no-validate",
        action="store_true",
        help="skip input validation against the vendored upstream schema",
    )

    schemas = subparsers.add_parser("schemas", help="list vendored hook schemas")
    schemas.add_argument(
        "--direction",
        choices=("input", "output", "both"),
        default="input",
        help="schema direction to display in the file-style names",
    )

    scaffold = subparsers.add_parser("scaffold", help="write a minimal import-first hook script")
    scaffold.add_argument("--schema", default="pre-tool-use", choices=available_schemas())
    scaffold.add_argument(
        "--output",
        "-o",
        type=Path,
        help="write the skeleton to this file instead of stdout",
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
        content = secret_guard_hook(schema=args.schema)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content, encoding="utf-8")
        else:
            print(content, end="")
        return 0

    if args.command == "download-schemas":
        snapshot = download_schema_snapshot(args.dest, commit=args.commit)
        print(
            f"downloaded {snapshot.schema_count} schema files from "
            f"{snapshot.repo}@{snapshot.commit} to {snapshot.destination}"
        )
        return 0

    if args.command == "guard":
        try:
            payload = HookPayload.from_stdin(
                schema=args.schema, validate_schema=not args.no_validate
            )
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


if __name__ == "__main__":
    raise SystemExit(main())
