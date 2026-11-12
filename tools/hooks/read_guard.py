"""Allow agent reads, including owner-only science files.

Edits under ``spec/`` and ``data/gold/`` are refused by the edit hooks. Agents
still have to read the spec.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.hooks.policy import payload_path, read_payload  # noqa: E402


def main() -> int:
    """Allow the read when the payload names a file."""
    payload = read_payload(sys.stdin)
    payload_path(payload)
    json.dump({"permission": "allow"}, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
