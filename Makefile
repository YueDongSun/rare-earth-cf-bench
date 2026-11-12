.PHONY: setup fmt fmt-check lint type test validate check

export PATH := $(HOME)/.local/bin:$(PATH)

setup:
	uv sync --frozen
	uv run pre-commit install --install-hooks --hook-type pre-commit --hook-type commit-msg --hook-type pre-push

fmt:
	uv run ruff format .

fmt-check:
	uv run ruff format --check .

lint:
	uv run ruff check .

type:
	uv run mypy src

test:
	uv run pytest

validate:
	uv run python -m cfbench.taskfmt

check: fmt-check lint type test validate
