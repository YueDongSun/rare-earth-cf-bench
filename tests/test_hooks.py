"""Unit tests for the git, Cursor, and Claude Code hook scripts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tools.hooks.policy import (
    CHECK_OUTPUT_TAIL,
    DEFAULT_MAX_BYTES,
    GOLD_MAX_BYTES,
    OWNER_ONLY_MESSAGE,
    claude_pretool,
    commit_message_error,
    cursor_permission,
    is_owner_only,
    large_file_error,
    push_refusal,
    shell_denial,
    should_run_check,
    size_limit_bytes,
    stop_block,
)

_REPO = Path(__file__).resolve().parents[1]
_CURSOR_DENY_EXIT = 2


def _run_script(
    script: str,
    payload: dict[str, object] | None = None,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(_REPO / script)]
    if args is not None:
        command.extend(args)
    return subprocess.run(
        command,
        input=None if payload is None else json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=_REPO,
        env=env,
        check=False,
    )


def test_owner_only_paths(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    assert is_owner_only("spec/SCIENCE.md")
    assert is_owner_only("./spec/SCIENCE.md")
    assert is_owner_only("data/gold/values.csv")
    assert is_owner_only(str(root / "spec" / "SCIENCE.md"), root)
    assert is_owner_only("tools/../spec/SCIENCE.md", root)
    assert is_owner_only(str(root / "tools" / ".." / "data" / "gold" / "values.csv"), root)
    assert not is_owner_only("spec/../src/cfbench/__init__.py", root)
    assert not is_owner_only("data/gold/../other/values.csv", root)
    assert not is_owner_only(str(tmp_path / "spec" / "SCIENCE.md"), root)
    assert not is_owner_only("src/cfbench/taskfmt/validate.py")
    assert not is_owner_only("data/other/values.csv")
    assert not is_owner_only("specs/SCIENCE.md")


def test_size_limits() -> None:
    assert DEFAULT_MAX_BYTES == 500 * 1024
    assert GOLD_MAX_BYTES == 5 * 1024 * 1024
    assert size_limit_bytes("src/cfbench/__init__.py") == DEFAULT_MAX_BYTES
    assert size_limit_bytes("data/gold/values.csv") == GOLD_MAX_BYTES


def test_large_file_error_respects_gold_ceiling(tmp_path: Path) -> None:
    repo = tmp_path
    (repo / "pyproject.toml").write_text("", encoding="utf-8")
    source = repo / "src" / "mod.py"
    source.parent.mkdir()
    source.write_bytes(b"x" * (DEFAULT_MAX_BYTES + 1))
    assert large_file_error(source, repo) is not None
    at_limit = repo / "src" / "edge.py"
    at_limit.write_bytes(b"x" * DEFAULT_MAX_BYTES)
    assert large_file_error(at_limit, repo) is None
    gold = repo / "data" / "gold" / "values.csv"
    gold.parent.mkdir(parents=True)
    gold.write_bytes(b"x" * (DEFAULT_MAX_BYTES + 1))
    assert large_file_error(gold, repo) is None
    assert large_file_error(repo / "src" / "missing.py", repo) is None


@pytest.mark.parametrize(
    ("message", "ok"),
    [
        ("chore(tooling): M0 scaffold", True),
        ("feat(task): add cf-t2-001", True),
        ("fix(verify): reject a vacuous verifier\n\nBody is allowed.\n", True),
        ("update stuff", False),
        ("feat: missing scope", False),
        ("feat(physics): not a scope", False),
        ("chore(tooling): M0 scaffold\n\nCo-authored-by: Bot <bot@example.com>", False),
        ("chore(tooling): M0 scaffold\n\nGenerated-by: tool", False),
        ("chore(tooling): M0 scaffold\n\nMade with Cursor", False),
        ("", False),
    ],
)
def test_commit_message_rules(message: str, ok: bool) -> None:
    error = commit_message_error(message)
    assert (error is None) is ok


def test_commit_message_ignores_git_comments() -> None:
    text = "chore(tooling): M0 scaffold\n\n# comment\n"
    assert commit_message_error(text) is None


@pytest.mark.parametrize(
    ("command", "branch", "denied"),
    [
        ("git push --force", "feature", True),
        ("git push --force-with-lease origin feature", "feature", True),
        ("git push -f origin feature", "feature", True),
        ("git push origin main", "feature", True),
        ("git push origin HEAD:main", "feature", True),
        ("git commit --no-verify -m 'chore(tooling): x'", "feature", True),
        ("git reset --hard", "main", True),
        ("git reset --hard", "cursor/m0_scaffold", False),
        ("git reset --hard origin/main", "cursor/m0_scaffold", True),
        ("git reset --hard feature", "main", False),
        ("OWNER_SPEC_EDIT=1 git status", "feature", True),
        ("pip install numpy", "feature", True),
        ("python -m pip install numpy", "feature", True),
        ("uv add numpy", "feature", False),
        ("git status", "feature", False),
        ("git push origin cursor/m0_scaffold", "feature", False),
        ("echo ok && git push --force", "feature", True),
    ],
)
def test_shell_denial(command: str, branch: str, denied: bool) -> None:
    assert (shell_denial(command, branch) is not None) is denied


def test_push_refusal() -> None:
    assert push_refusal("main", None, "") == "refusing push to main"
    assert push_refusal("feature", "refs/heads/main", "") == "refusing push to main"
    stdin = "refs/heads/feature abc refs/heads/main def\n"
    assert push_refusal("feature", None, stdin) == "refusing push to main"
    assert push_refusal("feature", "refs/heads/feature", "") is None


def test_stop_block_shapes() -> None:
    cursor = stop_block("stop", "lint failed")
    claude = stop_block("Stop", "lint failed")
    assert "followup_message" in cursor
    assert claude["decision"] == "block"
    assert should_run_check({"status": "completed"})
    assert not should_run_check({"status": "aborted"})
    assert not should_run_check({"status": "error"})
    assert CHECK_OUTPUT_TAIL > 0


def test_permission_objects() -> None:
    assert cursor_permission(None) == {"permission": "allow"}
    denied = cursor_permission("no")
    assert denied["permission"] == "deny"
    assert claude_pretool(None) is None
    blocked = claude_pretool("no")
    assert blocked is not None
    specific = blocked["hookSpecificOutput"]
    assert isinstance(specific, dict)
    assert specific["permissionDecision"] == "deny"


def test_check_spec_untouched_rejects_and_honours_owner_override(tmp_path: Path) -> None:
    rejected = _run_script("tools/check_spec_untouched.py", args=["spec/SCIENCE.md"])
    assert rejected.returncode == 1
    assert OWNER_ONLY_MESSAGE in rejected.stderr
    allowed_other = _run_script("tools/check_spec_untouched.py", args=["src/cfbench/__init__.py"])
    assert allowed_other.returncode == 0
    env = dict(os.environ)
    env["OWNER_SPEC_EDIT"] = "1"
    override = _run_script("tools/check_spec_untouched.py", args=["spec/SCIENCE.md"], env=env)
    assert override.returncode == 0
    assert tmp_path.is_dir()


def test_commit_msg_script(tmp_path: Path) -> None:
    good = tmp_path / "good.txt"
    good.write_text("chore(tooling): M0 scaffold\n", encoding="utf-8")
    bad = tmp_path / "bad.txt"
    bad.write_text("update stuff\n", encoding="utf-8")
    assert _run_script("tools/hooks/commit_msg.py", args=[str(good)]).returncode == 0
    rejected = _run_script("tools/hooks/commit_msg.py", args=[str(bad)])
    assert rejected.returncode == 1


def test_shell_guard_cursor_and_claude() -> None:
    cursor = _run_script(
        "tools/hooks/shell_guard.py",
        {"hook_event_name": "beforeShellExecution", "command": "pip install numpy"},
    )
    assert cursor.returncode == 0
    body = json.loads(cursor.stdout)
    assert body["permission"] == "deny"
    claude = _run_script(
        "tools/hooks/shell_guard.py",
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "git status"},
        },
    )
    assert claude.returncode == 0
    assert claude.stdout.strip() == ""


def test_read_guard_allows_spec() -> None:
    completed = _run_script(
        "tools/hooks/read_guard.py",
        {"file_path": str(_REPO / "spec" / "SCIENCE.md"), "content": ""},
    )
    assert completed.returncode == 0
    assert json.loads(completed.stdout)["permission"] == "allow"


def test_owner_path_guard_denies_dotdot_spec_edit() -> None:
    denied = _run_script(
        "tools/hooks/owner_path_guard.py",
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "tools/../spec/SCIENCE.md"},
        },
    )
    assert denied.returncode == 0
    specific = json.loads(denied.stdout)["hookSpecificOutput"]
    assert specific["permissionDecision"] == "deny"


def test_owner_path_guard_denies_spec_edit() -> None:
    denied = _run_script(
        "tools/hooks/owner_path_guard.py",
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": str(_REPO / "spec" / "SCIENCE.md")},
        },
    )
    assert denied.returncode == 0
    body = json.loads(denied.stdout)
    specific = body["hookSpecificOutput"]
    assert specific["permissionDecision"] == "deny"
    allowed = _run_script(
        "tools/hooks/owner_path_guard.py",
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": str(_REPO / "src" / "cfbench" / "__init__.py")},
        },
    )
    assert allowed.stdout.strip() == ""


def test_after_file_edit_denies_spec_and_formats_python(tmp_path: Path) -> None:
    spec_edit = _run_script(
        "tools/hooks/after_file_edit.py",
        {
            "hook_event_name": "afterFileEdit",
            "file_path": str(_REPO / "data" / "gold" / ".gitkeep"),
        },
    )
    assert spec_edit.returncode == _CURSOR_DENY_EXIT
    assert OWNER_ONLY_MESSAGE in spec_edit.stderr
    target = tmp_path / "sample.py"
    target.write_text("x=1\n", encoding="utf-8")
    formatted = _run_script(
        "tools/hooks/after_file_edit.py",
        {"hook_event_name": "afterFileEdit", "file_path": str(target)},
    )
    assert formatted.returncode == 0
    assert target.read_text(encoding="utf-8") == "x = 1\n"


def test_pre_push_refuses_main_without_running_check() -> None:
    env = dict(os.environ)
    env["PRE_COMMIT_REMOTE_BRANCH"] = "refs/heads/main"
    completed = _run_script("tools/hooks/pre_push.py", payload={}, env=env)
    assert completed.returncode == 1
    assert "refusing push to main" in completed.stderr


def test_large_files_script(tmp_path: Path) -> None:
    small = tmp_path / "small.py"
    small.write_text("x = 1\n", encoding="utf-8")
    assert _run_script("tools/hooks/large_files.py", args=[str(small)]).returncode == 0
