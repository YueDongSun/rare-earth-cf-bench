"""Format a Python file after an edit.

Owner-only paths are refused earlier, by ``preToolUse`` / ``PreToolUse``.
This hook only runs ruff format.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.hooks.policy import payload_path, read_payload  # noqa: E402


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
    """Format the edited file when it is Python."""
    payload = read_payload(sys.stdin)
    format_python(Path(payload_path(payload)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
