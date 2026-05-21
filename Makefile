.PHONY: build check check-generated fmt lint test

fmt:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff format --check .
	uv run ruff check .

check-generated:
	uv run python tools/generate_pydantic_outputs.py
	git diff --exit-code -- src/codex_hookkit/outputs.py

test:
	uv run pytest -q

build:
	rm -rf dist
	uv build
	uv run twine check dist/*

check: check-generated lint test build
