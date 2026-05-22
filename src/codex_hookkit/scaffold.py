"""Generate small Codex hook skeletons."""

from __future__ import annotations

import json
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
