.PHONY: build check check-generated ci fmt lint test

fmt:
	uv run ruff check --fix .
	uv run ruff format .

lint:
	uv run ruff format --check .
	uv run ruff check .

check-generated:
	uv run python tools/generate_pydantic_outputs.py
	git diff --exit-code -- src/codex_hookkit/inputs.py src/codex_hookkit/outputs.py

test:
	uv run pytest -q

build:
	rm -rf dist
	uv build
	uv run twine check dist/*

check: check-generated lint test build

ci: check
