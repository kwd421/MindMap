from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

from .v03_context_gate import (
    ContextGateRow,
    evaluate_development_context_gate as evaluate_raw_development_context_gate,
)


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def normalize_context_gate_summary(
    rows: list[ContextGateRow],
    summary: dict[str, object],
) -> dict[str, object]:
    """Return the publication-facing deterministic summary.

    The underlying P0 evaluator intentionally exposes many row-level booleans.
    This adapter makes every clean-intervention denominator explicit rather than
    inferring it from candidate exactness, which can differ by treatment.
    """

    normalized: dict[str, Any] = deepcopy(summary)
    summaries = normalized.get("summaries")
    if not isinstance(summaries, dict):
        raise ValueError("context-gate summary lacks treatment summaries")

    grouped: dict[tuple[str, str], list[ContextGateRow]] = defaultdict(list)
    for row in rows:
        grouped[(row.treatment, row.architecture)].append(row)

    for (treatment, architecture), group in grouped.items():
        key = f"{treatment}:{architecture}"
        target = summaries.get(key)
        if not isinstance(target, dict):
            raise ValueError(f"context-gate summary lacks group: {key}")
        clean_rows = [row for row in group if row.condition == "clean"]
        false_interventions = sum(
            row.clean_false_intervention for row in clean_rows
        )
        target["clean_false_intervention_count"] = false_interventions
        target["clean_checkpoint_count"] = len(clean_rows)
        target["clean_false_intervention_rate"] = _ratio(
            false_interventions, len(clean_rows)
        )

    normalized["reporting_normalization"] = {
        "clean_false_intervention_denominator": (
            "all clean passages in the same treatment and architecture"
        ),
        "row_level_source_retained": True,
    }
    return normalized


def evaluate_development_context_gate_report(
    repository_root: Path,
) -> tuple[list[ContextGateRow], dict[str, object]]:
    rows, summary = evaluate_raw_development_context_gate(repository_root)
    return rows, normalize_context_gate_summary(rows, summary)
