"""Reject staged paths under ``spec/`` or ``data/gold/``.

The owner override is the environment variable ``OWNER_SPEC_EDIT=1``.
Agents must never set it. The staged set comes from
``git diff --cached --name-status -z -M``, so deletes and both sides of a
rename are visible. Pre-commit does not pass deleted paths as filenames.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.hooks.policy import (  # noqa: E402
    OWNER_ONLY_MESSAGE,
    find_repo_root,
    owner_paths_in_cached_diff,
)


def main(argv: list[str]) -> int:
    """Exit 1 when an owner-only path is staged and the owner override is unset."""
    del argv
    if os.environ.get("OWNER_SPEC_EDIT") == "1":
        return 0
    blocked = owner_paths_in_cached_diff(find_repo_root(Path.cwd()))
    if not blocked:
        return 0
    print(OWNER_ONLY_MESSAGE, file=sys.stderr)
    for path in blocked:
        print(path, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
