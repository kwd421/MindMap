from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Iterable

from mindmap.canonical.generic import GenericLedger
from mindmap.canonical.model import TargetSpace
from mindmap.canonical.typed import TypedLedger

from .model import (
    CandidateCondition,
    RawCandidateCase,
    VerificationDecision,
    VerificationStatus,
)
from .verifier import RawEvidenceVerifier


_LEDGER_TYPES = {
    "G_generic": GenericLedger,
    "T_typed": TypedLedger,
}
_TREATMENTS = ("structured_only", "raw_verifier", "oracle_raw_ceiling")


def _decision_correct(
    case: RawCandidateCase, decision: VerificationDecision
) -> bool:
    if case.condition is CandidateCondition.CLEAN:
        return (
            decision.status is VerificationStatus.ACCEPT
            and decision.output_event == case.gold_event
        )
    if case.condition in {
        CandidateCondition.FIELD_CORRUPTION,
        CandidateCondition.CANDIDATE_OMITTED,
    }:
        return (
            decision.status is VerificationStatus.CORRECT
            and decision.output_event == case.gold_event
        )
    return decision.status is VerificationStatus.ABSTAIN


def _verification_row(
    case: RawCandidateCase, decision: VerificationDecision
) -> dict[str, object]:
    covered = decision.status in {
        VerificationStatus.ACCEPT,
        VerificationStatus.CORRECT,
    }
    output_exact = covered and decision.output_event == case.gold_event
    clean_false_correction = (
        case.condition is CandidateCondition.CLEAN
        and decision.status is not VerificationStatus.ACCEPT
    )
    corrupted_false_accept = (
        case.condition is CandidateCondition.FIELD_CORRUPTION
        and decision.status is VerificationStatus.ACCEPT
    )
    missing_recovered = (
        case.condition is CandidateCondition.CANDIDATE_OMITTED
        and decision.status is VerificationStatus.CORRECT
        and output_exact
    )
    raw_unavailable_abstained = (
        case.condition is CandidateCondition.RAW_UNAVAILABLE
        and decision.status is VerificationStatus.ABSTAIN
    )
    brier = (
        (decision.confidence - float(output_exact)) ** 2 if covered else None
    )
    return {
        "case_id": case.case_id,
        "split": case.split.value,
        "topology_family": case.topology_family,
        "rendering_family": case.rendering_family.value,
        "condition": case.condition.value,
        "recoverable_from_raw": case.recoverable_from_raw,
        "status": decision.status.value,
        "confidence": decision.confidence,
        "covered": covered,
        "output_event_exact": output_exact,
        "decision_correct": _decision_correct(case, decision),
        "clean_false_correction": clean_false_correction,
        "corrupted_false_accept": corrupted_false_accept,
        "missing_recovered": missing_recovered,
        "raw_unavailable_abstained": raw_unavailable_abstained,
        "field_evidence_count": len(decision.field_evidence),
        "reason_codes": "|".join(decision.reason_codes),
        "parser_calls": decision.parser_calls,
        "raw_characters": len(case.raw_text or ""),
        "brier_if_covered": brier,
    }


def _selected_event(
    case: RawCandidateCase,
    treatment: str,
    decision: VerificationDecision,
):
    if treatment == "structured_only":
        return case.candidate_event, False
    if treatment == "oracle_raw_ceiling":
        return case.gold_event, False
    if decision.status in {
        VerificationStatus.ABSTAIN,
        VerificationStatus.REJECT,
    }:
        return None, True
    return decision.output_event, False


def _downstream_row(
    case: RawCandidateCase,
    decision: VerificationDecision,
    treatment: str,
    architecture: str,
) -> dict[str, object]:
    selected_event, verifier_abstained = _selected_event(case, treatment, decision)
    answer: object = "ABSTAIN"
    projection_error = False
    abstained = verifier_abstained

    if not verifier_abstained:
        ledger_type = _LEDGER_TYPES[architecture]
        try:
            ledger = ledger_type(case.events_with(selected_event))
            answer = ledger.answer(case.query)
        except Exception as exc:  # fixed audit records the failure instead of hiding it
            answer = f"ERROR:{type(exc).__name__}:{exc}"
            projection_error = True
            abstained = True

    answer_correct = not abstained and answer == case.expected_answer
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
        "case_id": case.case_id,
        "split": case.split.value,
        "topology_family": case.topology_family,
        "rendering_family": case.rendering_family.value,
        "condition": case.condition.value,
        "treatment": treatment,
        "architecture": architecture,
        "selected_event_exact": selected_event == case.gold_event,
        "verifier_status": decision.status.value,
        "abstained": abstained,
        "projection_error": projection_error,
        "answer": repr(answer),
        "expected_answer": repr(case.expected_answer),
        "answer_correct": answer_correct,
        "silent_wrong_use": not abstained and not answer_correct,
        "unsafe_disclosure": unsafe_disclosure,
        "false_denial": false_denial,
    }


def _safe_rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _verification_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    covered = [row for row in rows if bool(row["covered"])]
    clean = [row for row in rows if row["condition"] == "clean"]
    corrupted = [
        row for row in rows if row["condition"] == "field_corruption"
    ]
    omitted = [row for row in rows if row["condition"] == "candidate_omitted"]
    unavailable = [row for row in rows if row["condition"] == "raw_unavailable"]
    brier_values = [
        float(row["brier_if_covered"])
        for row in covered
        if row["brier_if_covered"] is not None
    ]
    return {
        "n_cases": len(rows),
        "decision_accuracy": _safe_rate(
            sum(bool(row["decision_correct"]) for row in rows), len(rows)
        ),
        "coverage": _safe_rate(len(covered), len(rows)),
        "selective_risk": _safe_rate(
            sum(not bool(row["output_event_exact"]) for row in covered),
            len(covered),
        ),
        "exact_event_reconstruction_rate": _safe_rate(
            sum(bool(row["output_event_exact"]) for row in rows), len(rows)
        ),
        "clean_false_correction_rate": _safe_rate(
            sum(bool(row["clean_false_correction"]) for row in clean), len(clean)
        ),
        "corrupted_false_accept_rate": _safe_rate(
            sum(bool(row["corrupted_false_accept"]) for row in corrupted),
            len(corrupted),
        ),
        "missing_candidate_recovery_rate": _safe_rate(
            sum(bool(row["missing_recovered"]) for row in omitted), len(omitted)
        ),
        "raw_unavailable_abstention_rate": _safe_rate(
            sum(bool(row["raw_unavailable_abstained"]) for row in unavailable),
            len(unavailable),
        ),
        "brier_score_on_covered": mean(brier_values) if brier_values else 0.0,
        "mean_raw_characters": mean(
            int(row["raw_characters"]) for row in rows
        ) if rows else 0.0,
        "mean_parser_calls": mean(
            int(row["parser_calls"]) for row in rows
        ) if rows else 0.0,
    }


def _downstream_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    grouped: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["split"]), str(row["treatment"]), str(row["architecture"]))].append(row)
    for (split, treatment, architecture), group in sorted(grouped.items()):
        key = f"{split}:{treatment}:{architecture}"
        result[key] = {
            "n_rows": len(group),
            "answer_accuracy": _safe_rate(
                sum(bool(row["answer_correct"]) for row in group), len(group)
            ),
            "abstention_rate": _safe_rate(
                sum(bool(row["abstained"]) for row in group), len(group)
            ),
            "projection_error_rate": _safe_rate(
                sum(bool(row["projection_error"]) for row in group), len(group)
            ),
            "silent_wrong_use_rate": _safe_rate(
                sum(bool(row["silent_wrong_use"]) for row in group), len(group)
            ),
            "unsafe_disclosure_rate": _safe_rate(
                sum(bool(row["unsafe_disclosure"]) for row in group), len(group)
            ),
            "false_denial_rate": _safe_rate(
                sum(bool(row["false_denial"]) for row in group), len(group)
            ),
            "selected_event_exact_rate": _safe_rate(
                sum(bool(row["selected_event_exact"]) for row in group), len(group)
            ),
        }
    return result


def _disagreements(rows: list[dict[str, object]]) -> dict[str, int]:
    grouped: dict[tuple[str, str], dict[str, dict[str, object]]] = defaultdict(dict)
    for row in rows:
        grouped[(str(row["case_id"]), str(row["treatment"]))][
            str(row["architecture"])
        ] = row
    disagreements: dict[str, int] = {}
    for (case_id, treatment), pair in grouped.items():
        if set(pair) != set(_LEDGER_TYPES):
            continue
        generic = pair["G_generic"]
        typed = pair["T_typed"]
        outcome_generic = (
            generic["answer"],
            generic["abstained"],
            generic["answer_correct"],
            generic["unsafe_disclosure"],
        )
        outcome_typed = (
            typed["answer"],
            typed["abstained"],
            typed["answer_correct"],
            typed["unsafe_disclosure"],
        )
        if outcome_generic != outcome_typed:
            disagreements[f"{case_id}:{treatment}"] = 1
    return disagreements


def evaluate_raw_verifier_suite(
    cases: Iterable[RawCandidateCase],
    verifier: RawEvidenceVerifier | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    verifier = verifier or RawEvidenceVerifier()
    case_rows: list[dict[str, object]] = []
    downstream_rows: list[dict[str, object]] = []

    for case in cases:
        decision = verifier.verify(case.verifier_input())
        case_rows.append(_verification_row(case, decision))
        for treatment in _TREATMENTS:
            for architecture in _LEDGER_TYPES:
                downstream_rows.append(
                    _downstream_row(
                        case,
                        decision,
                        treatment,
                        architecture,
                    )
                )

    by_split: dict[str, dict[str, object]] = {}
    for split in ("development", "heldout"):
        split_rows = [row for row in case_rows if row["split"] == split]
        by_split[split] = _verification_summary(split_rows)

    summary = {
        "study": "MindMap Track X v0.1 leakage-free raw verifier P0",
        "interpretation": (
            "fixed deterministic parser/information-firewall audit; no "
            "inferential statistics or unrestricted natural-language claim"
        ),
        "n_cases": len(case_rows),
        "n_topology_families": len({row["topology_family"] for row in case_rows}),
        "verification": {
            "overall": _verification_summary(case_rows),
            "by_split": by_split,
        },
        "downstream": _downstream_summary(downstream_rows),
        "generic_typed_disagreements": _disagreements(downstream_rows),
    }
    return case_rows, downstream_rows, summary
