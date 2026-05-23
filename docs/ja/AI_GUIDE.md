# AI Agent Guide

この repo を AI agent が編集するときの要点です。

## 守ること

- 出力は日本語で行う
- schema JSON は手編集しない
- `inputs.py` / `outputs.py` は手編集しない
- generator は `tools/generate_pydantic_models.py`
- examples は Python hook と実 hook config に絞る
- payload/output JSON fixture は examples に置かない
- runtime hook evaluation に network access を入れない

## よく使うコマンド

```sh
uv sync --dev
uv run python tools/check_generated_models.py
uv run python tools/validate_skills.py
uv run ruff format --check .
uv run ruff check .
uv run pytest -q
make check
```

## 変更方針

- input/output model を変える場合は generator と tests を更新する
- policy sample を変える場合は `examples/secret_guard_policy.py` か skeleton と focused test を更新する
- review hook example を変える場合は `examples/python_hooks/codex_review/review_helpers.py` と `tests/test_review.py` を更新する
- Stop 側で fmt/lint/test を走らせる場合は、formatter `--check` など非破壊の check mode に留める
- docs は英語版と日本語版の両方を更新する
