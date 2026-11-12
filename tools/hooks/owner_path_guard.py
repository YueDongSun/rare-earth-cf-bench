"""Claude Code PreToolUse guard for edits under spec/ and data/gold/."""

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
    find_repo_root,
    is_owner_only,
    payload_path,
    read_payload,
)


def main() -> int:
    """Deny Edit, Write, and MultiEdit when the path is owner-only."""
    payload = read_payload(sys.stdin)
    path = payload_path(payload)
    reason = OWNER_ONLY_MESSAGE if is_owner_only(path, find_repo_root(Path.cwd())) else None
    response = claude_pretool(reason)
    if response is not None:
        json.dump(response, sys.stdout)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
