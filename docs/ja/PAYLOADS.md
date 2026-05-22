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

PreToolUseOutput.allow().write()
```

block する場合は Codex 互換の `exit 2 + stderr` も使えます。

```python
from codex_hookkit import deny

return deny.stderr_exit("Blocked direct secret file access.")
```

ただし、基本の Python examples は `InputModel` で受け、`OutputModel` で返す
構造化パターンを中心にしています。

## Examples

```text
examples/python_hooks/exit_status/*.py
examples/python_hooks/structured_output/*.py
examples/hooks.json
examples/codex_review_hooks.json
```
