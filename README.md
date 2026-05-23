# codex-hookkit

Small helpers for building Python Codex hooks against upstream Codex hook schemas.

`codex-hookkit` starts from one idea: Codex hook code should validate against
the same generated schemas that Codex itself publishes. The package vendors a
small schema snapshot from `openai/codex` and adds a thin Python layer for
schema validation, generated input models, generated output models, and
allow / deny decisions.

## What Is Included

- vendored snapshots of `openai/codex` generated hook schemas
- stdin parsing for Codex hook payloads
- JSON-schema validation helpers
- allow / deny output builders
- Pydantic structured input and output models generated from Codex schemas
- a minimal sample guard runner CLI
- CLI helpers for hook skeletons, local trust-state writes, review-hook samples,
  and schema snapshot updates

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
from codex_hookkit import PreToolUseInput, deny


def main() -> int:
    payload = PreToolUseInput.from_stdin()
    reason = blocked_reason(payload)

    if reason:
        return deny.stderr_exit(reason)

    return 0


def blocked_reason(payload: PreToolUseInput) -> str:
    command = payload.tool_input.get("cmd", "") if isinstance(payload.tool_input, dict) else ""
    if command == "pwd":
        return ""
    return ""
```

Generate that skeleton with:

```sh
codex-hookkit scaffold --output hooks/secret_guard.py
```

Initialize a minimal hook project skeleton with:

```sh
codex-hookkit init --output-dir .
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
`PermissionRequestOutput`, and `SessionStartOutput`. `PreToolUseOutput.deny()`
uses the top-level `decision="block"` / `reason` shape. Regenerate those
classes from the vendored Codex schemas with:

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

For structured Codex hook output on integrations that support it:

```sh
codex-hookkit guard --schema pre-tool-use --json-output
```

For `PreToolUse`, the JSON helper emits the schema-valid top-level `decision`
shape. As observed with `codex exec` v0.133.0, live `PreToolUse` command hooks
still treat that structured stdout as `PreToolUse Failed`, so the default guard
uses `exit 2 + stderr`.

Update the vendored schema snapshot with the repository tool:

```sh
uv run python tools/update_codex_hook_schemas.py
```

Write Codex hook trust state for all command hooks in a `hooks.json` file with
the repository tool:

```sh
uv run python tools/trust_codex_hooks.py --hooks-path .codex/hooks.json
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

The stable package API is intentionally narrow:

- generated input models such as `PreToolUseInput`
- generated output models such as `PreToolUseOutput`
- schema helpers such as `load_schema` and `validate`
- small allow / deny decision helpers

`PreToolUseOutput.deny(...)` builds top-level `decision="block"` output.
The verified live Codex CLI deny path remains `deny.stderr_exit(...)`.

Policy, review orchestration, trust-state writes, schema downloading, and
scaffolding are example/tooling concerns, not public Python APIs.

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

The repository includes a small review hook example for running Codex after
code changes:

- `examples/python_hooks/codex_review/request_review.py`: a `PostToolUse` hook
  that marks a pending review when the repository has changed code files
- `examples/python_hooks/codex_review/run_review.py`: a `Stop` hook that
  consumes the marker, runs inferred local checks, and runs one nested
  `codex exec` review

The nested review inherits `CODEX_HOOKKIT_REVIEW_ACTIVE=1`, so hook commands
skip themselves during the review and avoid recursive Codex runs.
Before launching Codex, the Stop hook selects non-mutating verification
commands for the changed project, such as `uv run ruff format --check .`,
`uv run ruff check .`, and `uv run pytest -q` for Python projects. The check
results are included in the review prompt. Use `--skip-checks` if a project
wants review-only behavior.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "uv run python examples/python_hooks/codex_review/request_review.py",
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
            "command": "uv run python examples/python_hooks/codex_review/run_review.py",
            "timeout": 900
          }
        ]
      }
    ]
  }
}
```

Use `--dry-run` to inspect the review prompt without launching Codex:

```sh
uv run python examples/python_hooks/codex_review/run_review.py --dry-run
```

## Architecture

The runtime flow is:

```text
Codex hook payload
  -> XxxInput.from_stdin()
  -> schema validation
  -> hook-owned policy logic
  -> XxxOutput.write() or exit status
```

The key modules are:

- `core/schemas.py`: locate, load, and validate vendored Codex schemas
- `core/inputs.py`: generated Pydantic classes for Codex hook inputs
- `core/outputs.py`: generated Pydantic classes for Codex hook outputs
- `core/decisions.py`: build allow / deny decisions and structured outputs
- `cli/`: sample guard runner, schema listing, and skeleton helpers
- `examples/`: sample policies and hook files
- `tools/`: maintainer helpers such as trust-state writing and schema updates

See `docs/ARCHITECTURE.md` for the full design notes.

## Development

```sh
uv sync --dev
uv run python tools/generate_pydantic_models.py
uv run python tools/validate_skills.py
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
