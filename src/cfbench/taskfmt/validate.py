"""Validate Terminal-Bench style task directories.

The workspace directory is the path in ``CFBENCH_WORKSPACE``. Science tasks
take numeric tolerances by name from ``spec/TOLERANCES.md``; this module does
not define any.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path

_TASK_ID = re.compile(
    r"^(?P<family>[a-z][a-z0-9]*(?:_[a-z][a-z0-9]*)*)"
    r"_(?P<number>[0-9]{3})"
    r"_(?P<slug>[a-z][a-z0-9]*(?:_[a-z][a-z0-9]*)*)$"
)
_STATUSES = frozenset({"draft", "ready"})
_REQUIRED_FILES = (
    "task.toml",
    "instruction.md",
    "environment/Dockerfile",
    "solution/solve.sh",
    "tests/test_outputs.py",
)


class TaskFormatError(Exception):
    """A task directory breaks the format contract in ADR 0002."""


@dataclass(frozen=True)
class TaskId:
    """Parsed ``<family>_<nnn>_<slug>`` task id."""

    family: str
    number: str
    slug: str

    @property
    def text(self) -> str:
        """Return the id as a single snake_case string."""
        return f"{self.family}_{self.number}_{self.slug}"


@dataclass(frozen=True)
class Timeouts:
    """Per-stage time limits from ``task.toml``, in seconds."""

    build_sec: int
    agent_sec: int
    verifier_sec: int


@dataclass(frozen=True)
class TaskManifest:
    """Required fields of ``task.toml``."""

    id: str
    family: str
    difficulty: str
    spec_reference: str
    author: str
    status: str
    timeouts: Timeouts


@dataclass(frozen=True)
class VerifierRun:
    """One pytest invocation of a task verifier."""

    returncode: int
    output: str


def parse_task_id(value: str) -> TaskId:
    """Parse a task id. Raise ``TaskFormatError`` when the shape is wrong."""
    match = _TASK_ID.fullmatch(value)
    if match is None:
        raise TaskFormatError(f"task id must be <family>_<nnn>_<slug> in snake_case, got {value!r}")
    return TaskId(
        family=match.group("family"),
        number=match.group("number"),
        slug=match.group("slug"),
    )


def validate_tasks(tasks_root: Path) -> str:
    """Validate every task directory under ``tasks_root``."""
    if not tasks_root.is_dir():
        raise TaskFormatError(f"tasks root is not a directory: {tasks_root}")
    task_dirs = sorted(
        path for path in tasks_root.iterdir() if path.is_dir() and not path.name.startswith(".")
    )
    if not task_dirs:
        raise TaskFormatError(f"no tasks under {tasks_root}")
    return "\n".join(validate_task(task_dir) for task_dir in task_dirs)


def validate_task(task_dir: Path) -> str:
    """Check structure, require the solution to pass, and require do-nothing to fail."""
    load_manifest(task_dir)
    solved = _run_with_solution(task_dir)
    if solved.returncode != 0:
        raise TaskFormatError(
            f"{task_dir.name}: reference solution failed its verifier\n{solved.output}"
        )
    empty = run_empty_verifier(task_dir)
    if empty.returncode == 0:
        raise TaskFormatError(f"{task_dir.name}: do-nothing run passed the verifier")
    return "\n".join(
        (
            f"{task_dir.name}: structure ok",
            f"{task_dir.name}: solution verifier passed",
            f"{task_dir.name}: do-nothing verifier failed as required",
            empty.output.rstrip(),
        )
    )


def run_empty_verifier(task_dir: Path) -> VerifierRun:
    """Run the verifier in an empty workspace, without the reference solution."""
    load_manifest(task_dir)
    with tempfile.TemporaryDirectory(prefix="cfbench-empty-") as empty:
        return _verifier(task_dir, Path(empty))


def load_manifest(task_dir: Path) -> TaskManifest:
    """Read ``task.toml`` and check the directory shape. No physics is interpreted."""
    for relative in _REQUIRED_FILES:
        _require_nonempty(task_dir, relative)
    _require_dockerfile(task_dir / "environment" / "Dockerfile")
    manifest = _parse_manifest(task_dir / "task.toml")
    parsed = parse_task_id(manifest.id)
    if task_dir.name != manifest.id:
        raise TaskFormatError(f"{task_dir.name}: directory name must equal id {manifest.id!r}")
    if manifest.family != parsed.family:
        raise TaskFormatError(
            f"{manifest.id}: family {manifest.family!r} does not match the id family "
            f"{parsed.family!r}"
        )
    if manifest.status not in _STATUSES:
        raise TaskFormatError(f"{manifest.id}: status must be draft or ready")
    _require_reference_file(manifest.spec_reference, _find_repo_root(task_dir))
    return manifest


def _run_with_solution(task_dir: Path) -> VerifierRun:
    with tempfile.TemporaryDirectory(prefix="cfbench-sol-") as solved_name:
        workspace = Path(solved_name)
        _run_solution(task_dir, workspace)
        return _verifier(task_dir, workspace)


def _run_solution(task_dir: Path, workspace: Path) -> None:
    script = (task_dir / "solution" / "solve.sh").resolve()
    completed = subprocess.run(
        ["bash", str(script)],
        cwd=workspace,
        env=_workspace_env(workspace),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise TaskFormatError(
            f"{task_dir.name}: reference solution exited {completed.returncode}\n"
            f"{completed.stdout}{completed.stderr}"
        )


def _verifier(task_dir: Path, workspace: Path) -> VerifierRun:
    test_file = (task_dir / "tests" / "test_outputs.py").resolve()
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(test_file)],
        cwd=workspace,
        env=_workspace_env(workspace),
        capture_output=True,
        text=True,
        check=False,
    )
    return VerifierRun(
        returncode=completed.returncode,
        output=completed.stdout + completed.stderr,
    )


def _workspace_env(workspace: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["CFBENCH_WORKSPACE"] = str(workspace)
    return env


def _require_nonempty(task_dir: Path, relative: str) -> None:
    path = task_dir / relative
    if not path.is_file():
        raise TaskFormatError(f"{task_dir.name}: missing {relative}")
    if path.stat().st_size == 0:
        raise TaskFormatError(f"{task_dir.name}: {relative} is empty")


def _require_dockerfile(path: Path) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("FROM "):
            return
        raise TaskFormatError(f"{path}: the first instruction must be FROM")
    raise TaskFormatError(f"{path}: missing FROM")


def _parse_manifest(path: Path) -> TaskManifest:
    table = _as_table(tomllib.loads(path.read_text(encoding="utf-8")), str(path))
    timeouts = _as_table(table.get("timeouts"), f"{path} timeouts")
    where = str(path)
    return TaskManifest(
        id=_require_str(table, "id", where),
        family=_require_str(table, "family", where),
        difficulty=_require_str(table, "difficulty", where),
        spec_reference=_require_str(table, "spec_reference", where),
        author=_require_str(table, "author", where),
        status=_require_str(table, "status", where),
        timeouts=Timeouts(
            build_sec=_require_positive_int(timeouts, "build_sec", where),
            agent_sec=_require_positive_int(timeouts, "agent_sec", where),
            verifier_sec=_require_positive_int(timeouts, "verifier_sec", where),
        ),
    )


def _require_reference_file(reference: str, repo_root: Path) -> None:
    path_part = reference.split("#", 1)[0]
    if path_part == "" or not (repo_root / path_part).is_file():
        raise TaskFormatError(f"spec_reference file does not exist: {path_part}")


def _as_table(value: object, where: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TaskFormatError(f"{where} must be a table")
    table: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise TaskFormatError(f"{where} has a non-string key")
        table[key] = item
    return table


def _require_str(table: dict[str, object], key: str, where: str) -> str:
    if key not in table:
        raise TaskFormatError(f"{where} missing {key}")
    value = table[key]
    if not isinstance(value, str) or value == "":
        raise TaskFormatError(f"{where} {key} must be a non-empty string")
    return value


def _require_positive_int(table: dict[str, object], key: str, where: str) -> int:
    if key not in table:
        raise TaskFormatError(f"{where} missing {key}")
    value = table[key]
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise TaskFormatError(f"{where} {key} must be a positive integer")
    return value


def _find_repo_root(start: Path) -> Path:
    for candidate in (start.resolve(), *start.resolve().parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise TaskFormatError(f"no pyproject.toml above {start}")


def main(argv: list[str] | None = None) -> int:
    """CLI entry for ``python -m cfbench.taskfmt.validate``."""
    parser = argparse.ArgumentParser(description="Validate task directories.")
    parser.add_argument("--tasks-root", type=Path, default=Path("tasks"))
    parser.add_argument("--task", default=None, help="Validate one task id.")
    parser.add_argument(
        "--empty",
        action="store_true",
        help="Run only the do-nothing verifier and return its exit code.",
    )
    args = parser.parse_args(argv)
    if args.empty:
        if args.task is None:
            print("--empty requires --task", file=sys.stderr)
            return 2
        try:
            result = run_empty_verifier(args.tasks_root / args.task)
        except TaskFormatError as exc:
            print(exc, file=sys.stderr)
            return 1
        sys.stdout.write(result.output)
        return result.returncode
    try:
        if args.task is None:
            report = validate_tasks(args.tasks_root)
        else:
            report = validate_task(args.tasks_root / args.task)
    except TaskFormatError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
