"""Deny writes, edits, and deletes under spec/ and data/gold/ before they land.

Cursor ``preToolUse`` and Claude Code ``PreToolUse`` both call this script.
The decision is emitted in the caller's hook schema.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.hooks.policy import (  # noqa: E402
    OWNER_ONLY_MESSAGE,
    claude_pretool,
    cursor_permission,
    find_repo_root,
    is_owner_only,
    read_payload,
    tool_target_paths,
)


def main() -> int:
    """Deny the tool call when any target path is owner-only."""
    payload = read_payload(sys.stdin)
    paths = tool_target_paths(payload)
    if not paths:
        raise SystemExit("hook payload has no file path")
    root = find_repo_root(Path.cwd())
    reason = OWNER_ONLY_MESSAGE if any(is_owner_only(path, root) for path in paths) else None
    if payload.get("hook_event_name") == "preToolUse":
        json.dump(cursor_permission(reason), sys.stdout)
        sys.stdout.write("\n")
        return 0
    response = claude_pretool(reason)
    if response is not None:
        json.dump(response, sys.stdout)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
