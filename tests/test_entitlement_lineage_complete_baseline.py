from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


SCRIPT = Path(__file__).resolve().parents[1] / "experiments" / "entitlement_lineage_complete_baseline.py"
SPEC = importlib.util.spec_from_file_location("entitlement_lineage_complete_baseline", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.path.insert(0, str(SCRIPT.parent))
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_complete_equal_information_baseline_erases_headline_gap() -> None:
    summary = MODULE.run(scenarios=200)
    assert summary["failure_count"] == 0, summary
    assert summary["primary_accuracy"] >= summary["ncm_psi_primary_accuracy"], summary
    assert summary["uses_query_factor_labels"] is False
