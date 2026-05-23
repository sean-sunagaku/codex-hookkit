# Hook Contracts

Hook contract は上流 `openai/codex` の generated schema を正とします。

- input schema: `*.command.input.schema.json`
- output schema: `*.command.output.schema.json`

`codex-hookkit` は schema snapshot を `third_party/openai-codex-hook-schemas/`
に vendoring し、そこから Pydantic model を生成します。

## 固定されるもの

- Hook event name
- stdin で渡される input JSON の形
- stdout に返せる structured output JSON の形
- enum 値

## Hook 側で決めるもの

- どの policy を適用するか
- block する条件
- `exit 2 + stderr` を使うか、structured output を使うか
- deny message

実運用の `PreToolUse` guard は `exit 2 + stderr` を優先します。JSON output が
必要な場合、`PreToolUseOutput.deny()` は schema-valid な top-level
`decision="block"` / `reason` 形を返します。ただし `codex exec` v0.133.0 では
実 `PreToolUse` hook の structured stdout は `PreToolUse Failed` 扱いになります。
