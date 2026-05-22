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
