# codex-hookkit Reference

## Package Names

```text
PyPI name:      codex-hookkit
Python package: codex_hookkit
CLI:            codex-hookkit
```

## Generated Input Models

Use generated input models for all hook payloads:

```python
from codex_hookkit import PreToolUseInput

payload = PreToolUseInput.from_stdin()
```

Available input models:

- `PermissionRequestInput`
- `PostCompactInput`
- `PostToolUseInput`
- `PreCompactInput`
- `PreToolUseInput`
- `SessionStartInput`
- `StopInput`
- `SubagentStartInput`
- `SubagentStopInput`
- `UserPromptSubmitInput`

## Generated Output Models

Use generated output models for structured hook responses:

```python
from codex_hookkit import PreToolUseOutput

PreToolUseOutput.deny("Blocked by local policy.").write()
```

Common output models:

- `PermissionRequestOutput`
- `PostCompactOutput`
- `PostToolUseOutput`
- `PreCompactOutput`
- `PreToolUseOutput`
- `SessionStartOutput`
- `StopOutput`
- `SubagentStartOutput`
- `SubagentStopOutput`
- `UserPromptSubmitOutput`

The generated models validate against vendored upstream output schemas. Do not hand-edit generated files; update the generator or the schema snapshot. `PreToolUseOutput.deny(...)` emits top-level `decision="block"` / `reason`. For live `PreToolUse` guard denials, use `deny.stderr_exit(...)`; `codex exec` v0.133.0 still reports structured `PreToolUse` stdout as a hook failure.

## CLI Roles

The CLI is intentionally secondary to import-first hook files:

```sh
codex-hookkit guard --schema pre-tool-use
codex-hookkit guard --schema pre-tool-use --json-output
codex-hookkit scaffold --output hooks/secret_guard.py
codex-hookkit init --output-dir .
codex-hookkit schemas --direction both
```

Use `guard` as a minimal sample or generic runner. Put real product-specific behavior in a Python hook file that imports `codex_hookkit`. Use repository tools for schema updates and local trust-state writes.

## Hook Config Shape

A command hook config uses Codex's hook JSON shape:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "uv run python hooks/secret_guard.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

After editing a command hook, rewrite trust state:

```sh
uv run python tools/trust_codex_hooks.py --hooks-path .codex/hooks.json
```

Codex records trust state by absolute hook file path and command hash, so do not commit machine-local `[hooks.state]` entries.

## Verification

Use the normal local checks:

```sh
uv run python tools/check_generated_models.py
uv run ruff format --check .
uv run ruff check .
uv run pytest -q
rm -rf dist
uv build
uv run twine check dist/*
```

`make check` runs the same sequence.

Use the real Codex CLI smoke checks when local Codex auth is available:

```sh
make codex-exec-e2e
make codex-exec-debug
```

`make codex-exec-e2e` runs pytest against a temporary `CODEX_HOME`.
`make codex-exec-debug` prints compact `codex exec --json` events plus hook-related stderr lines.

## Debug Interpretation

Codex CLI JSON mode currently reports assistant messages as:

```json
{"type": "item.completed", "item": {"type": "agent_message", "text": "..."}}
```

Do not look only for a top-level `agent_message` event.

Hook denials may appear on stderr while the overall `codex exec` command still exits successfully. For a blocked shell command, look for a stderr line containing:

```text
Command blocked by PreToolUse hook
```

This means the hook fired correctly even if stdout only shows the assistant summarizing the result.

## Codex Review Hook

The review hook flow is two-step:

- `examples/python_hooks/codex_review/request_review.py`: `PostToolUse` hook that writes a pending marker when code changes
- `examples/python_hooks/codex_review/run_review.py`: `Stop` hook that consumes the marker, runs inferred non-mutating local checks, and runs one nested `codex exec` review

Always keep this recursion guard in nested review runs:

```sh
CODEX_HOOKKIT_REVIEW_ACTIVE=1
```
