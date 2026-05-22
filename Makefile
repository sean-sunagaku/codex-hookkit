.PHONY: build check check-generated ci codex-exec-e2e fmt lint test

fmt:
	uv run ruff check --fix .
	uv run ruff format .

lint:
	uv run ruff format --check .
	uv run ruff check .

check-generated:
	uv run python tools/check_generated_models.py

test:
	uv run pytest -q

codex-exec-e2e:
	CODEX_HOOKKIT_RUN_CODEX_EXEC_E2E=1 uv run pytest -q tests/test_codex_exec_e2e.py

build:
	rm -rf dist
	uv build
	uv run twine check dist/*

check: check-generated lint test build

ci: check
