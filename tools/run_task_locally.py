"""Run one task's reference solution and verifier on the local machine."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cfbench.taskfmt.validate import TaskFormatError, validate_task


def main(argv: list[str] | None = None) -> int:
    """Validate a single task id and print the report."""
    parser = argparse.ArgumentParser(description="Validate one task locally.")
    parser.add_argument("task_id")
    parser.add_argument("--tasks-root", type=Path, default=Path("tasks"))
    args = parser.parse_args(argv)
    try:
        report = validate_task(args.tasks_root / args.task_id)
    except TaskFormatError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
