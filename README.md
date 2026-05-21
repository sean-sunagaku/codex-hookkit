# codex-hookkit

Small helpers for building Codex hook guards against upstream Codex hook schemas.

This package intentionally starts small:

- vendored snapshots of `openai/codex` generated hook schemas
- stdin parsing for Codex hook payloads
- JSON-schema validation helpers
- allow / deny output builders
- a minimal command guard CLI

## Install

```sh
uv add codex-hookkit
```

## CLI

Use `codex-hookkit guard` as a Codex hook command. It reads one hook payload from
stdin, validates it against the vendored upstream schema, and exits:

- `0` for allowed payloads
- `2` with a stderr reason for denied payloads

```sh
codex-hookkit guard --schema pre-tool-use
```

## Python API

```python
from codex_hookkit import HookPayload, SecretPolicy, deny

payload = HookPayload.from_stdin(schema="pre-tool-use")
decision = SecretPolicy.default().evaluate(payload)

if decision.denied:
    raise SystemExit(deny.stderr_exit(decision.reason))
```

JSON output helpers are also available for Codex hook contracts that consume
structured output.
