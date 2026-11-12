"""Refuse a push to ``main``, then run ``make check``."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.hooks.policy import git_branch, push_refusal  # noqa: E402


def main() -> int:
    """Exit 1 when the push updates main. Otherwise ``make check`` must pass."""
    stdin_text = "" if sys.stdin.isatty() else sys.stdin.read()
    refusal = push_refusal(
        git_branch(),
        os.environ.get("PRE_COMMIT_REMOTE_BRANCH"),
        stdin_text,
    )
    if refusal is not None:
        print(refusal, file=sys.stderr)
        return 1
    subprocess.run(["make", "check"], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
