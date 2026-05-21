"""Command line entrypoints for codex-hookkit."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from .decisions import allow, deny, dump_json
from .payload import HookPayload
from .policy import SecretPolicy
from .schemas import available_schemas


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

    subparsers.add_parser("schemas", help="list vendored hook schemas")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "schemas":
        for name in available_schemas():
            print(name)
        return 0

    if args.command == "guard":
        try:
            payload = HookPayload.from_stdin(schema=args.schema, validate_schema=not args.no_validate)
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
