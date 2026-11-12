"""Reject commit messages that are not Conventional Commits with a known scope."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.hooks.policy import commit_message_error  # noqa: E402


def main(argv: list[str]) -> int:
    """Check the commit message file passed by the commit-msg hook."""
    if len(argv) != 1:
        print("usage: commit_msg.py COMMIT_MSG_FILE", file=sys.stderr)
        return 2
    error = commit_message_error(Path(argv[0]).read_text(encoding="utf-8"))
    if error is not None:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
