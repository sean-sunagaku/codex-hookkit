# Release

この repo は `uv` で build / publish します。

## Verify

```sh
uv sync --dev
make check
```

`make check` は以下を含みます。

- input/output model の生成同期
- Skill validation
- format check
- lint
- pytest
- build
- twine check

## Publish

PyPI token は表示せず、環境変数経由で渡します。

```sh
UV_PUBLISH_TOKEN="$PYPI_TOKEN" uv publish dist/*
```

PyPI version は immutable なので、publish 前に `pyproject.toml` の version を確認します。

sdist に schema snapshot と Skill が含まれることも確認します。
