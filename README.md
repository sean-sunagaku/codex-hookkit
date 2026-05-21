# codex-hookkit

Small helpers for building Codex hook guards against upstream Codex hook schemas.

`codex-hookkit` starts from one idea: Codex hook code should validate against
the same generated schemas that Codex itself publishes. The package vendors a
small schema snapshot from `openai/codex` and adds a thin Python layer for
payload parsing, allow / deny decisions, and a minimal secret guard CLI.

## What Is Included

- vendored snapshots of `openai/codex` generated hook schemas
- stdin parsing for Codex hook payloads
- JSON-schema validation helpers
- allow / deny output builders
- a minimal command guard CLI

## Project Names

```text
GitHub repo: codex-hookkit
PyPI name:   codex-hookkit
Python pkg:  codex_hookkit
CLI:         codex-hookkit
```

## Install

```sh
uv add codex-hookkit
```

Or run the CLI directly:

```sh
uvx --from codex-hookkit codex-hookkit schemas
```

## CLI

Use `codex-hookkit guard` as a Codex hook command. It reads one hook payload from
stdin, validates it against the vendored upstream schema, and exits:

- `0` for allowed payloads
- `2` with a stderr reason for denied payloads

```sh
codex-hookkit guard --schema pre-tool-use
```

For structured Codex hook output:

```sh
codex-hookkit guard --schema pre-tool-use --json-output
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

## Codex Hook Example

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "uv run python -m codex_hookkit.cli guard --schema pre-tool-use",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## Architecture

The runtime flow is:

```text
Codex hook payload
  -> HookPayload.from_stdin()
  -> schema validation
  -> SecretPolicy.evaluate()
  -> allow or deny output
```

The key modules are:

- `schemas.py`: locate, load, and validate vendored Codex schemas
- `payload.py`: parse hook payloads and extract command text
- `decisions.py`: build allow / deny decisions and structured outputs
- `policy.py`: default secret-file and token-access guard
- `cli.py`: command line interface used by Codex hooks

See `docs/ARCHITECTURE.md` for the full design notes.

## Development

```sh
uv sync --dev
uv run pytest -q
uv build
uv run twine check dist/*
```

List vendored schemas:

```sh
uv run codex-hookkit schemas
```

Update the upstream schema snapshot:

```sh
uv run python tools/update_codex_hook_schemas.py
```

## Documentation

- `docs/ARCHITECTURE.md`: design and module boundaries
- `docs/HOOK_CONTRACTS.md`: Codex hook input / output contracts
- `docs/AI_GUIDE.md`: guide for AI agents changing this repository
- `docs/RELEASE.md`: build, publish, and post-publish checks
- `AGENTS.md`: repository instructions for Codex and other agents
