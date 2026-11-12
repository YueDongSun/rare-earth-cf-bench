"""Format-demo verifier.

The marker text is the instruction's required line, not a physical tolerance.
Science tasks take numeric tolerances by name from spec/TOLERANCES.md.
See docs/adr/0002-task-format.md.
"""

import os
from pathlib import Path

_MARKER_TEXT = "format_demo_ok\n"


def test_format_demo_marker() -> None:
    """The reference solution writes the marker file the instruction names."""
    workspace = Path(os.environ["CFBENCH_WORKSPACE"])
    marker = workspace / "smoke_marker.txt"
    assert marker.is_file()
    assert marker.read_text(encoding="utf-8") == _MARKER_TEXT
