"""Format a Python edit, and refuse owner-only paths after the fact.

Cursor ``afterFileEdit`` cannot undo a write. Exit code 2 is the deny signal.
Claude Code denies the edit earlier in ``owner_path_guard.py``; this script
still refuses to format an owner-only path.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.hooks.policy import (  # noqa: E402
    OWNER_ONLY_MESSAGE,
    find_repo_root,
    is_claude_payload,
    is_owner_only,
    payload_path,
    read_payload,
)


def format_python(path: Path) -> None:
    """Run ruff format on a Python file. Other suffixes are left alone."""
    if path.suffix not in {".py", ".pyi"}:
        return
    if not path.is_file():
        raise SystemExit(f"cannot format missing file {path}")
    ruff = Path(sys.executable).with_name("ruff")
    if not ruff.is_file():
        raise SystemExit(f"ruff is not installed next to {sys.executable}")
    subprocess.run([str(ruff), "format", str(path)], check=True)


def main() -> int:
    """Format the edited file, or deny an owner-only path."""
    payload = read_payload(sys.stdin)
    path = payload_path(payload)
    if is_owner_only(path, find_repo_root(Path.cwd())):
        print(OWNER_ONLY_MESSAGE, file=sys.stderr)
        if is_claude_payload(payload):
            json.dump({"decision": "block", "reason": OWNER_ONLY_MESSAGE}, sys.stdout)
            sys.stdout.write("\n")
            return 0
        return 2
    format_python(Path(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
