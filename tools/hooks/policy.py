"""Shared decisions for the git, Cursor, and Claude Code hooks.

Paths under ``spec/`` and ``data/gold/`` are owner-only. Shell denials match the
command list in the repository contract. No scientific quantity is checked here.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import TextIO

DEFAULT_MAX_BYTES = 500 * 1024
GOLD_MAX_BYTES = 5 * 1024 * 1024
CHECK_OUTPUT_TAIL = 4000
_GOLD_PATH_PARTS = 2
_PUSH_REF_FIELD = 2
_MIN_PUSH_FIELDS = 3
OWNER_ONLY_MESSAGE = (
    "spec/ and data/gold/ are owner-only. Open a GitHub issue labelled "
    "needs-science-decision, quote the spec line, list the concrete options, "
    "and stop work on that piece."
)
_SHARED_BRANCH = "main"
_COMMIT_TYPES = (
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
)
_COMMIT_SCOPES = (
    "task",
    "verify",
    "reference",
    "taskfmt",
    "tooling",
    "docs",
    "ci",
    "deps",
    "spec",
)
_COMMIT_HEADER = re.compile(
    "^(" + "|".join(_COMMIT_TYPES) + r")\((" + "|".join(_COMMIT_SCOPES) + r")\): \S.*$"
)
_BANNED_TRAILER = re.compile(
    r"^(co-authored-by:|generated-by:|made with )",
    re.IGNORECASE,
)
_SEGMENT = re.compile(r"&&|\|\||;|\n")
_GIT_PUSH = re.compile(r"\bgit(?:\s+-C\s+\S+)?\s+push\b")
_GIT_COMMIT = re.compile(r"\bgit(?:\s+-C\s+\S+)?\s+commit\b")
_GIT_RESET_HARD = re.compile(r"\bgit(?:\s+-C\s+\S+)?\s+reset\s+--hard(?:\s+(\S+))?")
_SHORT_FORCE = re.compile(r"(?:^|\s)-[A-Za-z]*f[A-Za-z]*(?:\s|$)")
_ORIGIN_MAIN = re.compile(r"\borigin\s+main(?:\s|$)")
_REF_MAIN = re.compile(r":(?:refs/heads/)?main(?:\s|$)")
_PIP_INSTALL = re.compile(r"(?:^|\s)pip3?\s+install\b")
_PYTHON_PIP = re.compile(r"\bpython3?\s+-m\s+pip\s+install\b")


def is_owner_only(path: str, repo_root: Path | None = None) -> bool:
    """Return whether ``path`` is under ``spec/`` or ``data/gold/``."""
    parts = PurePosixPath(_relative_path(path, repo_root)).parts
    if not parts:
        return False
    if parts[0] == "spec":
        return True
    return len(parts) >= _GOLD_PATH_PARTS and parts[0] == "data" and parts[1] == "gold"


def size_limit_bytes(path: str, repo_root: Path | None = None) -> int:
    """Return the large-file limit for ``path``. Gold files use the higher limit."""
    relative = _relative_path(path, repo_root)
    parts = PurePosixPath(relative).parts
    if len(parts) >= _GOLD_PATH_PARTS and parts[0] == "data" and parts[1] == "gold":
        return GOLD_MAX_BYTES
    return DEFAULT_MAX_BYTES


def large_file_error(path: Path, repo_root: Path) -> str | None:
    """Return an error when ``path`` is over its limit. Missing files are deletions."""
    if not path.exists():
        return None
    limit = size_limit_bytes(str(path), repo_root)
    size = path.stat().st_size
    if size <= limit:
        return None
    return f"{path} is {size} bytes; limit is {limit} bytes"


def commit_message_error(text: str) -> str | None:
    """Return an error when ``text`` is not an allowed Conventional Commit."""
    lines = [line for line in text.splitlines() if not line.startswith("#")]
    if not lines or lines[0].strip() == "":
        return "commit message is empty"
    header = lines[0].rstrip()
    if _COMMIT_HEADER.fullmatch(header) is None:
        return (
            "commit message must be Conventional Commits with a scope from "
            "task, verify, reference, taskfmt, tooling, docs, ci, deps, spec "
            "(example: feat(task): add cf-t2-001)"
        )
    for line in lines[1:]:
        if _BANNED_TRAILER.match(line.strip()):
            return "attribution trailers are not allowed in ordinary commits"
    return None


def shell_denial(command: str, current_branch: str) -> str | None:
    """Return a denial reason for a shell command, or None when it may run."""
    if "OWNER_SPEC_EDIT=" in command:
        return "setting OWNER_SPEC_EDIT is refused; agents must never set it"
    for segment in _segments(command):
        reason = _segment_denial(segment, current_branch)
        if reason is not None:
            return reason
    return None


def push_refusal(head_branch: str, remote_branch: str | None, stdin_text: str) -> str | None:
    """Return a refusal when a push updates ``main``."""
    targets = [] if remote_branch is None else [remote_branch]
    for line in stdin_text.splitlines():
        parts = line.split()
        if len(parts) >= _MIN_PUSH_FIELDS:
            targets.append(parts[_PUSH_REF_FIELD])
    blocked = head_branch == _SHARED_BRANCH or any(
        target in {_SHARED_BRANCH, "refs/heads/main"} for target in targets
    )
    if blocked:
        return "refusing push to main"
    return None


def read_payload(stdin: TextIO) -> dict[str, object]:
    """Read one JSON object from a hook stdin. Empty input is an error."""
    raw = stdin.read()
    if raw.strip() == "":
        raise SystemExit("hook received an empty payload")
    loaded = json.loads(raw)
    if not isinstance(loaded, dict):
        raise SystemExit("hook payload must be a JSON object")
    payload: dict[str, object] = {}
    for key, value in loaded.items():
        if not isinstance(key, str):
            raise SystemExit("hook payload keys must be strings")
        payload[key] = value
    return payload


def shell_command(payload: dict[str, object]) -> str:
    """Pull the shell command out of a Cursor or Claude hook payload."""
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        nested = tool_input.get("command")
        if isinstance(nested, str):
            return nested
    command = payload.get("command")
    if isinstance(command, str):
        return command
    raise SystemExit("hook payload has no shell command")


def payload_path(payload: dict[str, object]) -> str:
    """Pull a file path out of a Cursor or Claude hook payload."""
    direct = payload.get("file_path")
    if isinstance(direct, str) and direct != "":
        return direct
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        nested = tool_input.get("file_path")
        if isinstance(nested, str) and nested != "":
            return nested
    raise SystemExit("hook payload has no file_path")


def is_claude_payload(payload: dict[str, object]) -> bool:
    """Return whether the payload is a Claude Code hook event."""
    event = payload.get("hook_event_name")
    if event in {"PreToolUse", "PostToolUse", "Stop"}:
        return True
    return "tool_name" in payload and "hook_event_name" not in payload


def cursor_permission(reason: str | None) -> dict[str, str]:
    """Cursor permission object. ``reason`` None allows the call."""
    if reason is None:
        return {"permission": "allow"}
    return {"permission": "deny", "user_message": reason, "agent_message": reason}


def claude_pretool(reason: str | None) -> dict[str, object] | None:
    """Claude PreToolUse decision. None means the hook has no opinion."""
    if reason is None:
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def stop_block(event_name: str, summary: str) -> dict[str, object]:
    """Tell the agent to keep working because ``make check`` failed."""
    message = "make check failed. Keep working until make check passes.\n" + summary
    if event_name == "Stop":
        return {"decision": "block", "reason": message}
    return {"followup_message": message}


def should_run_check(payload: dict[str, object]) -> bool:
    """Skip the stop hook when the Cursor turn was aborted or errored."""
    return payload.get("status") not in {"aborted", "error"}


def git_branch() -> str:
    """Return the current git branch name."""
    completed = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def find_repo_root(start: Path) -> Path:
    """Walk parents until ``pyproject.toml`` is found."""
    for candidate in (start.resolve(), *start.resolve().parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise SystemExit(f"no pyproject.toml above {start}")


def _relative_path(path: str, repo_root: Path | None) -> str:
    candidate = Path(path)
    if candidate.is_absolute() and repo_root is not None:
        resolved = candidate.resolve()
        root = repo_root.resolve()
        if resolved.is_relative_to(root):
            candidate = resolved.relative_to(root)
        else:
            return resolved.as_posix()
    text = candidate.as_posix()
    if text.startswith("./"):
        return text[2:]
    return text


def _segments(command: str) -> list[str]:
    return [part for part in _SEGMENT.split(command) if part.strip() != ""]


def _segment_denial(segment: str, current_branch: str) -> str | None:
    checks = (
        (_force_push(segment), "git push --force is refused"),
        (_pushes_main(segment), "git push to main is refused"),
        (_commit_no_verify(segment), "git commit --no-verify is refused"),
        (_reset_hard_on_shared(segment, current_branch), "git reset --hard on main is refused"),
        (
            _PIP_INSTALL.search(segment) is not None or _PYTHON_PIP.search(segment) is not None,
            "pip install is refused; use uv add",
        ),
    )
    for matched, reason in checks:
        if matched:
            return reason
    return None


def _force_push(segment: str) -> bool:
    if _GIT_PUSH.search(segment) is None:
        return False
    return "--force" in segment or _SHORT_FORCE.search(segment) is not None


def _pushes_main(segment: str) -> bool:
    if _GIT_PUSH.search(segment) is None:
        return False
    return _ORIGIN_MAIN.search(segment) is not None or _REF_MAIN.search(segment) is not None


def _commit_no_verify(segment: str) -> bool:
    return _GIT_COMMIT.search(segment) is not None and "--no-verify" in segment


def _reset_hard_on_shared(segment: str, current_branch: str) -> bool:
    match = _GIT_RESET_HARD.search(segment)
    if match is None:
        return False
    target = match.group(1)
    if target is None or target == "HEAD" or target.startswith(("HEAD~", "HEAD^")):
        return current_branch == _SHARED_BRANCH
    normalized = target.removeprefix("refs/heads/").removeprefix("refs/remotes/")
    if "/" in normalized:
        normalized = normalized.rsplit("/", 1)[-1]
    return normalized == _SHARED_BRANCH
