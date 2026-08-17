#!/usr/bin/env python3
"""Compatibility entry point for the NCM-Psi P0 equal-information audit."""
from __future__ import annotations

import sys
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).resolve().parent
if str(EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_DIR))

from p0_equal_information_pkg import *  # noqa: F401,F403,E402
from p0_equal_information_pkg.runner import main  # noqa: E402

if __name__ == "__main__":
    main()
