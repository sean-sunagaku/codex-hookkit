# Payloads And Outputs

Codex hook processes communicate through standard input, standard output,
standard error, and exit status.

## Input

Codex starts the hook command and writes one JSON object to `stdin`.

```text
Codex
  -> starts hook process
  -> writes JSON payload to stdin
  -> waits for process exit
```

Read it with:

```python
from codex_hookkit import PreToolUseInput

payload = PreToolUseInput.from_stdin()
```

The payload shape is fixed by the upstream generated input schema for that hook
event. For example:

```text
pre-tool-use.command.input.schema.json
permission-request.command.input.schema.json
post-tool-use.command.input.schema.json
```

`codex-hookkit` exposes generated Pydantic input models, but those models are
generated from the schema. The schema remains the source of truth.

Minimal Python hook files live in:

```text
examples/python_hooks/exit_status/*.py
examples/python_hooks/structured_output/*.py
```

Use `exit_status` when a hook only needs `exit 0` or `exit 2 + stderr`.
Use `structured_output` when a hook should write a schema-valid JSON response
to stdout and the Codex runtime accepts structured output for that hook event.

The structured-output examples use Pydantic models generated from the vendored
Codex input and output schemas:

```python
from codex_hookkit import PreToolUseInput, PreToolUseOutput

payload = PreToolUseInput.from_stdin()
PreToolUseOutput.deny("Blocked direct secret file access.").write()
```

For `PreToolUse`, `PreToolUseOutput.deny()` emits the top-level
`decision="block"` / `reason` shape. For live guard hooks, the `exit_status`
example remains the default because `codex exec` v0.133.0 still reports
structured `PreToolUse` stdout as a hook failure.

Regenerate them with:

```sh
uv run python tools/generate_pydantic_models.py
```

## Common Input Fields

Current `PreToolUse`-style payloads commonly include:

```json
{
  "hook_event_name": "PreToolUse",
  "session_id": "session",
  "turn_id": "turn",
  "cwd": "/path/to/project",
  "tool_name": "shell",
  "tool_input": {
    "cmd": "pwd"
  },
  "tool_use_id": "tool-use",
  "permission_mode": "default",
  "model": "gpt-5",
  "transcript_path": null
}
```

The exact fields can change when Codex changes the upstream schema. Update the
vendored snapshot before relying on new fields.

## Command Text

Policy logic belongs to the hook file or the consuming project. When a hook
needs command text, extract it defensively from common input shapes:

- `tool_input.cmd`
- `tool_input.command`
- `tool_input.script`
- string `tool_input`

Not every hook event is command-shaped, so policy code should tolerate missing
or differently shaped `tool_input` values.

## Blocking With Exit Status

The simplest blocking response is:

```text
exit code: 2
stderr: reason visible to Codex
```

Use:

```python
from codex_hookkit import deny

return deny.stderr_exit("Blocked direct secret file access: .env.")
```

This is the default behavior of:

```sh
codex-hookkit guard --schema pre-tool-use
```

## Structured Output

Some integrations prefer a structured JSON response on `stdout`. That shape is
fixed by the upstream output schema:

```text
pre-tool-use.command.output.schema.json
permission-request.command.output.schema.json
```

Use the output builders:

```python
from codex_hookkit import deny

output = deny.pre_tool_use_json("Blocked direct secret file access: .env.")
```

The builders validate their result before returning it.

For live `PreToolUse` guard hooks, `deny.stderr_exit(...)` remains the default
and most compatible blocking path.

Python examples live under `examples/python_hooks/`. Hook configuration samples
live in `examples/hooks.json` and `examples/codex_review_hooks.json`.

## What Is Fixed

Fixed by upstream Codex schemas:

- hook input JSON shape
- structured output JSON shape
- hook event names inside structured output
- allowed enum values such as permission decisions

Owned by your hook code:

- which schema you validate against
- which policy rules you apply
- whether you block through `exit 2 + stderr` or structured JSON
- what message you show when denying

## Inspecting Schemas

List base schema names:

```sh
codex-hookkit schemas
```

List input and output schema file names:

```sh
codex-hookkit schemas --direction both
```

Load a schema from Python:

```python
from codex_hookkit import load_schema

input_schema = load_schema("pre-tool-use", direction="input")
output_schema = load_schema("pre-tool-use", direction="output")
```
