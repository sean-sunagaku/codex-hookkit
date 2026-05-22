"""Command line entrypoints for codex-hookkit."""

from __future__ import annotations

import argparse
import re
import shlex
import sys
from pathlib import Path, PurePosixPath

from codex_hookkit.cli._scaffold import project_skeleton, secret_guard_hook
from codex_hookkit.core.decisions import Decision, allow, deny, dump_json
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
from codex_hookkit.core.schemas import available_schemas

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
        choices=("secret-guard",),
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

    if args.command == "init":
        try:
            written = project_skeleton(
                args.output_dir,
                force=args.force,
            )
        except Exception as exc:
            return deny.stderr_exit(f"Failed to write Codex hook skeleton: {exc}")
        for path in written:
            print(path)
        return 0

    if args.command == "guard":
        try:
            payload = read_input(args.schema)
        except Exception as exc:
            return deny.stderr_exit(f"Invalid Codex hook payload: {exc}")

        decision = sample_secret_guard_decision(payload)
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


def sample_secret_guard_decision(payload: object) -> Decision:
    """Evaluate the CLI sample guard policy.

    This is intentionally private to the CLI sample runner. Real hooks should
    copy or write their own policy logic instead of importing a package policy.
    """

    command = _command_text(payload)
    if not command:
        return allow.decision()

    env_match = _blocked_env_name(command)
    if env_match:
        return deny.decision(f"Blocked direct secret environment access: {env_match}.")

    path_match = _blocked_path(command)
    if path_match:
        return deny.decision(f"Blocked direct secret file access: {path_match}.")

    for pattern in _blocked_command_patterns():
        if pattern.search(command):
            return deny.decision("Blocked command that appears to read secrets.")

    return allow.decision()


def _blocked_path_fragments() -> tuple[str, ...]:
    return (
        "." + "env",
        "." + "pypirc",
        "." + "npmrc",
        "." + "netrc",
        "." + "ssh",
        "id_rsa",
        "id_ed25519",
    )


def _blocked_env_names() -> tuple[str, ...]:
    return (
        "PYPI_API_TOKEN",
        "TWINE_PASSWORD",
        "CLOUDFLARE_API_TOKEN",
        "GITHUB_TOKEN",
        "OPENAI_API_KEY",
    )


def _blocked_command_patterns() -> tuple[re.Pattern[str], ...]:
    sensitive_files = r"\.(env|pypirc|npmrc)"
    return (
        re.compile(r"\b(printenv|env)\b.*\b(TOKEN|SECRET|PASSWORD|KEY)\b", re.IGNORECASE),
        re.compile(rf"\b(cat|less|more|tail|head|sed|awk|rg|grep)\b.*{sensitive_files}\b"),
    )


def _blocked_env_name(command: str) -> str:
    for name in _blocked_env_names():
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", command):
            return name
    return ""


def _blocked_path(command: str) -> str:
    for token in _split_command(command):
        normalized = token.replace("\\", "/")
        path = PurePosixPath(normalized)
        parts = set(path.parts)
        for fragment in _blocked_path_fragments():
            if fragment in normalized or fragment in parts:
                return token
    return ""


def _split_command(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def _command_text(payload: object) -> str:
    tool_input = getattr(payload, "tool_input", None)
    if isinstance(tool_input, dict):
        for key in ("cmd", "command", "script"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
    if isinstance(tool_input, str):
        return tool_input
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
