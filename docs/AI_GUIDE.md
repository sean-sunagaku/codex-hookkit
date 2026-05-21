# AI Agent Guide

This guide is for AI agents working in this repository. It is intentionally
operational and explicit.

## Mission

`codex-hookkit` helps developers build Codex hooks against the real upstream
Codex hook schemas. Keep the project small, boring, and easy to trust.

## First Read

Read these files before changing behavior:

```text
README.md
docs/ARCHITECTURE.md
docs/HOOK_CONTRACTS.md
src/codex_hookkit/*.py
tests/test_cli.py
third_party/openai-codex-hook-schemas/UPSTREAM.md
```

For a release or publishing task, also read:

```text
docs/RELEASE.md
```

## Invariants

- `openai/codex` generated schemas are the upstream contract.
- Do not hand-edit vendored schema JSON files.
- Update schema JSON through `tools/update_codex_hook_schemas.py`.
- Keep the core API import-first. The CLI is a sample runner and helper.
- Keep product-specific security rules out of the default policy.
- Validate hook input and generated hook output whenever practical.
- Preserve `exit 2 + stderr` as the default blocking behavior.
- Keep package imports under `codex_hookkit`.
- Keep the PyPI project name `codex-hookkit`.

## Common Commands

```sh
uv sync --dev
uv run pytest -q
uv build
uv run twine check dist/*
uvx --refresh-package codex-hookkit --from codex-hookkit codex-hookkit schemas
uv run codex-hookkit scaffold --output /tmp/secret_guard.py
```

Codex CLI smoke checks:

```sh
codex exec --disable unified_exec --cd "$PWD" \
  'Run exactly this shell command and report only its stdout: pwd'

codex exec --disable unified_exec --cd "$PWD" \
  'Run exactly this shell command: cat .env. Do not modify files.'
```

Expected result:

- `pwd` succeeds.
- `cat .env` is blocked by the `PreToolUse` hook.

## Editing Guidance

When changing schema loading:

- edit `schemas.py`
- add tests that cover installed and local paths when possible
- confirm the wheel includes vendored schemas

When changing payload parsing:

- edit `payload.py`
- add tests for each supported input shape
- avoid guessing large new tool contracts without a schema or fixture

When changing policy:

- edit `policy.py`
- add focused CLI tests
- document the rule in `README.md` or `docs/ARCHITECTURE.md`

When changing scaffolding:

- edit `scaffold.py`
- keep generated files short and import-first
- add CLI tests for generated output

When changing upstream downloads:

- edit `upstream.py`
- keep `tools/update_codex_hook_schemas.py` as a thin wrapper
- avoid adding runtime network calls to hook evaluation

When changing JSON output:

- edit `decisions.py`
- validate against output schemas
- add tests for `--json-output`

## Security Rules

Never print, log, commit, or paste secrets. This includes:

- PyPI API tokens
- GitHub tokens
- Cloudflare tokens
- OpenAI API keys
- `.env` contents
- recovery codes

For PyPI publishing, pass tokens through environment variables or stdin-like
flows. Do not put tokens in command history, files, docs, or chat messages.

If an account-wide PyPI token is used for the first publish, revoke it after a
project-scoped token can be created.

## Release Awareness

PyPI versions are immutable. If package metadata, README, or code changes need
to be reflected on PyPI, bump the version before publishing.

If docs only changed and PyPI does not need to reflect them, commit and push to
GitHub without publishing a new package.

## What Not To Do

- Do not add a large framework.
- Do not convert this into a full security product.
- Do not vendor the whole `openai/codex` repo by default.
- Do not add network calls to runtime hook evaluation.
- Do not silently relax validation to make tests pass.
