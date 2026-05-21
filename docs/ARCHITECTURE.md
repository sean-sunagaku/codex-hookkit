# Architecture

`codex-hookkit` is intentionally small. It is a Python helper package for
building Codex hook guards without guessing the hook payload contract.

## Design Goals

- Treat upstream Codex generated JSON schemas as the source of truth.
- Keep the Python API thin and predictable.
- Make hook guards easy to write as normal Python files.
- Keep the CLI as a sample runner and setup helper, not the main abstraction.
- Prefer a safe default policy, while leaving real product policy to callers.
- Avoid vendoring the full `openai/codex` repository unless it becomes useful.

## Package Shape

```text
src/codex_hookkit/
  schemas.py      # schema discovery, loading, and jsonschema validation
  payload.py      # HookPayload parsing from stdin, stream, or dict
  outputs.py      # generated Pydantic classes for schema-valid hook outputs
  decisions.py    # compatibility allow / deny helpers over generated outputs
  policy.py       # minimal SecretPolicy default guard
  review.py       # changed-code marker and Stop-hook Codex review runner
  upstream.py     # importable schema snapshot downloader
  scaffold.py     # hook skeleton generation
  cli.py          # sample runner and project setup helpers
```

The repository also contains:

```text
third_party/openai-codex-hook-schemas/
  generated/*.schema.json
  UPSTREAM.md

tools/update_codex_hook_schemas.py
tools/generate_pydantic_outputs.py
.codex/hooks.json
tests/test_cli.py
tests/test_outputs.py
tests/test_review.py
```

## Library-First Data Flow

```mermaid
flowchart LR
  A["Codex hook event"] --> B["stdin JSON payload"]
  B --> C["HookPayload.from_stdin"]
  C --> D["schemas.validate(input)"]
  D --> E["SecretPolicy.evaluate"]
  E --> F{"Decision"}
  F -->|"allow"| G["exit 0"]
  F -->|"deny"| H["exit 2 + stderr"]
  F -->|"--json-output"| I["validated hookSpecificOutput JSON"]
```

The CLI `guard` command follows this same flow, but it is intentionally just a
minimal sample / generic runner. Production hooks should usually be ordinary
Python files that import `codex_hookkit`.

## Schema Strategy

The package vendors only `openai/codex` generated hook schema JSON files.
Those files live under `third_party/openai-codex-hook-schemas/generated`.

At build time, Hatch includes the snapshot inside the wheel at:

```text
codex_hookkit/vendor/openai-codex-hook-schemas/generated
```

At development time, `schemas.py` can also read the local `third_party`
snapshot. This keeps local tests and editable usage simple.

This is deliberately a snapshot, not a Git submodule:

- Reviews show exactly which schema JSON files changed.
- The package does not pull in the full Codex Rust codebase.
- Updates are explicit and pinned through `UPSTREAM.md`.

## Public API

The intended import path is:

```python
from codex_hookkit import HookPayload, SecretPolicy, allow, deny
```

Stable concepts:

- `HookPayload`: parsed hook payload plus convenience accessors.
- `SecretPolicy`: small default policy for secret-file and token access.
- `Decision`: allowed or denied result.
- `StructuredOutput`: base class for generated, schema-validated output models.
- `PreToolUseOutput`, `PermissionRequestOutput`, and other generated output
  classes: structured hook output builders.
- `allow` / `deny`: compatibility builders for simple decisions and common
  Codex JSON output.
- `validate`: validate arbitrary input or output against vendored schemas.
- `download_schema_snapshot`: fetch generated schemas from `openai/codex`.
- `secret_guard_hook`: generate the minimal import-first hook skeleton.
- `request_review` / `run_review`: mark changed code in `PostToolUse`, then run
  one nested Codex review in `Stop`.

The current default policy is conservative but not complete. It blocks common
direct reads of `.env`, `.pypirc`, `.npmrc`, `.netrc`, `.ssh`, private key file
names, and selected token environment names.

## CLI Role

`codex-hookkit` is useful, but it is not the core architecture. It provides:

- `guard`: minimal sample / generic guard runner
- `schemas`: schema discovery
- `scaffold`: hook skeleton generation
- `download-schemas`: upstream schema snapshot download

`codex-hookkit guard` reads one JSON payload from `stdin`.

Default behavior:

- valid and allowed payload: exit `0`
- invalid payload: exit `2` with stderr
- denied payload: exit `2` with stderr

With `--json-output`, denials and allows are emitted as validated
`hookSpecificOutput` JSON and the process exits `0`.

## Generated Output Models

`src/codex_hookkit/outputs.py` is generated from the vendored Codex output
schemas. It should not be edited by hand.

Regenerate it with:

```sh
uv run python tools/generate_pydantic_outputs.py
```

The test suite includes an exact sync check so generated classes cannot drift
from the generator. This keeps the architecture simple:

- schema files define the contract
- the generator turns that contract into Pydantic classes
- `outputs.py` exposes structured, validated objects
- `decisions.py` remains a thin backward-compatible wrapper

## Local Codex Hook Config

The repository includes `.codex/hooks.json` for dogfooding:

- `PreToolUse` runs `codex-hookkit guard --schema pre-tool-use`
- `PermissionRequest` runs `codex-hookkit guard --schema permission-request`
- `PostToolUse` runs `codex-hookkit request-review`
- `Stop` runs `codex-hookkit run-review`

The command uses `uv run python -m codex_hookkit.cli` so local changes are
tested before an installed wheel.

The review hooks are deliberately split into two phases. `PostToolUse` only
writes a small marker under `.codex-hookkit/` when git reports changed code
files. `Stop` consumes that marker and launches `codex exec` once. Nested review
runs set `CODEX_HOOKKIT_REVIEW_ACTIVE=1`, and hook helpers no-op when that
variable is present, preventing recursive reviews.

## Boundaries

This project is a toolkit, not a full policy engine.

Keep these boundaries in mind:

- Schema validation belongs in `schemas.py`.
- Payload normalization belongs in `payload.py`.
- Generated Codex output models belong in `outputs.py`.
- Compatibility decision helpers belong in `decisions.py`.
- Security rules belong in `policy.py` or caller-owned policies.
- Changed-code review orchestration belongs in `review.py`.
- Schema download belongs in `upstream.py`.
- Skeleton text belongs in `scaffold.py`.
- CLI argument parsing and sample runner behavior belong in `cli.py`.

Do not add product-specific policy directly to the default package unless it is
generic enough to help most Codex hook users.
