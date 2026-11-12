"""Run ``make check`` when an agent turn stops, and block a failing turn."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.hooks.policy import (  # noqa: E402
    CHECK_OUTPUT_TAIL,
    read_payload,
    should_run_check,
    stop_block,
)


def run_make_check() -> tuple[bool, str]:
    """Return whether ``make check`` passed, plus the tail of its output."""
    completed = subprocess.run(
        ["make", "check"],
        capture_output=True,
        text=True,
        check=False,
    )
    combined = f"{completed.stdout}\n{completed.stderr}"
    return completed.returncode == 0, combined[-CHECK_OUTPUT_TAIL:]


def main() -> int:
    """Block the stop when ``make check`` fails."""
    payload = read_payload(sys.stdin)
    if not should_run_check(payload):
        return 0
    passed, tail = run_make_check()
    if passed:
        return 0
    event = payload.get("hook_event_name")
    event_name = event if isinstance(event, str) else "stop"
    json.dump(stop_block(event_name, tail), sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
