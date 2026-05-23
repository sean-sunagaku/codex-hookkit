"""Generate small Codex hook skeletons."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent


def secret_guard_hook(schema: str = "pre-tool-use") -> str:
    """Return a minimal import-first secret guard hook script."""

    return dedent(
        '''\
        #!/usr/bin/env python3
        """Minimal Codex hook built with codex-hookkit."""

        from __future__ import annotations

        import shlex
        from pathlib import PurePosixPath

        from codex_hookkit import PreToolUseInput, deny


        def main() -> int:
            payload = PreToolUseInput.from_stdin()
            reason = blocked_reason(payload)

            if reason:
                return deny.stderr_exit(reason)

            return 0


        def blocked_reason(payload: object) -> str:
            command = command_text(payload)
            if not command:
                return ""
            path_match = blocked_path(command)
            if path_match:
                return f"Blocked direct secret file access: {path_match}."
            return ""


        def blocked_path(command: str) -> str:
            fragments = ("." + "env", "." + "pypirc", "." + "npmrc")
            for token in split_command(command):
                normalized = token.replace("\\\\", "/")
                parts = set(PurePosixPath(normalized).parts)
                for fragment in fragments:
                    if fragment in normalized or fragment in parts:
                        return token
            return ""


        def split_command(command: str) -> list[str]:
            try:
                return shlex.split(command)
            except ValueError:
                return command.split()


        def command_text(payload: object) -> str:
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
        '''
    )


def structured_secret_guard_hook() -> str:
    """Return a structured-output secret guard hook script."""

    return dedent(
        '''\
        #!/usr/bin/env python3
        """Structured Codex secret guard hook built with codex-hookkit."""

        from __future__ import annotations

        import shlex
        from pathlib import PurePosixPath

        from codex_hookkit import PreToolUseInput, PreToolUseOutput


        def main() -> int:
            payload = PreToolUseInput.from_stdin()
            reason = blocked_reason(payload)

            if reason:
                PreToolUseOutput.deny(reason).write()
            else:
                PreToolUseOutput.allow().write()

            return 0


        def blocked_reason(payload: object) -> str:
            command = command_text(payload)
            if not command:
                return ""
            path_match = blocked_path(command)
            if path_match:
                return f"Blocked direct secret file access: {path_match}."
            return ""


        def blocked_path(command: str) -> str:
            fragments = ("." + "env", "." + "pypirc", "." + "npmrc")
            for token in split_command(command):
                normalized = token.replace("\\\\", "/")
                parts = set(PurePosixPath(normalized).parts)
                for fragment in fragments:
                    if fragment in normalized or fragment in parts:
                        return token
            return ""


        def split_command(command: str) -> list[str]:
            try:
                return shlex.split(command)
            except ValueError:
                return command.split()


        def command_text(payload: object) -> str:
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
        '''
    )


def project_hooks_json(*, hook_path: str = "hooks/secret_guard.py") -> str:
    """Return a minimal project hooks.json skeleton."""

    command_prefix = 'sh -c \'cd "$(git rev-parse --show-toplevel)" && exec '
    hooks: dict[str, list[dict[str, object]]] = {
        "PreToolUse": [
            {
                "matcher": "*",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"{command_prefix}uv run python {hook_path}'",
                        "timeout": 10,
                        "statusMessage": "Checking Codex hook guard policy",
                    }
                ],
            }
        ]
    }
    return json.dumps({"hooks": hooks}, indent=2) + "\n"


def project_config_toml() -> str:
    """Return a small project-local Codex config skeleton."""

    return dedent(
        """\
        # Project-local Codex config.
        #
        # Hook commands live in .codex/hooks.json. Hook trust state is machine-local
        # because Codex keys it by absolute hook file path. This repository
        # includes a development helper you can copy if needed:
        #
        #   uv run python tools/trust_codex_hooks.py --hooks-path .codex/hooks.json

        model = "gpt-5.4-mini"
        """
    )


def project_skeleton(
    output_dir: str | Path,
    *,
    force: bool = False,
) -> tuple[Path, ...]:
    """Write a minimal Codex hook project skeleton and return created paths."""

    root = Path(output_dir)
    files = {
        root / "hooks" / "secret_guard.py": secret_guard_hook(),
        root / ".codex" / "hooks.json": project_hooks_json(),
        root / "config.toml": project_config_toml(),
    }

    existing = [path for path in files if path.exists() and not force]
    if existing:
        names = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"refusing to overwrite existing files without --force: {names}")

    written: list[Path] = []
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return tuple(written)
