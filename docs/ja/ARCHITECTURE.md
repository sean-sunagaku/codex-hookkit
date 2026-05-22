# アーキテクチャ

`codex-hookkit` は Codex Hooks を Python で作るための小さなライブラリです。
上流 `openai/codex` の generated schema を source of truth とし、その上に
薄い Python API を置きます。

## モジュール構成

```text
src/codex_hookkit/
  schemas.py      # schema の探索、読み込み、validation
  inputs.py       # schema から生成した Hook input model
  outputs.py      # schema から生成した Hook output model
  decisions.py    # allow / deny 互換 helper
  policy.py       # 最小の SecretPolicy
  review.py       # PostToolUse/Stop を使う Codex review hook
  trust.py        # Codex hook trust state 書き込み
  upstream.py     # schema snapshot downloader
  scaffold.py     # hook skeleton / config 生成
  cli.py          # sample runner と補助 CLI
```

## 基本フロー

```text
Codex hook JSON
  -> XxxInput.from_stdin()
  -> schema validation
  -> policy / hook logic
  -> XxxOutput.write() または exit status
```

基本は `InputModel` で受けて `OutputModel` で返します。payload の共通
wrapper は持たず、hook ごとの生成 model をそのまま扱います。

## Generator

`tools/generate_pydantic_models.py` は `inputs.py` と `outputs.py` の両方を
生成します。

```sh
uv run python tools/generate_pydantic_models.py
```

生成物は手編集しません。変更する場合は generator か upstream schema を直します。

## Examples

`examples/` には Python hook と実際に使う hook config だけを置きます。
payload/output の JSON fixture は置かず、テスト側で管理します。
