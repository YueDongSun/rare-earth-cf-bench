"""Reject added files over 500 KiB, with a 5 MiB ceiling for ``data/gold/``."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.hooks.policy import find_repo_root, large_file_error  # noqa: E402


def main(argv: list[str]) -> int:
    """Check each path argument. No arguments is a pass."""
    root = find_repo_root(Path.cwd())
    errors = [error for path in argv if (error := large_file_error(Path(path), root)) is not None]
    if not errors:
        return 0
    for error in errors:
        print(error, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
