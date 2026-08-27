from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "run_late_destination_factorial",
    ROOT / "tools" / "run_late_destination_factorial.py",
)
FACTORIAL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(FACTORIAL)


def test_worker_preserves_known_temporal_pattern() -> None:
    rows = FACTORIAL.worker_rows(ROOT, "main", "test-revision")
    keyed = {
        (row["destination_creation_system_time"], row["implementation"]): row[
            "available"
        ]
        for row in rows
    }
    assert len(rows) == 9
    assert all(
        keyed[(time, implementation)]
        for time in (5, 6)
        for implementation in FACTORIAL.IMPLEMENTATIONS
    )
    assert keyed[(7, "gold")] is False
    assert keyed[(7, "generic")] is False
    assert keyed[(7, "typed")] is True


def test_summary_uses_nine_paired_revision_cells() -> None:
    main_rows = FACTORIAL.worker_rows(ROOT, "main", FACTORIAL.MAIN_REVISION)
    pr55_rows = [
        {**row, "revision_role": "pr55", "revision_sha": FACTORIAL.PR55_REVISION}
        for row in main_rows
    ]
    summary = FACTORIAL.summarize(main_rows + pr55_rows)
    assert summary["boolean_outputs"] == {"numerator": 18, "denominator": 18}
    assert summary["paired_revision_differences"] == {
        "numerator": 0,
        "denominator": 9,
    }
