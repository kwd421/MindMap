from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable

from mindmap.canonical.generic import GenericLedger
from mindmap.canonical.typed import TypedLedger

from .generic_observer import GenericObserver
from .model import FaultCase, ObserverResult, ObserverSurface, localization_scores
from .typed_observer import TypedObserver


_OBSERVERS = (
    (GenericObserver(), GenericLedger),
    (TypedObserver(), TypedLedger),
)


def _evaluate_one(case: FaultCase, observer, ledger_type) -> tuple[ObserverResult, dict[str, object]]:
    surface = (
        ObserverSurface.SEMANTIC_JOURNAL
        if not case.identifiable
        else case.required_surface
    )
    projection_rows = case.faulty_projection_rows
    alerts = observer.inspect(
        case.faulty_events,
        surface=surface,
        journal_commitment=case.journal_commitment,
        projection_commitment=case.projection_commitment,
        projection_rows=projection_rows,
    )
    detected = bool(alerts)
    candidate_events = frozenset(
        event_id for alert in alerts for event_id in alert.candidate_event_ids
    )
    candidate_constraints = frozenset(
        constraint_id
        for alert in alerts
        for constraint_id in alert.constraint_ids
    )

    if detected:
        answer = "QUARANTINED"
        contained = True
        answer_correct = False
        silent_incorrect = False
    else:
        try:
            answer = ledger_type(case.faulty_events).answer(case.query)
        except Exception as exc:  # surfaced as an uncontained implementation failure
            answer = f"ERROR:{type(exc).__name__}:{exc}"
        contained = False
        answer_correct = answer == case.expected_clean_answer
        silent_incorrect = not answer_correct

    result = ObserverResult(
        observer=observer.name,
        case_id=case.case_id,
        alerts=alerts,
        answer=answer,
        detected=detected,
        contained=contained,
        answer_correct=answer_correct,
        silent_incorrect_use=silent_incorrect,
        candidate_event_ids=candidate_events,
        candidate_constraint_ids=candidate_constraints,
    )
    loc = localization_scores(
        candidate_events,
        candidate_constraints,
        case.acceptable_responsible_sets,
    )
    row: dict[str, object] = {
        "case_id": case.case_id,
        "family": case.family,
        "observer": observer.name,
        "surface": surface.name,
        "clean_control": case.clean_control,
        "identifiable": case.identifiable,
        "detected": detected,
        "contained": contained,
        "answer_correct": answer_correct,
        "silent_incorrect_use": silent_incorrect,
        "answer": repr(answer),
        "expected_clean_answer": repr(case.expected_clean_answer),
        "alert_rules": "|".join(sorted({alert.rule for alert in alerts})),
        "candidate_event_ids": "|".join(sorted(candidate_events)),
        "candidate_constraint_ids": "|".join(sorted(candidate_constraints)),
        **loc,
    }
    return result, row


def evaluate_suite(cases: Iterable[FaultCase]) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows: list[dict[str, object]] = []
    case_list = tuple(cases)
    for case in case_list:
        for observer, ledger_type in _OBSERVERS:
            _, row = _evaluate_one(case, observer, ledger_type)
            rows.append(row)

    by_observer: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_observer[str(row["observer"])].append(row)

    summary_rows: dict[str, dict[str, object]] = {}
    for observer, observer_rows in by_observer.items():
        faults = [row for row in observer_rows if not row["clean_control"]]
        identifiable = [row for row in faults if row["identifiable"]]
        clean = [row for row in observer_rows if row["clean_control"]]
        non_identifiable = [row for row in faults if not row["identifiable"]]
        summary_rows[observer] = {
            "n_cases": len(observer_rows),
            "n_faults": len(faults),
            "n_identifiable_faults": len(identifiable),
            "n_non_identifiable_faults": len(non_identifiable),
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
            "silent_incorrect_use_rate": (
                sum(bool(row["silent_incorrect_use"]) for row in faults) / len(faults)
                if faults
                else 0.0
            ),
            "non_identifiable_detected": sum(
                bool(row["detected"]) for row in non_identifiable
            ),
            "mean_candidate_set_size_given_detection": (
                sum(int(row["candidate_set_size"]) for row in identifiable if row["detected"])
                / sum(bool(row["detected"]) for row in identifiable)
                if any(bool(row["detected"]) for row in identifiable)
                else 0.0
            ),
            "mutated_event_hit_rate_given_detection": (
                sum(bool(row["mutated_event_hit"]) for row in identifiable if row["detected"])
                / sum(bool(row["detected"]) for row in identifiable)
                if any(bool(row["detected"]) for row in identifiable)
                else 0.0
            ),
            "exact_responsible_set_rate_given_detection": (
                sum(bool(row["exact_responsible_set"]) for row in identifiable if row["detected"])
                / sum(bool(row["detected"]) for row in identifiable)
                if any(bool(row["detected"]) for row in identifiable)
                else 0.0
            ),
        }

    disagreements = Counter()
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["case_id"])].append(row)
    for case_id, values in grouped.items():
        if len(values) != 2:
            disagreements[f"{case_id}:missing_observer"] += 1
            continue
        comparable = (
            values[0]["detected"],
            values[0]["answer_correct"],
            values[0]["silent_incorrect_use"],
        )
        other = (
            values[1]["detected"],
            values[1]["answer_correct"],
            values[1]["silent_incorrect_use"],
        )
        if comparable != other:
            disagreements[case_id] += 1

    summary: dict[str, object] = {
        "study": "MindMap Track E v0.2 canonical fixed P0",
        "interpretation": "fixed deterministic fault/clean-control audit; no inferential statistics",
        "n_archetypes": len(case_list),
        "n_rows": len(rows),
        "observers": summary_rows,
        "outcome_disagreements": dict(disagreements),
    }
    return rows, summary
