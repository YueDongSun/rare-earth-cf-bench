"""Task-format validator.

The directory contract is ``docs/adr/0002-task-format.md``. This package does
not judge crystal-field results. Numeric tolerances, once the owner writes
them, are named in ``spec/TOLERANCES.md``.
"""

from cfbench.taskfmt.validate import (
    TaskFormatError,
    TaskId,
    parse_task_id,
    validate_task,
    validate_tasks,
)

__all__ = [
    "TaskFormatError",
    "TaskId",
    "parse_task_id",
    "validate_task",
    "validate_tasks",
]
