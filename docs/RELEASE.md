# Release

This repository uses `uv` for local development, build, and publish workflows.

## Preconditions

- You are on a clean working tree.
- Tests pass locally.
- The version in `pyproject.toml` is the version you intend to publish.
- If exporting `__version__`, keep it aligned with `pyproject.toml`.
- Bundled skills validate with `tools/validate_skills.py`.
- PyPI credentials are available without printing them.

## Verify

```sh
uv sync --dev
uv run python tools/check_generated_models.py
uv run python tools/validate_skills.py
uv run ruff format --check .
uv run ruff check .
uv run pytest -q
rm -rf dist
uv build
uv run twine check dist/*
```

Equivalent local gate:

```sh
make check
```

Optional package-content check:

```sh
python -m tarfile -l dist/codex_hookkit-*.tar.gz | grep openai-codex-hook-schemas
python -m tarfile -l dist/codex_hookkit-*.tar.gz | grep skills/codex-hookkit
python -m zipfile -l dist/codex_hookkit-*.whl | grep openai-codex-hook-schemas
python -m zipfile -l dist/codex_hookkit-*.whl | grep codex_hookkit/skills/codex-hookkit
```

## Publish

Use `uv publish` with a token passed through the environment.

```sh
UV_PUBLISH_TOKEN="$PYPI_TOKEN" uv publish dist/*
```

Do not echo the token. Do not write it to `.pypirc`. Do not paste it into logs.

## First Project Publish

For the first upload of a new PyPI project, PyPI cannot create a project-scoped
token yet. Use an account-wide token only long enough to create the project.

After the first release:

1. Create a project-scoped token for `codex-hookkit`.
2. Revoke the temporary account-wide token.
3. Use only the project-scoped token for later releases.

## Post-Publish Checks

```sh
python - <<'PY'
import json, urllib.request
with urllib.request.urlopen("https://pypi.org/pypi/codex-hookkit/json", timeout=20) as r:
    data = json.load(r)
print(data["info"]["name"], data["info"]["version"])
PY

uvx --refresh-package codex-hookkit --from codex-hookkit codex-hookkit schemas
uvx --refresh-package codex-hookkit --from codex-hookkit codex-hookkit scaffold
```

Confirm the PyPI page:

```text
https://pypi.org/project/codex-hookkit/
```

## GitHub

Commit and push after verification:

```sh
git status -sb
git add <paths>
git diff --cached --stat
git commit -m "Release <version>"
git push
```

If the release includes only docs that do not need to update PyPI metadata, a
GitHub push is enough.
