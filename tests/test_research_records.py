from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_research_records_are_machine_checkable() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_research_records.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
