# codex-hookkit

Small helpers for building Codex hook guards against upstream Codex hook schemas.

`codex-hookkit` starts from one idea: Codex hook code should validate against
the same generated schemas that Codex itself publishes. The package vendors a
small schema snapshot from `openai/codex` and adds a thin Python layer for
payload parsing, allow / deny decisions, scaffold generation, and schema
snapshot updates.

## What Is Included

- vendored snapshots of `openai/codex` generated hook schemas
- stdin parsing for Codex hook payloads
- JSON-schema validation helpers
- allow / deny output builders
- Pydantic structured input and output models generated from Codex schemas
- a minimal sample guard runner CLI
- a hook skeleton generator
- a two-step Codex review hook for changed code
- an importable schema snapshot downloader

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

## Import-First Usage

For real hook implementations, prefer importing the library from your own
Python hook file:

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
```

Generate that skeleton with:

```sh
codex-hookkit scaffold --output hooks/secret_guard.py
```

Generate a Codex review hook config with:

```sh
codex-hookkit scaffold --kind codex-review-hooks --output hooks.json
```

The repository also includes Python hook examples and real hook config samples:

```text
examples/minimal_secret_guard.py
examples/python_hooks/exit_status/*.py
examples/python_hooks/structured_output/*.py
examples/hooks.json
examples/codex_review_hooks.json
```

A Codex Skill for using this library lives at:

```text
skills/codex-hookkit/SKILL.md
```

The structured examples use generated Pydantic classes such as
`PreToolUseInput`, `PreToolUseOutput`, `PermissionRequestInput`,
`PermissionRequestOutput`, and `SessionStartOutput`. Regenerate those classes
from the vendored Codex schemas with:

```sh
uv run python tools/generate_pydantic_models.py
```

## CLI Helpers

`codex-hookkit guard` is a minimal sample / generic guard runner. It reads one
hook payload from stdin, validates it against the vendored upstream schema, and
exits:

- `0` for allowed payloads
- `2` with a stderr reason for denied payloads

```sh
codex-hookkit guard --schema pre-tool-use
```

For structured Codex hook output:

```sh
codex-hookkit guard --schema pre-tool-use --json-output
```

Download a schema snapshot from Python:

```python
from codex_hookkit import download_schema_snapshot

snapshot = download_schema_snapshot("third_party/openai-codex-hook-schemas")
print(snapshot.commit, snapshot.schema_count)
```

Or from the CLI:

```sh
codex-hookkit download-schemas --dest third_party/openai-codex-hook-schemas
```

Write Codex hook trust state for all command hooks in a `hooks.json` file:

```sh
codex-hookkit trust-hooks --hooks-path .codex/hooks.json
```

This upserts `[hooks.state."..."] trusted_hash = "..."` entries in
`~/.codex/config.toml`. Use `--dry-run` to print the entries without writing.
The repository includes a small project-local `config.toml` for Codex defaults;
trust state is not committed because Codex records absolute hook file paths.

Run the real Codex CLI hook smoke test locally with:

```sh
make codex-exec-e2e
```

That test creates a temporary `CODEX_HOME`, copies your existing Codex auth,
writes hook trust entries, then verifies `codex exec` can run an ordinary
command and that the secret-file guard blocks a sensitive file-read command.
It is skipped in normal CI unless `CODEX_HOOKKIT_RUN_CODEX_EXEC_E2E=1` is set.

For debugging the same path with compact `codex exec --json` events:

```sh
make codex-exec-debug
```

One important detail: Codex CLI JSON mode currently reports assistant text as
`item.completed` events whose `item.type` is `agent_message`. Hook denials may
also be surfaced on stderr as lines such as `Command blocked by PreToolUse
hook: ...`. A stdout-only check can therefore make a working hook look like it
did not fire; inspect both the JSON events and hook-related stderr lines.

## Python API

```python
from codex_hookkit import PreToolUseInput, PreToolUseOutput, SecretPolicy

payload = PreToolUseInput.from_stdin()
decision = SecretPolicy.default().evaluate(payload)

if decision.denied:
    PreToolUseOutput.deny(decision.reason).write()
else:
    PreToolUseOutput.allow().write()
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

## Codex Review Hook

`codex-hookkit` also includes a small review hook flow for running Codex after
code changes:

- `request-review`: a `PostToolUse` hook that marks a pending review when the
  repository has changed code files
- `run-review`: a `Stop` hook that consumes the marker and runs one nested
  `codex exec` review

The nested review inherits `CODEX_HOOKKIT_REVIEW_ACTIVE=1`, so hook commands
skip themselves during the review and avoid recursive Codex runs.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "uv run python -m codex_hookkit.cli request-review",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "uv run python -m codex_hookkit.cli run-review",
            "timeout": 300
          }
        ]
      }
    ]
  }
}
```

Use `--dry-run` to inspect the review prompt without launching Codex:

```sh
uv run python -m codex_hookkit.cli run-review --dry-run
```

## Architecture

The runtime flow is:

```text
Codex hook payload
  -> XxxInput.from_stdin()
  -> schema validation
  -> SecretPolicy.evaluate()
  -> XxxOutput.write() or exit status
```

The key modules are:

- `schemas.py`: locate, load, and validate vendored Codex schemas
- `inputs.py`: generated Pydantic classes for Codex hook inputs
- `outputs.py`: generated Pydantic classes for Codex hook outputs
- `decisions.py`: build allow / deny decisions and structured outputs
- `policy.py`: default secret-file and token-access guard
- `review.py`: two-step changed-code Codex review hook
- `trust.py`: compute and write Codex hook trusted hashes
- `upstream.py`: download pinned upstream schema snapshots
- `scaffold.py`: generate small hook skeletons
- `cli.py`: sample runner and project setup helpers

See `docs/ARCHITECTURE.md` for the full design notes.

## Development

```sh
uv sync --dev
uv run python tools/generate_pydantic_models.py
uv run ruff format .
uv run ruff check .
uv run pytest -q
rm -rf dist
uv build
uv run twine check dist/*
```

Or run the same local gate that CI uses:

```sh
make check
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
- `docs/PAYLOADS.md`: what hook payloads look like and what outputs are fixed
- `docs/AI_GUIDE.md`: guide for AI agents changing this repository
- `docs/RELEASE.md`: build, publish, and post-publish checks
- `docs/ja/`: Japanese documentation
- `README.ja.md`: Japanese README
- `AGENTS.md`: repository instructions for Codex and other agents
