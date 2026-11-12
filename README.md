# rare-earth-cf-bench

Execution-graded benchmark for rare-earth crystal-field Hamiltonians. A graded agent builds the free-ion, crystal-field, Zeeman, and hyperfine terms for a lanthanide site, diagonalises them, and projects a low-energy subspace onto an effective spin Hamiltonian (g, A, and Q tensors). Scores compare that work with a reference solver and with curated literature values.

Those definitions are not in this scaffold. They belong in [`spec/`](spec/), which the owner fills. Agents do not edit `spec/` or `data/gold/`.

## Status

| Milestone | Status |
| --- | --- |
| M0 scaffold | in review |
| M1 reference solver, verifier helpers, task image | not started |

`tasks/example_000_smoke` is a format demo with no crystal-field content. Detail is in [PROGRESS.md](PROGRESS.md).

## Quickstart

```bash
make setup && make check
```

Python 3.12 and [uv](https://docs.astral.sh/uv/) are required. `make setup` creates the environment and installs the git hooks.

## Add a task

```bash
uv run python tools/new_task.py <family>_<nnn>_<slug>
```

Write `instruction.md`, `solution/solve.sh`, and `tests/test_outputs.py` from the spec section cited in `task.toml`. Do not invent a convention or a tolerance. `make validate` passes only when the reference solution passes its verifier and a do-nothing run fails it.

## Contract

[AGENTS.md](AGENTS.md) is the agent and contributor contract. Scientific scope, conventions, tolerances, and sources are in [`spec/`](spec/).
