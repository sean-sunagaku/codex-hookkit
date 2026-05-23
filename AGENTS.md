# AGENTS.md

このリポジトリでは、英語で考えても構いませんが、ユーザー向けの出力は日本語で行ってください。

## Project Purpose

`codex-hookkit` は Codex hooks を Python で作るための最小 toolkit です。
上流 `openai/codex` の generated hook JSON schema を contract として扱い、
その上に薄い parser、decision helper、default policy、scaffold、補助 CLI を置きます。

## Read Before Editing

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/HOOK_CONTRACTS.md`
- `docs/PAYLOADS.md`
- `docs/AI_GUIDE.md`
- `src/codex_hookkit/*.py`
- `src/codex_hookkit/core/*.py`
- `tests/test_cli.py`

Release や publish を扱う場合は `docs/RELEASE.md` も読んでください。

## Core Rules

- PyPI name は `codex-hookkit`、Python package は `codex_hookkit` のままにする。
- 上流 schema は `third_party/openai-codex-hook-schemas/generated` に vendor snapshot として置く。
- schema JSON は手編集せず、`tools/update_codex_hook_schemas.py` 経由で更新する。
- generated input/output model は `tools/generate_pydantic_models.py` 経由で更新する。
- runtime hook evaluation に不要な network access を入れない。
- default policy は汎用的な secret guard に留め、プロダクト固有ルールを混ぜない。
- core は import-first に保ち、CLI は sample runner / scaffold / schema helper に留める。
- Codex review hook は `PostToolUse` で marker を置き、`Stop` で 1 回だけ実行する。
- Codex review hook の fmt/lint/test は `Stop` 側で必要な場合だけ実行し、formatter は
  `--check` のような非破壊モードを使う。
- nested review は `CODEX_HOOKKIT_REVIEW_ACTIVE=1` で再帰実行を防ぐ。
- hook trust state は `uv run python tools/trust_codex_hooks.py --hooks-path .codex/hooks.json` で `~/.codex/config.toml` に書き込む。
- `exit 2 + stderr` による deny 動作を壊さない。
- 実 `codex exec` の `PreToolUse` guard は `exit 2 + stderr` を正とする。
  `PreToolUseOutput.allow()/deny()` は schema-valid な top-level
  `decision="approve"` / `decision="block"` JSON helper だが、Codex CLI
  v0.133.0 の live `PreToolUse` command hook では structured stdout が
  `PreToolUse Failed` 扱いになる。`.codex/hooks.json` や実運用サンプルを
  `--json-output` に切り替えない。
- JSON output helper は vendored output schema で validation する。
  `PreToolUseOutput.allow()/deny()` は `hookSpecificOutput.permissionDecision`
  ではなく top-level `decision` shape を返すことを保つ。

## Commands

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
```

`make check` runs the generated-model sync check, lint, tests, and package
build in the same order expected by CI.

Codex CLI hook smoke:

```sh
codex exec --disable unified_exec --cd "$PWD" \
  'Run exactly this shell command and report only its stdout: pwd'

codex exec --disable unified_exec --cd "$PWD" \
  'Run exactly this shell command: cat .env. Do not modify files.'
```

`pwd` は通り、`cat .env` は `PreToolUse` hook で block されるのが期待値です。

Hook output / Codex E2E 周りを変更した場合は、通常チェックに加えて次も確認します。

```sh
uv run pytest -q tests/test_outputs.py tests/test_cli.py tests/test_example_hook_config_smoke.py
CODEX_HOOKKIT_RUN_CODEX_EXEC_E2E=1 uv run pytest -q tests/test_codex_exec_e2e.py
uv run python tools/run_codex_exec_e2e.py --dump-events
```

`tests/test_codex_exec_e2e.py` と `tools/run_codex_exec_e2e.py` は、live
`codex exec --json` で通常コマンドが成功し、secret read が
`Command blocked by PreToolUse hook` になることを期待します。
`PreToolUse Failed` は失敗扱いにします。JSON helper は同じ E2E 経路で
top-level `approve` / `block` shape を検証しますが、live hook には使いません。

## Security

token、secret、recovery code、`.env` 内容をチャット、ログ、ファイル、commit に出さないでください。

PyPI publish では token を環境変数経由で渡し、値を表示しないでください。
初回 publish のため account-wide token を使った場合は、project-scoped token 作成後に revoke してください。
