"""Scaffold a task directory. The scaffold does not pass ``make validate``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cfbench.taskfmt.validate import TaskFormatError, parse_task_id

_DOCKERFILE = """\
FROM python:3.12.7-slim-bookworm

# Placeholder image. Pin extra packages only when the cited spec section requires them.
# Tests must not use the network.
WORKDIR /workspace
"""

_SOLVE = """\
#!/bin/sh
echo "reference solution is not written" >&2
exit 1
"""

_TEST = '''\
"""Placeholder verifier.

Replace this with deterministic checks. Numeric tolerances must be read by name
from spec/TOLERANCES.md. Do not hard-code a threshold.
"""

import os
from pathlib import Path


def test_placeholder_output() -> None:
    workspace = Path(os.environ["CFBENCH_WORKSPACE"])
    assert (workspace / "TODO_OUTPUT").is_file()
'''

_INSTRUCTION = """\
# Task

TODO: state what the agent under test must produce. Do not describe the hidden
verifier and do not include the answer.

Spec reference: see `spec_reference` in `task.toml`. If that section does not
define the inputs, outputs, and pass criteria, stop and open a
`needs-science-decision` issue.
"""


def scaffold_task(task_id: str, tasks_root: Path) -> Path:
    """Create ``tasks_root/task_id`` and return that path."""
    parsed = parse_task_id(task_id)
    destination = tasks_root / parsed.text
    if destination.exists():
        raise TaskFormatError(f"{destination} already exists")
    (destination / "environment").mkdir(parents=True)
    (destination / "solution").mkdir()
    (destination / "tests").mkdir()
    manifest = "\n".join(
        (
            f'id = "{parsed.text}"',
            f'family = "{parsed.family}"',
            'difficulty = "unspecified"',
            'spec_reference = "spec/TASKS.md#task-families"',
            'author = "unassigned"',
            'status = "draft"',
            "",
            "[timeouts]",
            "build_sec = 60",
            "agent_sec = 60",
            "verifier_sec = 60",
            "",
        )
    )
    (destination / "task.toml").write_text(manifest, encoding="utf-8")
    (destination / "instruction.md").write_text(_INSTRUCTION, encoding="utf-8")
    (destination / "environment" / "Dockerfile").write_text(_DOCKERFILE, encoding="utf-8")
    solve = destination / "solution" / "solve.sh"
    solve.write_text(_SOLVE, encoding="utf-8")
    solve.chmod(0o755)
    (destination / "tests" / "test_outputs.py").write_text(_TEST, encoding="utf-8")
    return destination


def main(argv: list[str] | None = None) -> int:
    """CLI wrapper around ``scaffold_task``."""
    parser = argparse.ArgumentParser(description="Scaffold a task directory.")
    parser.add_argument("task_id")
    parser.add_argument("--tasks-root", type=Path, default=Path("tasks"))
    args = parser.parse_args(argv)
    try:
        destination = scaffold_task(args.task_id, args.tasks_root)
    except TaskFormatError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
