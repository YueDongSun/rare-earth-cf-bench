"""Deny destructive git commands and pip install for Cursor and Claude Code."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.hooks.policy import (  # noqa: E402
    claude_pretool,
    cursor_permission,
    git_branch,
    is_claude_payload,
    read_payload,
    shell_command,
    shell_denial,
)


def main() -> int:
    """Read a hook payload and print an allow or deny decision."""
    payload = read_payload(sys.stdin)
    reason = shell_denial(shell_command(payload), git_branch())
    if is_claude_payload(payload):
        response = claude_pretool(reason)
        if response is not None:
            json.dump(response, sys.stdout)
            sys.stdout.write("\n")
        return 0
    json.dump(cursor_permission(reason), sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
