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
from codex_hookkit import HookPayload

payload = HookPayload.from_stdin(schema="pre-tool-use")
```

The payload shape is fixed by the upstream generated input schema for that hook
event. For example:

```text
pre-tool-use.command.input.schema.json
permission-request.command.input.schema.json
post-tool-use.command.input.schema.json
```

`codex-hookkit` exposes convenience accessors, but those accessors are not the
source of truth. The schema is.

Minimal validated examples live in `examples/`:

```text
examples/permission_request_payload.json
examples/post_compact_payload.json
examples/post_tool_use_payload.json
examples/pre_compact_payload.json
examples/pre_tool_use_payload.json
examples/session_start_payload.json
examples/stop_payload.json
examples/subagent_start_payload.json
examples/subagent_stop_payload.json
examples/user_prompt_submit_payload.json
```

Minimal Python hook files live in:

```text
examples/python_hooks/exit_status/*.py
examples/python_hooks/structured_output/*.py
```

Use `exit_status` when a hook only needs `exit 0` or `exit 2 + stderr`.
Use `structured_output` when a hook should write a schema-valid JSON response
to stdout.

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

`HookPayload.command_text()` extracts a command from common input shapes:

- `tool_input.cmd`
- `tool_input.command`
- `tool_input.script`
- string `tool_input`

This is a best-effort helper for command-like tools. Policy code should still
be written defensively because not every hook event is command-shaped.

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

Minimal validated output examples live in `examples/`:

```text
examples/permission_request_allow.json
examples/permission_request_deny.json
examples/permission_request_output.json
examples/post_compact_output.json
examples/post_tool_use_output.json
examples/pre_compact_output.json
examples/pre_tool_use_allow.json
examples/pre_tool_use_deny.json
examples/pre_tool_use_output.json
examples/session_start_output.json
examples/stop_output.json
examples/subagent_start_output.json
examples/subagent_stop_output.json
examples/user_prompt_submit_output.json
```

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
