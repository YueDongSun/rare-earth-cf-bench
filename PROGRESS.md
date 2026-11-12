# Progress

| Milestone | Status | Blocked on |
| --- | --- | --- |
| M0 scaffold | in review | Owner review of the scaffold pull request |
| M1 reference-solver scaffolding | not started | `spec/SCIENCE.md` and a reference-solver decision |
| M1 verifier helpers | not started | `spec/TOLERANCES.md` |
| M1 task base image | not started | `spec/TASKS.md` runtime needs for each task family |

`tasks/example_000_smoke` is a format demo. Status in `task.toml`: `draft`. It does not grade crystal-field physics.

## Open science decisions

No reference solver is selected. The M0 brief names PyCrystalField only as a candidate for the owner to accept or reject. No module imports it.

The owner still has to fill:

- `spec/SCIENCE.md#scope`
- `spec/SCIENCE.md#hamiltonian-terms`
- `spec/SCIENCE.md#operator-and-parameter-conventions`
- `spec/SCIENCE.md#site-symmetry-handling`
- `spec/SCIENCE.md#projection-to-effective-spin-hamiltonian`
- `spec/TASKS.md#t1-build-h-cf`
- `spec/TASKS.md#t2-levels`
- `spec/TASKS.md#t3-g-a-q-projection`
- `spec/TASKS.md#t4-parameter-fitting`
- `spec/TASKS.md#t5-host-migration`
- `spec/TOLERANCES.md#tolerances`
- `spec/SOURCES.md#sources`
