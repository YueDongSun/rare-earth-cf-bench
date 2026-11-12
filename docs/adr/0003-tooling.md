# 3. Tooling

Date: 2026-11-12

## Status

Accepted

## Context

Local `make check` is the source of truth. Git hooks, Cursor hooks, and Claude Code hooks have to agree, and several agents will run them. The repository has no numerical reference code yet, so it has no numerical library yet.

## Decision

- Python 3.12. Dependencies are declared in `pyproject.toml` and pinned in `uv.lock`. `uv sync` is how the environment is installed. `pip install` is refused by the agent shell hooks.
- `ruff` formats and lints with rule set E, F, W, I, B, UP, SIM, RUF, N, PL and line length 100. The pre-commit lint hook does not pass `--fix`.
- `mypy --strict` runs on `src/`.
- `pytest --strict-markers` runs the tests in `tests/`. Slow tests use the `slow` marker and are included in `make check`.
- `make check` is `ruff format --check`, `ruff check`, `mypy`, `pytest` (including slow tests), and `make validate`.
- Git hooks are installed by `make setup` through `pre-commit`, on the pre-commit, commit-msg, and pre-push stages. The commit-msg hook requires Conventional Commits with a scope from `task`, `verify`, `reference`, `taskfmt`, `tooling`, `docs`, `ci`, `deps`, `spec`. The pre-push hook refuses a push whose current branch or remote ref is `main`, then runs `make check`. `pre-commit` exposes the remote ref as `PRE_COMMIT_REMOTE_BRANCH`.
- Cursor hooks live in `.cursor/hooks.json`. Claude Code hooks live in `.claude/settings.json`. Both call the Python scripts in `tools/hooks/`.
- Notebooks are not part of `src/` or `tasks/`. `nbstripout` is hooked so a future notebook under `notebooks/` does not keep outputs.
- No checksum manifest, signing step, or live model call is part of the suite.
- NumPy and SciPy are the libraries for numerical reference code when that code exists. M0 does not depend on them because there is no numerical code.
- No reference solver is selected. The M0 brief names PyCrystalField only as a candidate for the owner to accept or reject. Nothing in the package imports it.

## Consequences

A machine that has not run `make setup` has no git hooks and no `.venv`. Agent hooks call `.venv/bin/python`, so they start working after setup. GitHub Actions runs the same `make check`. If Actions is unavailable, the local `make check` output in the pull request is the record.
