from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from statistics import mean

from mindmap.canonical.generic import GenericLedger
from mindmap.canonical.model import TargetSpace
from mindmap.canonical.typed import TypedLedger

from .model import VerificationStatus
from .v02_cases import V02DevelopmentCase, build_development_cases, expected_status
from .v02_data import PassageCondition


_LEDGER_TYPES = {
    "G_generic": GenericLedger,
    "T_typed": TypedLedger,
}


def _selected_event(case: V02DevelopmentCase, treatment: str):
    if treatment == "primary_candidate":
        return case.candidate_event, False
    if treatment == "raw_verifier":
        decision = case.verifier_decision
        if decision.status in {
            VerificationStatus.ABSTAIN,
            VerificationStatus.REJECT,
        }:
            return None, True
        return decision.output_event, False
    if treatment == "oracle_raw_ceiling":
        return case.gold_event, False
    raise ValueError(f"unknown treatment: {treatment}")


def _verification_row(case: V02DevelopmentCase) -> dict[str, object]:
    decision = case.verifier_decision
    covered = decision.status in {
        VerificationStatus.ACCEPT,
        VerificationStatus.CORRECT,
    }
    output_exact = covered and decision.output_event == case.gold_event
    expected = expected_status(case.record.candidate_condition)
    primary_exact = case.primary_extraction.event == case.gold_event
    return {
        "passage_id": case.record.passage_id,
        "topology_family": case.record.topology_family,
        "condition": case.record.candidate_condition.value,
        "primary_event_exact": primary_exact,
        "primary_confidence": case.primary_extraction.confidence,
        "candidate_event_exact": case.candidate_event == case.gold_event,
        "verifier_status": decision.status.value,
        "expected_status": expected.value,
        "status_correct": decision.status is expected,
        "covered": covered,
        "output_event_exact": output_exact,
        "clean_false_correction": (
            case.record.candidate_condition is PassageCondition.CLEAN
            and decision.status is not VerificationStatus.ACCEPT
        ),
        "false_accept": (
            case.record.candidate_condition is PassageCondition.FIELD_CORRUPTION
            and decision.status is VerificationStatus.ACCEPT
        ),
        "ambiguous_abstained": (
            case.record.candidate_condition is PassageCondition.AMBIGUOUS_RAW
            and decision.status is VerificationStatus.ABSTAIN
        ),
        "raw_unavailable_abstained": (
            case.record.candidate_condition is PassageCondition.RAW_UNAVAILABLE
            and decision.status is VerificationStatus.ABSTAIN
        ),
        "misleading_context_corrected": (
            case.record.candidate_condition is PassageCondition.MISLEADING_CONTEXT
            and decision.status is VerificationStatus.CORRECT
            and output_exact
        ),
        "confidence": decision.confidence,
        "reason_codes": "|".join(decision.reason_codes),
        "raw_characters": len(case.record.raw_text or ""),
        "context_characters": sum(len(text) for text in case.record.context_passages),
    }


def _downstream_row(
    case: V02DevelopmentCase,
    treatment: str,
    architecture: str,
) -> dict[str, object]:
    event, abstained = _selected_event(case, treatment)
    answer: object = "ABSTAIN"
    projection_error = False
    if not abstained:
        try:
            ledger = _LEDGER_TYPES[architecture](case.events_with(event))
            answer = ledger.answer(case.query)
        except Exception as exc:
            answer = f"ERROR:{type(exc).__name__}:{exc}"
            projection_error = True
            abstained = True
    correct = not abstained and answer == case.expected_answer
    unsafe_disclosure = (
        case.query.target_space is TargetSpace.DISCLOSE
        and case.expected_answer is False
        and answer is True
    )
    false_denial = (
        case.query.target_space is TargetSpace.DISCLOSE
        and case.expected_answer is True
        and answer is False
    )
    return {
        "passage_id": case.record.passage_id,
        "topology_family": case.record.topology_family,
        "condition": case.record.candidate_condition.value,
        "treatment": treatment,
        "architecture": architecture,
        "selected_event_exact": event == case.gold_event,
        "abstained": abstained,
        "projection_error": projection_error,
        "answer": repr(answer),
        "expected_answer": repr(case.expected_answer),
        "answer_correct": correct,
        "silent_wrong_use": not abstained and not correct,
        "unsafe_disclosure": unsafe_disclosure,
        "false_denial": false_denial,
    }


def _rate(values: list[bool]) -> float:
    return sum(values) / len(values) if values else 0.0


def evaluate_development(
    repository_root: Path,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    cases = build_development_cases(repository_root=repository_root)
    verification_rows = [_verification_row(case) for case in cases]
    downstream_rows: list[dict[str, object]] = []
    treatments = ("primary_candidate", "raw_verifier", "oracle_raw_ceiling")
    for case in cases:
        for treatment in treatments:
            for architecture in _LEDGER_TYPES:
                downstream_rows.append(
                    _downstream_row(case, treatment, architecture)
                )

    by_condition: dict[str, dict[str, object]] = {}
    for condition in PassageCondition:
        rows = [
            row for row in verification_rows if row["condition"] == condition.value
        ]
        by_condition[condition.value] = {
            "n": len(rows),
            "status_accuracy": _rate(
                [bool(row["status_correct"]) for row in rows]
            ),
            "output_exact_rate": _rate(
                [bool(row["output_event_exact"]) for row in rows]
            ),
            "mean_confidence": mean(
                float(row["confidence"]) for row in rows
            ) if rows else 0.0,
        }

    downstream_summary: dict[str, dict[str, object]] = {}
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in downstream_rows:
        grouped[(str(row["treatment"]), str(row["architecture"]))].append(row)
    for (treatment, architecture), rows in sorted(grouped.items()):
        downstream_summary[f"{treatment}:{architecture}"] = {
            "n": len(rows),
            "answer_accuracy": _rate(
                [bool(row["answer_correct"]) for row in rows]
            ),
            "abstention_rate": _rate([bool(row["abstained"]) for row in rows]),
            "silent_wrong_use_rate": _rate(
                [bool(row["silent_wrong_use"]) for row in rows]
            ),
            "unsafe_disclosure_rate": _rate(
                [bool(row["unsafe_disclosure"]) for row in rows]
            ),
            "selected_event_exact_rate": _rate(
                [bool(row["selected_event_exact"]) for row in rows]
            ),
        }

    disagreements: dict[str, int] = {}
    pair_map: dict[tuple[str, str], dict[str, dict[str, object]]] = defaultdict(dict)
    for row in downstream_rows:
        pair_map[(str(row["passage_id"]), str(row["treatment"]))][
            str(row["architecture"])
        ] = row
    for key, pair in pair_map.items():
        if set(pair) != set(_LEDGER_TYPES):
            continue
        generic = pair["G_generic"]
        typed = pair["T_typed"]
        generic_outcome = (
            generic["answer"],
            generic["abstained"],
            generic["answer_correct"],
            generic["unsafe_disclosure"],
        )
        typed_outcome = (
            typed["answer"],
            typed["abstained"],
            typed["answer_correct"],
            typed["unsafe_disclosure"],
        )
        if generic_outcome != typed_outcome:
            disagreements[f"{key[0]}:{key[1]}"] = 1

    summary = {
        "study": "MindMap Track X v0.2 development freeze audit",
        "interpretation": (
            "Session-B-authored development passages only; no held-out result"
        ),
        "n_topologies": len({row["topology_family"] for row in verification_rows}),
        "n_passage_conditions": len(verification_rows),
        "verification": {
            "status_accuracy": _rate(
                [bool(row["status_correct"]) for row in verification_rows]
            ),
            "covered_output_exact_rate": _rate(
                [
                    bool(row["output_event_exact"])
                    for row in verification_rows
                    if bool(row["covered"])
                ]
            ),
            "clean_false_correction_rate": _rate(
                [
                    bool(row["clean_false_correction"])
                    for row in verification_rows
                    if row["condition"] == PassageCondition.CLEAN.value
                ]
            ),
            "false_accept_rate": _rate(
                [
                    bool(row["false_accept"])
                    for row in verification_rows
                    if row["condition"] == PassageCondition.FIELD_CORRUPTION.value
                ]
            ),
            "ambiguous_abstention_rate": _rate(
                [
                    bool(row["ambiguous_abstained"])
                    for row in verification_rows
                    if row["condition"] == PassageCondition.AMBIGUOUS_RAW.value
                ]
            ),
            "raw_unavailable_abstention_rate": _rate(
                [
                    bool(row["raw_unavailable_abstained"])
                    for row in verification_rows
                    if row["condition"] == PassageCondition.RAW_UNAVAILABLE.value
                ]
            ),
            "misleading_context_correction_rate": _rate(
                [
                    bool(row["misleading_context_corrected"])
                    for row in verification_rows
                    if row["condition"] == PassageCondition.MISLEADING_CONTEXT.value
                ]
            ),
            "by_condition": by_condition,
        },
        "downstream": downstream_summary,
        "generic_typed_disagreements": disagreements,
    }
    return verification_rows, downstream_rows, summary
