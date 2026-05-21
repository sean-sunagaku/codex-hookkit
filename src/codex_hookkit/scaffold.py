"""Generate small Codex hook skeletons."""

from __future__ import annotations

from textwrap import dedent


def secret_guard_hook(schema: str = "pre-tool-use") -> str:
    """Return a minimal import-first secret guard hook script."""

    return dedent(
        f'''\
        #!/usr/bin/env python3
        """Minimal Codex hook built with codex-hookkit."""

        from __future__ import annotations

        from codex_hookkit import HookPayload, SecretPolicy, deny


        def main() -> int:
            payload = HookPayload.from_stdin(schema={schema!r})
            decision = SecretPolicy.default().evaluate(payload)

            if decision.denied:
                return deny.stderr_exit(decision.reason)

            return 0


        if __name__ == "__main__":
            raise SystemExit(main())
        '''
    )
