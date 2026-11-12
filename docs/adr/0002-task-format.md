# 2. Task format

Date: 2026-11-12

## Status

Accepted

## Context

Tasks are graded the way a Terminal-Bench task is graded: an instruction, an environment, a reference solution, and a hidden verifier. `make validate` has to reject a task whose verifier passes when the solution does nothing.

The owner has not filled `spec/TASKS.md` or `spec/TOLERANCES.md`. Milestone M0 still needs one task directory so the harness can be exercised.

## Decision

Each `tasks/<task_id>/` directory contains:

- `task.toml`: `id`, `family`, `difficulty`, `spec_reference`, `author`, `status` (`draft` or `ready`), and `[timeouts]` with positive integer seconds `build_sec`, `agent_sec`, `verifier_sec`.
- `instruction.md`: what the agent under test sees. No hidden-test details and no answers.
- `environment/Dockerfile`: a pinned base image. Tests do not use the network.
- `solution/solve.sh`: the reference solution.
- `tests/test_outputs.py`: the hidden verifier, run with pytest.

Task ids match `<family>_<nnn>_<slug>` in snake_case. The directory name equals `id`. `family` in `task.toml` equals the family parsed from that id. `spec_reference` is a repository path, optionally followed by `#anchor`, and the path must exist.

The local harness sets `CFBENCH_WORKSPACE` to an empty directory, runs `solution/solve.sh` with that variable set, then runs the verifier with the same variable. The do-nothing run sets `CFBENCH_WORKSPACE` to a fresh empty directory and runs the verifier without the solution. `make validate` passes a task only when the solution run's verifier exits 0 and the do-nothing run's verifier exits non-zero.

`tasks/example_000_smoke` is a format demo. Its status is `draft`. It checks that the solution wrote the marker file named in its instruction. That marker is not a physical quantity. Science tasks must not copy this pattern: their numeric checks take tolerances by name from `spec/TOLERANCES.md`, which the owner has not filled.

`tools/new_task.py` creates the same files with the solution exiting non-zero. A scaffold is not a passing task.

## Consequences

`src/cfbench/taskfmt/` enforces this contract and nothing about crystal-field physics. A science task cannot be marked ready by this milestone's validator alone; the owner still has to define inputs, outputs, and tolerances in `spec/`.
