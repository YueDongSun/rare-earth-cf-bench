# Agent contract

This file is the working contract for humans and coding agents in `rare-earth-cf-bench`. The owner is Yuedong Sun (@YueDongSun). The owner writes the science. Agents build the engineering around it. `CLAUDE.md` is a symlink to this file.

## Owner standard

- snake_case for every project-owned path and identifier: directories, modules, task ids, scripts, and labels where the platform allows it. Keep external or required names as they are: `AGENTS.md`, `README.md`, `Dockerfile`, `pyproject.toml`, `task.toml`, `.pre-commit-config.yaml`, `.cursor/`, `.claude/`, GitHub template filenames, and the repository name.
- Code comments, docs, ADRs, and agent instructions are English.
- Ordinary commits have no attribution trailers. No `Co-authored-by`, no `Generated-by`, and no "made with" line.
- One mutable owner per resource. One agent owns one issue, one branch, and one worktree at a time. Do not edit, rebase, or push another agent's branch. Preserve concurrent and unknown dirty work. Never force-remove a worktree or a branch.
- Preparation, installation, registration, a successful call, and end-to-end acceptance are separate states. A pull request says which state each claim reached. A claim is not verified without the command output that shows it.
- Never commit credentials, real host inventories, personal chat histories, tokens, or token-bearing URLs. Keep third-party licenses and origin notes when vendoring (`THIRD_PARTY_NOTICES.md`).
- Update `README.md` and the docs a change affects in the same pull request, and only with behaviour that was verified.
- Repository visibility is the owner's decision.

## Who edits what

- `spec/` is owner-only. It holds task-family physics, conventions (units, operator normalisation, basis order, sign conventions), tolerances, gold-data provenance, and the task list.
- `data/gold/` is owner-only. It holds curated literature values with citations.
- Agents do not edit those trees. If a spec point is missing or ambiguous, open a GitHub issue labelled `needs-science-decision`, quote the exact spec line, list the concrete options, and stop work on that piece.
- Do not guess a convention, a tolerance, or a physical constant that the spec does not state.
- Do not set `OWNER_SPEC_EDIT`. That variable is the owner's override for the git hook that guards `spec/` and `data/gold/`.
- `src/`, `tasks/`, `tests/`, `tools/`, and `docs/` are agent territory. Every behaviour traces to a line in `spec/` or to an ADR in `docs/adr/`.

## Layout

`src/cfbench/` is the importable library: `reference/` (solvers, not yet selected), `verify/` (helpers, waiting on tolerances), and `taskfmt/` (the task-format validator). Tasks live in `tasks/<task_id>/`. See `docs/adr/0002-task-format.md`.

Task ids are `<family>_<nnn>_<slug>` in snake_case, for example `cf_t2_001_laf3_er_levels`. Scaffold one with `uv run python tools/new_task.py <task_id>`.

## Code

- Python 3.12, `uv`, and a committed `uv.lock`. No unpinned dependency. Add dependencies with `uv add`, not `pip install`.
- `ruff` lint and format, rule set E, F, W, I, B, UP, SIM, RUF, N, PL, line length 100. `mypy --strict` on `src/`.
- `pytest --strict-markers`. Tests are deterministic, with an explicit seed when a test uses randomness. Slow tests use `@pytest.mark.slow`. `make check` runs them.
- Type hints on `src/`. Docstrings state units and conventions and point at the spec section. There is no numerical code in M0, and `spec/` does not yet state units.
- No defensive programming: no broad `try/except`, no silent fallback, no "just in case" branch, no hand-rolled sanitising beyond the task format. Fail with a clear error.
- No speculative abstraction. Build what the current spec and ADRs need.
- No checksum or sha256 manifests, signing, or certificate bureaucracy.
- No notebooks in `src/` or `tasks/`. Exploratory notebooks go in `notebooks/` with outputs stripped.
- Numerical reference code, when it exists, uses NumPy and SciPy, prefers exact diagonalisation, and documents matrix basis order. No live or paid model call in the test suite.
- No reference solver is selected. PyCrystalField is a candidate named for the owner, not a dependency.

## Commands

- `make setup` installs the environment and the git hooks. Run it first: the hooks call `.venv/bin/python` and fail closed until that interpreter exists.
- `make check` is the bar: format check, lint, type check, pytest, and `make validate`.
- `make validate` checks every task directory, runs its reference solution, and requires a do-nothing run to fail the verifier.

## Hooks

Run `make setup` before an agent session. The hook commands call `.venv/bin/python` and fail closed until the environment exists.

Three layers, same rules:

- Git, via `pre-commit`: format, lint, mypy, nbstripout, YAML and TOML checks, whitespace, end of file, large files (500 KiB, `data/gold/` up to 5 MiB), `tools/check_spec_untouched.py`, and no commits on `main`. Commit messages are Conventional Commits with a required scope: `task`, `verify`, `reference`, `taskfmt`, `tooling`, `docs`, `ci`, `deps`, `spec`. Pre-push refuses `main` and runs `make check`.
- Cursor (`.cursor/hooks.json`) and Claude Code (`.claude/settings.json`): refuse `git push --force`, `git push` to `main`, `git commit --no-verify`, `git reset --hard` on `main`, `OWNER_SPEC_EDIT=`, and `pip install`. Refuse edits under `spec/` and `data/gold/`. Format Python files after an edit. On stop, `make check` has to pass.

Reading `spec/` is allowed. Editing it is not.

## Branches and pull requests

- `main` stays green. Agents do not merge. The owner merges, squash only, after a rebase onto `main`.
- One issue, one branch, one pull request. Branch name: `<agent>/<issue_number>_<slug>`. Comment `claim` and add the label `in-progress` before starting. Stay inside the issue's files. If two issues need the same file, the second waits or the change is split.
- Aim for under 400 changed lines excluding `data/` and lockfiles. A larger diff needs a reason in the pull request body.
- Pull request sections, all required: issue link; spec reference (exact `spec/...#anchor` lines); contract changes (`none` or a list plus an ADR link); local `make check` output; what is not verified; open science questions.
- Update `PROGRESS.md` in the same pull request when a milestone or task status changes.

## Milestone M0

The scaffold is the layout, the hooks, ADRs 0001–0003, the `spec/` skeleton (headings and `TODO(owner)` only), `tools/new_task.py`, `make validate`, and the format demo `tasks/example_000_smoke`. It does not contain crystal-field physics.
