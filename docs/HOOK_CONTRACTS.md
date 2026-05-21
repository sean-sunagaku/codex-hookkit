# Hook Contracts

This document explains how `codex-hookkit` maps to Codex hook contracts.

## Upstream Schemas

Vendored schemas are copied from:

```text
https://github.com/openai/codex
codex-rs/hooks/schema/generated
```

The pinned upstream commit is recorded in:

```text
third_party/openai-codex-hook-schemas/UPSTREAM.md
```

Each hook event has an input schema and an output schema:

```text
pre-tool-use.command.input.schema.json
pre-tool-use.command.output.schema.json
permission-request.command.input.schema.json
permission-request.command.output.schema.json
...
```

List available base names with:

```sh
uv run codex-hookkit schemas
```

## Input Validation

Use `HookPayload` when writing a hook:

```python
from codex_hookkit import HookPayload

payload = HookPayload.from_stdin(schema="pre-tool-use")
```

This validates the incoming JSON against the matching input schema by default.
Disable validation only for debugging:

```python
payload = HookPayload.from_stdin(schema="pre-tool-use", validate_schema=False)
```

## Command Extraction

`HookPayload.command_text()` performs best-effort extraction from common Codex
tool inputs:

- `tool_input.cmd`
- `tool_input.command`
- `tool_input.script`
- string `tool_input`

If a future Codex tool changes the command shape, add extraction logic in
`payload.py` and cover it with tests.

## Deny By Exit Code

Codex accepts a hook process exiting with code `2` and a message on stderr as a
blocking decision. This is the default guard behavior:

```sh
codex-hookkit guard --schema pre-tool-use
```

Denied example:

```text
exit code: 2
stderr: Blocked direct secret file access: .env.
```

This mode is simple and works well for local guard hooks.

## Structured JSON Output

Some hook integrations prefer structured output. Use `--json-output`:

```sh
codex-hookkit guard --schema pre-tool-use --json-output
```

For a denied `PreToolUse`, the package emits:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked direct secret file access: .env."
  }
}
```

For `PermissionRequest`, it emits the matching `decision` shape defined by the
vendored output schema.

All JSON builders in `decisions.py` validate their output before returning it.

## Updating Schemas

Update to the latest upstream Codex schema snapshot with:

```sh
uv run python tools/update_codex_hook_schemas.py
```

Or pin a specific upstream commit:

```sh
uv run python tools/update_codex_hook_schemas.py <commit-sha>
```

After updating:

```sh
uv run pytest -q
uv build
uv run twine check dist/*
```

Review the schema diff carefully. If input or output shapes changed, update
`payload.py`, `decisions.py`, tests, and this document.
