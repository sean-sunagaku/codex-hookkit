# codex-hookkit

`codex-hookkit` は Codex Hooks を Python で作るための小さな toolkit です。
上流 `openai/codex` の generated JSON schema を contract として vendoring し、
その schema から Pydantic の Input / Output model を生成します。

## 基本方針

- Hook の入力は `PreToolUseInput` などの生成 Input model で受ける
- Hook の構造化出力は `PreToolUseOutput` などの生成 Output model で返す
- CLI は sample runner / scaffold / schema helper に留める
- `examples/` は Python hook 実例と実際に使える hook config サンプルに絞る

## インストール

```sh
uv add codex-hookkit
```

## 最小 Hook

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

## Examples

```text
examples/minimal_secret_guard.py
examples/python_hooks/exit_status/*.py
examples/python_hooks/structured_output/*.py
examples/hooks.json
examples/codex_review_hooks.json
```

`structured_output` の Python example は、基本的にすべて
`XxxInput.from_stdin()` で読み、`XxxOutput` で返す形です。

## Hook Config

実際に hook を設定するサンプルは `examples/hooks.json` にあります。
レビュー hook だけを使いたい場合は `examples/codex_review_hooks.json` を見てください。

Codex の hook trust state を `~/.codex/config.toml` に書き込む場合は:

```sh
codex-hookkit trust-hooks --hooks-path .codex/hooks.json
```

このコマンドは、全 command hook について `[hooks.state."..."]` の
`trusted_hash` を upsert します。書き込み前に確認したい場合は `--dry-run` を使います。
この repository には Codex 用の project-local `config.toml` も置いています。
ただし hook trust state は絶対パスを含む machine-local な状態なので commit せず、
上の `trust-hooks` で各環境の `~/.codex/config.toml` に書き込みます。

実際の Codex CLI と hook trust を使った smoke test は次で実行できます。

```sh
make codex-exec-e2e
```

このテストは一時 `CODEX_HOME` に既存の Codex auth をコピーし、hook trust を書き込んだうえで、
`codex exec` が通常コマンドを実行できることと、secret-file guard が sensitive file-read
command を block することを確認します。通常の CI では skip され、
`CODEX_HOOKKIT_RUN_CODEX_EXEC_E2E=1` がある場合だけ実行されます。

## 開発

```sh
uv sync --dev
make check
```

`make check` は input/output model の生成同期、format check、lint、pytest、
build、twine check をまとめて実行します。

## 日本語ドキュメント

- `docs/ja/ARCHITECTURE.md`
- `docs/ja/PAYLOADS.md`
- `docs/ja/HOOK_CONTRACTS.md`
- `docs/ja/AI_GUIDE.md`
- `docs/ja/RELEASE.md`
