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
src/codex_hookkit/core/*.py
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
uv run python tools/check_generated_models.py
uv run python tools/validate_skills.py
uv run ruff format --check .
uv run ruff check .
uv run pytest -q
rm -rf dist
uv build
uv run twine check dist/*
make check
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

- edit `src/codex_hookkit/core/schemas.py`
- add tests that cover installed and local paths when possible
- confirm the wheel includes vendored schemas

When changing input handling:

- edit the generated-model generator or upstream schemas, then regenerate
- add tests for each supported input model shape
- avoid guessing large new tool contracts without a schema or fixture

When changing policy:

- edit `src/codex_hookkit/core/policy.py`
- add focused CLI tests
- document the rule in `README.md` or `docs/ARCHITECTURE.md`

When changing Codex review hooks:

- edit `src/codex_hookkit/core/review.py` for marker, changed-file, or nested Codex behavior
- keep `PostToolUse` cheap; it should mark pending review, not run review
- keep nested review protected by `CODEX_HOOKKIT_REVIEW_ACTIVE`
- add tests in `tests/test_review.py`
- update `.codex/hooks.json` and `examples/codex_review_hooks.json` together

When changing scaffolding:

- edit `src/codex_hookkit/core/scaffold.py`
- keep generated files short and import-first
- add CLI tests for generated output

When changing upstream downloads:

- edit `src/codex_hookkit/core/upstream.py`
- keep `tools/update_codex_hook_schemas.py` as a thin wrapper
- avoid adding runtime network calls to hook evaluation

When changing JSON output:

- edit the generator in `tools/generate_pydantic_models.py`
- run `uv run python tools/generate_pydantic_models.py`
- keep `src/codex_hookkit/core/inputs.py` generated from vendored input schemas
- keep `src/codex_hookkit/core/outputs.py` generated from vendored output schemas
- keep `src/codex_hookkit/core/decisions.py` as a thin compatibility layer over generated output models
- add tests for `--json-output`
- keep `tests/test_outputs.py` passing so the generator and generated file stay
  in sync

When changing examples:

- keep `examples/` focused on Python hook files and real hook config samples
- do not add JSON payload/output fixtures under `examples/`
- put schema fixture data in tests instead

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
