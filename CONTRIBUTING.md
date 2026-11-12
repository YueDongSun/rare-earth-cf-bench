# Contributing

The owner (Yuedong Sun, @YueDongSun) merges to `main`. Agents do not merge. `AGENTS.md` is the full contract; this file is the branch and review procedure.

## Setup

```bash
make setup && make check
```

`make setup` creates the uv environment and installs the pre-commit, commit-msg, and pre-push hooks. After that, a commit on `main` is refused, a staged change under `spec/` or `data/gold/` is refused, and a non-conventional commit message is refused.

The owner may set `OWNER_SPEC_EDIT=1` to commit scientific edits. Agents must not set that variable. Open a `needs-science-decision` issue instead.

## Branches

One issue, one branch, one pull request.

```text
<agent>/<issue_number>_<slug>
```

Comment `claim` on the issue and add the label `in-progress` before editing. Do not edit, rebase, or push a branch another agent owns. Do not force-push, and do not delete someone else's worktree or branch.

## Commits

Conventional Commits with a required scope:

```text
<type>(<scope>): <description>
```

Scopes: `task`, `verify`, `reference`, `taskfmt`, `tooling`, `docs`, `ci`, `deps`, `spec`.

Example: `feat(task): add cf_t2_001_laf3_er_levels`.

No `Co-authored-by`, `Generated-by`, or "made with" trailer.

## Pull requests

Use the pull request template. Rebase on `main` before review. Squash merge is the owner's action.

A diff over 400 lines, excluding `data/` and lockfiles, needs a reason in the body. The M0 scaffold is one of those diffs: the hooks have to land together or they do not guard anything.

A change to the task format, the public API, or the directory layout needs a new file in `docs/adr/`. Update `PROGRESS.md` when a milestone or task status changes.

## Science

Do not put a guessed convention, tolerance, or literature value in `spec/`, `data/gold/`, or the verifiers. Quote the spec line, list the options, and wait for the owner.
