"""Task-format validator, scaffolder, and the format-demo meta-test."""

from __future__ import annotations

from pathlib import Path

import pytest

from cfbench.taskfmt.validate import (
    TaskFormatError,
    parse_task_id,
    validate_task,
    validate_tasks,
)
from tools.new_task import scaffold_task


def test_parse_task_id_accepts_the_documented_shape() -> None:
    parsed = parse_task_id("cf_t2_001_laf3_er_levels")
    assert parsed.family == "cf_t2"
    assert parsed.number == "001"
    assert parsed.slug == "laf3_er_levels"
    parsed_demo = parse_task_id("example_000_smoke")
    assert parsed_demo.family == "example"
    with pytest.raises(TaskFormatError):
        parse_task_id("NotATask")


def test_scaffold_writes_the_contract_and_refuses_to_overwrite(tmp_path: Path) -> None:
    created = scaffold_task("cf_t1_001_placeholder", tmp_path)
    assert (created / "task.toml").is_file()
    assert (created / "instruction.md").is_file()
    assert (created / "environment" / "Dockerfile").is_file()
    assert (created / "solution" / "solve.sh").is_file()
    assert (created / "tests" / "test_outputs.py").is_file()
    with pytest.raises(TaskFormatError, match="already exists"):
        scaffold_task("cf_t1_001_placeholder", tmp_path)


def _fake_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "spec").mkdir(parents=True)
    (root / "spec" / "TASKS.md").write_text("# Tasks\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("[project]\nname = 't'\n", encoding="utf-8")
    return root


def test_placeholder_solution_does_not_pass_validate(tmp_path: Path) -> None:
    root = _fake_repo(tmp_path)
    created = scaffold_task("cf_t1_001_placeholder", root / "tasks")
    with pytest.raises(TaskFormatError, match="exited"):
        validate_task(created)


def test_vacuous_verifier_is_rejected(tmp_path: Path) -> None:
    root = _fake_repo(tmp_path)
    task = root / "tasks" / "example_009_vacuous"
    (task / "environment").mkdir(parents=True)
    (task / "solution").mkdir()
    (task / "tests").mkdir()
    (task / "task.toml").write_text(
        "\n".join(
            (
                'id = "example_009_vacuous"',
                'family = "example"',
                'difficulty = "trivial"',
                'spec_reference = "spec/TASKS.md"',
                'author = "test"',
                'status = "draft"',
                "",
                "[timeouts]",
                "build_sec = 60",
                "agent_sec = 60",
                "verifier_sec = 60",
                "",
            )
        ),
        encoding="utf-8",
    )
    (task / "instruction.md").write_text("demo\n", encoding="utf-8")
    (task / "environment" / "Dockerfile").write_text(
        "FROM python:3.12.7-slim-bookworm\n",
        encoding="utf-8",
    )
    (task / "solution" / "solve.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (task / "tests" / "test_outputs.py").write_text(
        "def test_always() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    with pytest.raises(TaskFormatError, match="do-nothing"):
        validate_task(task)


def _write_task(
    root: Path,
    task_id: str,
    solve: str,
    test: str,
    limits: tuple[int, int],
) -> Path:
    agent_sec, verifier_sec = limits
    task = root / "tasks" / task_id
    (task / "environment").mkdir(parents=True)
    (task / "solution").mkdir()
    (task / "tests").mkdir()
    (task / "task.toml").write_text(
        "\n".join(
            (
                f'id = "{task_id}"',
                'family = "example"',
                'difficulty = "trivial"',
                'spec_reference = "spec/TASKS.md"',
                'author = "test"',
                'status = "draft"',
                "",
                "[timeouts]",
                "build_sec = 60",
                f"agent_sec = {agent_sec}",
                f"verifier_sec = {verifier_sec}",
                "",
            )
        ),
        encoding="utf-8",
    )
    (task / "instruction.md").write_text("demo\n", encoding="utf-8")
    (task / "environment" / "Dockerfile").write_text(
        "FROM python:3.12.7-slim-bookworm\n",
        encoding="utf-8",
    )
    (task / "solution" / "solve.sh").write_text(solve, encoding="utf-8")
    (task / "tests" / "test_outputs.py").write_text(test, encoding="utf-8")
    return task


def test_solution_timeout_is_a_validation_failure(tmp_path: Path) -> None:
    root = _fake_repo(tmp_path)
    task = _write_task(
        root,
        "example_011_slow_solution",
        "#!/bin/sh\nsleep 30\n",
        "def test_ok() -> None:\n    assert True\n",
        (1, 30),
    )
    with pytest.raises(TaskFormatError, match="reference solution exceeded 1s"):
        validate_task(task)


def test_verifier_timeout_is_a_validation_failure(tmp_path: Path) -> None:
    root = _fake_repo(tmp_path)
    task = _write_task(
        root,
        "example_012_slow_verifier",
        "#!/bin/sh\nexit 0\n",
        "import time\n\ndef test_slow() -> None:\n    time.sleep(30)\n",
        (30, 1),
    )
    with pytest.raises(TaskFormatError, match="verifier exceeded 1s"):
        validate_task(task)


def test_missing_file_is_rejected(tmp_path: Path) -> None:
    root = _fake_repo(tmp_path)
    task = root / "tasks" / "example_010_broken"
    task.mkdir(parents=True)
    with pytest.raises(TaskFormatError, match="missing"):
        validate_task(task)


def test_every_task_solution_passes_and_empty_fails() -> None:
    """Meta-test: every committed task passes, and a do-nothing run does not."""
    report = validate_tasks(Path("tasks"))
    assert "example_000_smoke: solution verifier passed" in report
    assert "do-nothing verifier failed as required" in report
