from __future__ import annotations

from pathlib import Path

from mindmap.track_x.v03_context_gate import ContextGateTreatment
from mindmap.track_x.v03_context_gate_report import (
    evaluate_development_context_gate_report,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_publication_summary_uses_clean_rows_as_clean_intervention_denominator():
    _rows, summary = evaluate_development_context_gate_report(REPOSITORY_ROOT)
    assert summary["reporting_normalization"] == {
        "clean_false_intervention_denominator": (
            "all clean passages in the same treatment and architecture"
        ),
        "row_level_source_retained": True,
    }

    summaries = summary["summaries"]
    assert isinstance(summaries, dict)
    for treatment in ContextGateTreatment:
        for architecture in ("G_generic", "T_typed"):
            group = summaries[f"{treatment.value}:{architecture}"]
            assert isinstance(group, dict)
            assert group["clean_checkpoint_count"] == 7
            assert group["clean_false_intervention_count"] == 0
            assert group["clean_false_intervention_rate"] == 0.0
