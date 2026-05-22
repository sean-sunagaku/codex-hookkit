# アーキテクチャ

`codex-hookkit` は Codex Hooks を Python で作るための小さな toolkit です。
上流 `openai/codex` の generated schema を source of truth とし、その上に
薄い Python API を置きます。

## モジュール構成

```text
src/codex_hookkit/
  __init__.py       # public import-first API
  core/
    schemas.py      # schema の探索、読み込み、validation
    inputs.py       # schema から生成した Hook input model
    outputs.py      # schema から生成した Hook output model
    decisions.py    # allow / deny helper
  cli/
    main.py         # sample guard runner / schemas / scaffold / init
    _scaffold.py    # CLI 内部の skeleton text
```

`policy`、`trust`、`review`、`upstream update` は stable package API では
ありません。サンプルや運用補助は `examples/` と `tools/` に置きます。

```text
examples/
  secret_guard_policy.py
  python_hooks/
  hooks.json
  codex_review_hooks.json

tools/
  update_codex_hook_schemas.py
  trust_codex_hooks.py
```

## 基本フロー

```text
Codex hook JSON
  -> XxxInput.from_stdin()
  -> schema validation
  -> hook 側の policy logic
  -> XxxOutput.write() または exit status
```

`schemas.py` は残します。これは vendored schema を読み込み、Input/Output
model が Codex の contract に合っているか確認する中核です。

## Public API

hook 利用者は基本的に package root から import します。

```python
from codex_hookkit import PreToolUseInput, PreToolUseOutput
```

public API は次に絞ります。

- 生成 Input model
- 生成 Output model
- `load_schema` / `validate` などの schema helper
- `allow` / `deny` / `Decision`

## Generator

`tools/generate_pydantic_models.py` は `core/inputs.py` と `core/outputs.py` の
両方を生成します。

```sh
uv run python tools/generate_pydantic_models.py
```

生成物は手編集しません。変更する場合は generator か upstream schema を直します。

## Examples

`examples/` には Python hook と実際に使う hook config だけを置きます。
payload/output の JSON fixture は置かず、テスト側で管理します。
