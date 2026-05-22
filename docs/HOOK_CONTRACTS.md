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

List concrete file-style input and output schema names with:

```sh
uv run codex-hookkit schemas --direction both
```

## Input Validation

Use generated input models when writing a hook:

```python
from codex_hookkit import PreToolUseInput

payload = PreToolUseInput.from_stdin()
```

This validates the incoming JSON against the matching input schema by default.
`HookPayload` remains available as a compatibility wrapper for generic code:

```python
from codex_hookkit import HookPayload

payload = HookPayload.from_model(PreToolUseInput.from_stdin())
```

Codex sends the hook payload as one JSON object on `stdin`. The exact fields are
defined by the matching upstream input schema. `codex-hookkit` does not invent
that shape; it validates and exposes it.

Common fields currently include:

- `hook_event_name`
- `session_id`
- `turn_id`
- `cwd`
- `tool_name`
- `tool_input`
- `tool_use_id`
- `permission_mode`
- `model`
- `transcript_path`

Treat the schema as the contract. Treat compatibility helpers like
`HookPayload.command_text()` as helpers layered on top.

## Command Extraction

`SecretPolicy` can evaluate generated input models directly. The compatibility
`HookPayload.command_text()` method performs best-effort extraction from common
Codex tool inputs:

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

The fixed part of a structured hook response is the upstream output schema.
For `PreToolUse`, that means the response must use `hookSpecificOutput` with:

- `hookEventName`
- `permissionDecision`
- optional `permissionDecisionReason`
- optional `additionalContext`

For `PermissionRequest`, the response must use the `decision` shape defined in
`permission-request.command.output.schema.json`.

When in doubt, load the exact schema:

```python
from codex_hookkit import load_schema

schema = load_schema("pre-tool-use", direction="output")
```

## Skeleton Generation

Generate a minimal import-first hook:

```sh
uv run codex-hookkit scaffold --output hooks/secret_guard.py
```

That file is meant to be edited by the application. The CLI runner is useful
for quick starts, but custom hook behavior should live in your Python file.

## Updating Schemas

Update to the latest upstream Codex schema snapshot with:

```sh
uv run python tools/update_codex_hook_schemas.py
```

The same operation is importable:

```python
from codex_hookkit import download_schema_snapshot

snapshot = download_schema_snapshot("third_party/openai-codex-hook-schemas")
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
