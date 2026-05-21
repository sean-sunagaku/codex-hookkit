# AGENTS.md

このリポジトリでは、英語で考えても構いませんが、ユーザー向けの出力は日本語で行ってください。

## Project Purpose

`codex-hookkit` は Codex hooks を Python で作るための最小 toolkit です。
上流 `openai/codex` の generated hook JSON schema を contract として扱い、
その上に薄い parser、decision helper、default policy、CLI を置きます。

## Read Before Editing

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/HOOK_CONTRACTS.md`
- `docs/AI_GUIDE.md`
- `src/codex_hookkit/*.py`
- `tests/test_cli.py`

Release や publish を扱う場合は `docs/RELEASE.md` も読んでください。

## Core Rules

- PyPI name は `codex-hookkit`、Python package は `codex_hookkit` のままにする。
- 上流 schema は `third_party/openai-codex-hook-schemas/generated` に vendor snapshot として置く。
- schema JSON は手編集せず、`tools/update_codex_hook_schemas.py` 経由で更新する。
- runtime hook evaluation に不要な network access を入れない。
- default policy は汎用的な secret guard に留め、プロダクト固有ルールを混ぜない。
- `exit 2 + stderr` による deny 動作を壊さない。
- JSON output helper は vendored output schema で validation する。

## Commands

```sh
uv sync --dev
uv run pytest -q
uv build
uv run twine check dist/*
```

Codex CLI hook smoke:

```sh
codex exec --disable unified_exec --cd "$PWD" \
  'Run exactly this shell command and report only its stdout: pwd'

codex exec --disable unified_exec --cd "$PWD" \
  'Run exactly this shell command: cat .env. Do not modify files.'
```

`pwd` は通り、`cat .env` は `PreToolUse` hook で block されるのが期待値です。

## Security

token、secret、recovery code、`.env` 内容をチャット、ログ、ファイル、commit に出さないでください。

PyPI publish では token を環境変数経由で渡し、値を表示しないでください。
初回 publish のため account-wide token を使った場合は、project-scoped token 作成後に revoke してください。
