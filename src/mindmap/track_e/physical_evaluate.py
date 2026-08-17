from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from typing import Iterable

from .physical import (
    GenericPhysicalStore,
    PhysicalFaultCase,
    TypedPhysicalStore,
    run_physical_case,
)


_STORES = (GenericPhysicalStore, TypedPhysicalStore)


def _metrics_delta(before: tuple[tuple[str, int], ...], after: tuple[tuple[str, int], ...]) -> dict[str, int]:
    left = dict(before)
    right = dict(after)
    return {key: right.get(key, 0) - left.get(key, 0) for key in sorted(set(left) | set(right))}


def evaluate_physical_suite(
    cases: Iterable[PhysicalFaultCase],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    case_list = tuple(cases)
    rows: list[dict[str, object]] = []
    for case in case_list:
        for store_type in _STORES:
            result = run_physical_case(case, store_type)
            row = asdict(result)
            row["metrics_before_repair"] = dict(result.metrics_before_repair)
            row["metrics_after_repair"] = dict(result.metrics_after_repair)
            row["repair_cost"] = _metrics_delta(
                result.metrics_before_repair, result.metrics_after_repair
            )
            rows.append(row)

    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["implementation"])].append(row)

    observer_summaries: dict[str, dict[str, object]] = {}
    for implementation, values in grouped.items():
        faults = [row for row in values if not row["clean_control"]]
        identifiable = [row for row in faults if row["identifiable"]]
        clean = [row for row in values if row["clean_control"]]
        repairable = [row for row in identifiable if row["repair_attempted"]]
        observer_summaries[implementation] = {
            "n_cases": len(values),
            "n_faults": len(faults),
            "n_identifiable_faults": len(identifiable),
            "n_clean_controls": len(clean),
            "identifiable_detection_recall": (
                sum(bool(row["detected"]) for row in identifiable) / len(identifiable)
                if identifiable
                else 0.0
            ),
            "clean_false_alarm_rate": (
                sum(bool(row["detected"]) for row in clean) / len(clean)
                if clean
                else 0.0
            ),
            "silent_incorrect_use_rate_all_faults": (
                sum(bool(row["silent_incorrect_use"]) for row in faults) / len(faults)
                if faults
                else 0.0
            ),
            "silent_incorrect_use_rate_identifiable": (
                sum(bool(row["silent_incorrect_use"]) for row in identifiable) / len(identifiable)
                if identifiable
                else 0.0
            ),
            "repair_success_rate": (
                sum(bool(row["repair_success"]) for row in repairable) / len(repairable)
                if repairable
                else 0.0
            ),
            "mean_repair_events_reprocessed": (
                sum(int(row["repair_cost"]["events_reprocessed"]) for row in repairable)
                / len(repairable)
                if repairable
                else 0.0
            ),
            "mean_repair_query_recomputations": (
                sum(int(row["repair_cost"]["query_recomputations"]) for row in repairable)
                / len(repairable)
                if repairable
                else 0.0
            ),
            "total_residue_after_repair": sum(
                int(row["residue_after_repair"]) for row in repairable
            ),
            "journal_mismatch_count": sum(
                bool(row["journal_commitment_mismatch"]) for row in values
            ),
            "projection_head_mismatch_count": sum(
                bool(row["projection_head_mismatch"]) for row in values
            ),
            "projection_content_mismatch_count": sum(
                bool(row["projection_content_mismatch"]) for row in values
            ),
        }

    outcome_disagreements: dict[str, dict[str, tuple[object, object]]] = {}
    by_case: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_case[str(row["case_id"])].append(row)
    fields = (
        "detected",
        "pre_repair_correct",
        "silent_incorrect_use",
        "repair_success",
        "residue_after_repair",
    )
    for case_id, values in by_case.items():
        if len(values) != 2:
            outcome_disagreements[case_id] = {"missing_implementation": (len(values), 2)}
            continue
        differences = {
            field: (values[0][field], values[1][field])
            for field in fields
            if values[0][field] != values[1][field]
        }
        if differences:
            outcome_disagreements[case_id] = differences

    summary: dict[str, object] = {
        "study": "MindMap Track E v0.3 matched physical fault P1",
        "interpretation": "fixed deterministic physical projection/repair audit; no inferential statistics",
        "n_archetypes": len(case_list),
        "n_rows": len(rows),
        "implementations": observer_summaries,
        "outcome_disagreements": outcome_disagreements,
        "case_ids": [case.case_id for case in case_list],
    }
    return rows, summary
