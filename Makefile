.PHONY: build check check-generated ci fmt lint test

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

build:
	rm -rf dist
	uv build
	uv run twine check dist/*

check: check-generated lint test build

ci: check
