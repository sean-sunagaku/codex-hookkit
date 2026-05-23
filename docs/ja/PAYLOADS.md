# Payload と Output

Codex Hook は標準入力で 1 つの JSON object を受け取ります。

```python
from codex_hookkit import PreToolUseInput

payload = PreToolUseInput.from_stdin()
```

入力の形は上流 Codex schema で固定です。`codex-hookkit` はその schema から
`PreToolUseInput`、`PermissionRequestInput` などを生成します。

構造化出力を返す場合も同じく生成 model を使います。

```python
from codex_hookkit import PreToolUseOutput

PreToolUseOutput.deny("Blocked direct secret file access.").write()
```

`PreToolUseOutput.deny()` は schema-valid な top-level `decision="block"` /
`reason` 形を返します。ただし `codex exec` v0.133.0 の実 hook では
structured stdout が `PreToolUse Failed` 扱いになるため、`PreToolUse` で
block する実運用 hook は次の `exit 2 + stderr` を優先してください。

block する場合は Codex 互換の `exit 2 + stderr` も使えます。

```python
from codex_hookkit import deny

return deny.stderr_exit("Blocked direct secret file access.")
```

基本の Python examples は `exit_status` と `structured_output` の両方を置いています。
実 CLI smoke では `PreToolUse` は `exit_status` 版を使います。

## Examples

```text
examples/python_hooks/exit_status/*.py
examples/python_hooks/structured_output/*.py
examples/hooks.json
examples/codex_review_hooks.json
```
