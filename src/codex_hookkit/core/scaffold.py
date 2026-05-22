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

        from codex_hookkit import PreToolUseInput, SecretPolicy, deny


        def main() -> int:
            payload = PreToolUseInput.from_stdin()
            decision = SecretPolicy.default().evaluate(payload)

            if decision.denied:
                return deny.stderr_exit(decision.reason)

            return 0


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

        from codex_hookkit import PreToolUseInput, PreToolUseOutput, SecretPolicy


        def main() -> int:
            payload = PreToolUseInput.from_stdin()
            decision = SecretPolicy.default().evaluate(payload)

            if decision.denied:
                PreToolUseOutput.deny(decision.reason).write()
            else:
                PreToolUseOutput.allow().write()

            return 0


        if __name__ == "__main__":
            raise SystemExit(main())
        '''
    )


def project_hooks_json(
    *, hook_path: str = "hooks/secret_guard.py", include_review: bool = False
) -> str:
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
    if include_review:
        review_config = json.loads(codex_review_hooks())
        hooks.update(review_config["hooks"])
    return json.dumps({"hooks": hooks}, indent=2) + "\n"


def project_config_toml() -> str:
    """Return a small project-local Codex config skeleton."""

    return dedent(
        """\
        # Project-local Codex config.
        #
        # Hook commands live in .codex/hooks.json. Hook trust state is machine-local
        # because Codex keys it by absolute hook file path, so write it with:
        #
        #   uv run codex-hookkit trust-hooks --hooks-path .codex/hooks.json

        model = "gpt-5.4-mini"
        """
    )


def project_skeleton(
    output_dir: str | Path,
    *,
    force: bool = False,
    include_review: bool = False,
) -> tuple[Path, ...]:
    """Write a minimal Codex hook project skeleton and return created paths."""

    root = Path(output_dir)
    files = {
        root / "hooks" / "secret_guard.py": structured_secret_guard_hook(),
        root / ".codex" / "hooks.json": project_hooks_json(include_review=include_review),
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


def codex_review_hooks() -> str:
    """Return a Codex hooks.json snippet that runs review after code changes."""

    command_prefix = 'sh -c \'cd "$(git rev-parse --show-toplevel)" && exec '
    config = {
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": (
                                f"{command_prefix}"
                                "uv run python -m codex_hookkit.cli request-review'"
                            ),
                            "timeout": 10,
                            "statusMessage": "Marking Codex review when code changes",
                        }
                    ],
                }
            ],
            "Stop": [
                {
                    "matcher": "*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": (
                                f"{command_prefix}uv run python -m codex_hookkit.cli run-review'"
                            ),
                            "timeout": 300,
                            "statusMessage": "Running Codex review for changed code",
                        }
                    ],
                }
            ],
        }
    }
    return json.dumps(config, indent=2) + "\n"
