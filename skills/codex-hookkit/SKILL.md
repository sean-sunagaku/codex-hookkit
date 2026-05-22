---
name: codex-hookkit
description: Build, scaffold, debug, or verify Python Codex hooks with the codex-hookkit library. Use when a task involves Codex hook payload schemas, generated input/output models, PreToolUse or PermissionRequest guards, hook trust state, codex exec hook E2E checks, or updating the vendored openai/codex hook schema snapshot.
---

# Codex Hookkit

Use this skill when working on Python hooks built with `codex-hookkit`.

## Core Workflow

1. Treat the vendored upstream Codex schemas as the contract.
2. Read hook input with generated models such as `PreToolUseInput.from_stdin()`.
3. Return structured output with generated models such as `PreToolUseOutput.deny(...).write()` when the hook supports JSON output.
4. Use `exit 2` plus stderr only for the simple deny path or examples that intentionally demonstrate exit-status mode.
5. Keep project-specific policy outside the default `SecretPolicy`; add product rules in the consuming hook file.
6. Verify with unit tests first, then run the real `codex exec` smoke path when auth is available.

## Implementation Pattern

Prefer import-first hook files over putting real behavior in the generic CLI runner:

```python
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
```

Use the CLI for samples, scaffolding, schema listing, trust writing, and debug smoke checks.

## Commands

Use these from the repository root:

```sh
uv run codex-hookkit scaffold --output hooks/secret_guard.py
uv run codex-hookkit schemas --direction both
uv run codex-hookkit trust-hooks --hooks-path .codex/hooks.json
make codex-exec-e2e
make codex-exec-debug
make check
```

`make codex-exec-debug` prints compact `codex exec --json` events and hook-related stderr lines. Inspect both stdout events and stderr because Codex may report a hook denial on stderr while still completing the overall `codex exec` turn successfully.

## Editing This Repository

- Keep generated input/output models in `src/codex_hookkit/inputs.py` and `src/codex_hookkit/outputs.py` generated-only.
- Regenerate models with `uv run python tools/generate_pydantic_models.py`.
- Check generated-model drift with `uv run python tools/check_generated_models.py`.
- Update upstream schema snapshots only through `tools/update_codex_hook_schemas.py`.
- Do not add runtime network access to hook evaluation.
- Preserve the Codex review hook recursion guard: `CODEX_HOOKKIT_REVIEW_ACTIVE=1`.
- Preserve the hook trust workflow: `codex-hookkit trust-hooks --hooks-path .codex/hooks.json`.

## References

Read [references/hookkit-reference.md](references/hookkit-reference.md) when you need exact model names, CLI roles, hook config shape, verification commands, or debug interpretation details.
