from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from mindmap.canonical.generic import GenericLedger
from mindmap.canonical.model import CommonEvent, TargetSpace
from mindmap.canonical.typed import TypedLedger

from .model import VerificationDecision, VerificationStatus
from .v02_cases import V02Case, build_development_cases
from .v02_data import PassageCondition


class ContextGateTreatment(str, Enum):
    PRIMARY_PASSTHROUGH = "primary_passthrough"
    PRIMARY_VERIFIED_GATE = "primary_verified_gate"
    CONTROLLED_PASSTHROUGH = "controlled_passthrough"
    CONTROLLED_VERIFIED_GATE = "controlled_verified_gate"
    ORACLE_CONTEXT_CEILING = "oracle_context_ceiling"


_LEDGER_TYPES = {
    "G_generic": GenericLedger,
    "T_typed": TypedLedger,
}

_RAW_COMPLETE_CONDITIONS = frozenset(
    {
        PassageCondition.CLEAN,
        PassageCondition.FIELD_CORRUPTION,
        PassageCondition.CANDIDATE_OMITTED,
        PassageCondition.MISLEADING_CONTEXT,
    }
)


@dataclass(frozen=True, slots=True)
class ContextSelection:
    candidate_event: CommonEvent | None
    prompt_event: CommonEvent | None
    method_abstained: bool
    gate_applied: bool
    gate_status: str
    gate_confidence: float | None
    gate_reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ContextGateRow:
    passage_id: str
    fixture_id: str
    topology_family: str
    condition: str
    treatment: str
    architecture: str
    raw_available: bool
    raw_complete: bool
    candidate_present: bool
    candidate_exact: bool
    prompt_event_present: bool
    prompt_event_exact: bool
    prompt_payload_sha256: str | None
    prompt_payload_characters: int
    unsupported_prompt_exposure: bool
    ineligible_prompt_exposure: bool
    raw_unavailable_prompt_exposure: bool
    ambiguous_prompt_exposure: bool
    misleading_context_prompt_exposure: bool
    permitted_prompt_success: bool
    permitted_prompt_failure: bool
    gate_applied: bool
    gate_status: str
    gate_confidence: float | None
    gate_reason_codes: str
    gate_recovered_candidate_error: bool
    gate_blocked_candidate_error: bool
    clean_false_intervention: bool
    method_abstained: bool
    projection_error: bool
    answer: str
    expected_answer: str
    answer_correct: bool
    silent_wrong_use: bool
    unsafe_disclosure: bool
    false_denial: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _decision_selection(
    *,
    candidate: CommonEvent | None,
    decision: VerificationDecision,
) -> ContextSelection:
    if decision.status in {
        VerificationStatus.ABSTAIN,
        VerificationStatus.REJECT,
    }:
        return ContextSelection(
            candidate_event=candidate,
            prompt_event=None,
            method_abstained=True,
            gate_applied=True,
            gate_status=decision.status.value,
            gate_confidence=decision.confidence,
            gate_reason_codes=decision.reason_codes,
        )
    return ContextSelection(
        candidate_event=candidate,
        prompt_event=decision.output_event,
        method_abstained=False,
        gate_applied=True,
        gate_status=decision.status.value,
        gate_confidence=decision.confidence,
        gate_reason_codes=decision.reason_codes,
    )


def select_context(
    case: V02Case,
    treatment: ContextGateTreatment,
) -> ContextSelection:
    if treatment is ContextGateTreatment.PRIMARY_PASSTHROUGH:
        candidate = case.primary_extraction.event
        return ContextSelection(
            candidate_event=candidate,
            prompt_event=candidate,
            method_abstained=candidate is None,
            gate_applied=False,
            gate_status="not_applied",
            gate_confidence=None,
            gate_reason_codes=(),
        )

    if treatment is ContextGateTreatment.PRIMARY_VERIFIED_GATE:
        return _decision_selection(
            candidate=case.primary_extraction.event,
            decision=case.primary_verifier_decision,
        )

    if treatment is ContextGateTreatment.CONTROLLED_PASSTHROUGH:
        # The controlled candidate-only path intentionally continues even when
        # the candidate is omitted; the downstream ledger then operates on the
        # remaining context. This preserves the v0.2 mechanism-audit semantics.
        candidate = case.controlled_candidate_event
        return ContextSelection(
            candidate_event=candidate,
            prompt_event=candidate,
            method_abstained=False,
            gate_applied=False,
            gate_status="not_applied",
            gate_confidence=None,
            gate_reason_codes=(),
        )

    if treatment is ContextGateTreatment.CONTROLLED_VERIFIED_GATE:
        return _decision_selection(
            candidate=case.controlled_candidate_event,
            decision=case.controlled_verifier_decision,
        )

    if treatment is ContextGateTreatment.ORACLE_CONTEXT_CEILING:
        return ContextSelection(
            candidate_event=case.gold_event,
            prompt_event=case.gold_event,
            method_abstained=False,
            gate_applied=False,
            gate_status="oracle",
            gate_confidence=1.0,
            gate_reason_codes=("oracle_context_ceiling",),
        )

    raise ValueError(f"unknown context-gate treatment: {treatment}")


def _canonical_event_payload(event: CommonEvent | None) -> tuple[str | None, int]:
    if event is None:
        return None, 0
    payload = json.dumps(
        asdict(event),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return sha256(payload.encode("utf-8")).hexdigest(), len(payload)


def _answer_case(
    case: V02Case,
    *,
    architecture: str,
    selection: ContextSelection,
) -> tuple[object, bool, bool]:
    if selection.method_abstained:
        return "ABSTAIN", False, False
    try:
        ledger = _LEDGER_TYPES[architecture](
            case.events_with(selection.prompt_event)
        )
        return ledger.answer(case.query), False, True
    except Exception as exc:  # deterministic projection failures remain visible
        return f"ERROR:{type(exc).__name__}:{exc}", True, False


def evaluate_context_gate_case(
    case: V02Case,
    *,
    treatment: ContextGateTreatment,
    architecture: str,
) -> ContextGateRow:
    selection = select_context(case, treatment)
    condition = case.record.candidate_condition
    raw_available = bool(case.record.raw_text)
    raw_complete = condition in _RAW_COMPLETE_CONDITIONS
    candidate_exact = selection.candidate_event == case.gold_event
    prompt_present = selection.prompt_event is not None
    prompt_exact = prompt_present and selection.prompt_event == case.gold_event
    prompt_hash, prompt_characters = _canonical_event_payload(
        selection.prompt_event
    )

    answer, projection_error, attempted_answer = _answer_case(
        case,
        architecture=architecture,
        selection=selection,
    )
    answer_correct = (
        attempted_answer
        and not projection_error
        and answer == case.expected_answer
    )
    unsafe_disclosure = (
        attempted_answer
        and case.query.target_space is TargetSpace.DISCLOSE
        and case.expected_answer is False
        and answer is True
    )
    false_denial = (
        attempted_answer
        and case.query.target_space is TargetSpace.DISCLOSE
        and case.expected_answer is True
        and answer is False
    )

    candidate_error = not candidate_exact
    ineligible = condition in {
        PassageCondition.RAW_UNAVAILABLE,
        PassageCondition.AMBIGUOUS_RAW,
    }

    return ContextGateRow(
        passage_id=case.record.passage_id,
        fixture_id=case.record.fixture_id,
        topology_family=case.record.topology_family,
        condition=condition.value,
        treatment=treatment.value,
        architecture=architecture,
        raw_available=raw_available,
        raw_complete=raw_complete,
        candidate_present=selection.candidate_event is not None,
        candidate_exact=candidate_exact,
        prompt_event_present=prompt_present,
        prompt_event_exact=prompt_exact,
        prompt_payload_sha256=prompt_hash,
        prompt_payload_characters=prompt_characters,
        unsupported_prompt_exposure=prompt_present and not prompt_exact,
        ineligible_prompt_exposure=ineligible and prompt_present,
        raw_unavailable_prompt_exposure=(
            condition is PassageCondition.RAW_UNAVAILABLE and prompt_present
        ),
        ambiguous_prompt_exposure=(
            condition is PassageCondition.AMBIGUOUS_RAW and prompt_present
        ),
        misleading_context_prompt_exposure=(
            condition is PassageCondition.MISLEADING_CONTEXT
            and prompt_present
            and not prompt_exact
        ),
        permitted_prompt_success=raw_complete and prompt_exact,
        permitted_prompt_failure=raw_complete and not prompt_exact,
        gate_applied=selection.gate_applied,
        gate_status=selection.gate_status,
        gate_confidence=selection.gate_confidence,
        gate_reason_codes="|".join(selection.gate_reason_codes),
        gate_recovered_candidate_error=(
            selection.gate_applied and candidate_error and prompt_exact
        ),
        gate_blocked_candidate_error=(
            selection.gate_applied
            and candidate_error
            and not prompt_present
        ),
        clean_false_intervention=(
            condition is PassageCondition.CLEAN
            and selection.gate_applied
            and (not prompt_exact or selection.gate_status != "accept")
        ),
        method_abstained=selection.method_abstained,
        projection_error=projection_error,
        answer=repr(answer),
        expected_answer=repr(case.expected_answer),
        answer_correct=answer_correct,
        silent_wrong_use=(
            attempted_answer and not projection_error and not answer_correct
        ),
        unsafe_disclosure=unsafe_disclosure,
        false_denial=false_denial,
    )


def _rate(rows: list[ContextGateRow], field: str) -> float:
    if not rows:
        return 0.0
    return sum(bool(getattr(row, field)) for row in rows) / len(rows)


def _conditional_rate(
    rows: list[ContextGateRow],
    *,
    numerator: str,
    denominator: str,
) -> float | None:
    eligible = [row for row in rows if bool(getattr(row, denominator))]
    if not eligible:
        return None
    return sum(bool(getattr(row, numerator)) for row in eligible) / len(eligible)


def summarize_context_gate_rows(
    rows: list[ContextGateRow],
) -> dict[str, object]:
    grouped: dict[tuple[str, str], list[ContextGateRow]] = defaultdict(list)
    for row in rows:
        grouped[(row.treatment, row.architecture)].append(row)

    summaries: dict[str, dict[str, object]] = {}
    for (treatment, architecture), group in sorted(grouped.items()):
        prompt_rows = [row for row in group if row.prompt_event_present]
        permitted_rows = [row for row in group if row.raw_complete]
        ineligible_rows = [row for row in group if not row.raw_complete]
        candidate_error_rows = [row for row in group if not row.candidate_exact]
        summaries[f"{treatment}:{architecture}"] = {
            "n": len(group),
            "candidate_presence_rate": _rate(group, "candidate_present"),
            "candidate_exact_rate": _rate(group, "candidate_exact"),
            "prompt_coverage": _rate(group, "prompt_event_present"),
            "prompt_exact_rate": _rate(group, "prompt_event_exact"),
            "prompt_conditional_risk": (
                _rate(prompt_rows, "unsupported_prompt_exposure")
                if prompt_rows
                else None
            ),
            "unsupported_prompt_exposure_rate": _rate(
                group, "unsupported_prompt_exposure"
            ),
            "ineligible_prompt_exposure_rate": _rate(
                group, "ineligible_prompt_exposure"
            ),
            "ineligible_prompt_exposure_conditional": (
                _rate(ineligible_rows, "ineligible_prompt_exposure")
                if ineligible_rows
                else None
            ),
            "permitted_prompt_recall": (
                _rate(permitted_rows, "permitted_prompt_success")
                if permitted_rows
                else None
            ),
            "gate_recovery_rate_on_candidate_errors": (
                _rate(candidate_error_rows, "gate_recovered_candidate_error")
                if candidate_error_rows
                else None
            ),
            "gate_block_rate_on_candidate_errors": (
                _rate(candidate_error_rows, "gate_blocked_candidate_error")
                if candidate_error_rows
                else None
            ),
            "abstention_rate": _rate(group, "method_abstained"),
            "answer_accuracy": _rate(group, "answer_correct"),
            "silent_wrong_use_rate": _rate(group, "silent_wrong_use"),
            "unsafe_disclosure_rate": _rate(group, "unsafe_disclosure"),
            "false_denial_rate": _rate(group, "false_denial"),
            "clean_false_intervention_rate": _conditional_rate(
                group,
                numerator="clean_false_intervention",
                denominator="candidate_exact",
            ),
            "prompt_payload_characters_total": sum(
                row.prompt_payload_characters for row in group
            ),
        }

    disagreements: list[str] = []
    by_case: dict[tuple[str, str], dict[str, ContextGateRow]] = defaultdict(dict)
    for row in rows:
        by_case[(row.passage_id, row.treatment)][row.architecture] = row
    for (passage_id, treatment), pair in sorted(by_case.items()):
        if set(pair) != set(_LEDGER_TYPES):
            continue
        generic = pair["G_generic"]
        typed = pair["T_typed"]
        generic_outcome = (
            generic.answer,
            generic.method_abstained,
            generic.answer_correct,
            generic.unsafe_disclosure,
            generic.false_denial,
        )
        typed_outcome = (
            typed.answer,
            typed.method_abstained,
            typed.answer_correct,
            typed.unsafe_disclosure,
            typed.false_denial,
        )
        if generic_outcome != typed_outcome:
            disagreements.append(f"{passage_id}:{treatment}")

    return {
        "schema_version": "track-x-v0.3-context-gate-p0",
        "classification": (
            "fixed deterministic development-only mechanism audit; no held-out "
            "or public-benchmark claim"
        ),
        "n_rows": len(rows),
        "n_passages": len({row.passage_id for row in rows}),
        "n_topologies": len({row.topology_family for row in rows}),
        "treatments": [treatment.value for treatment in ContextGateTreatment],
        "architectures": sorted(_LEDGER_TYPES),
        "summaries": summaries,
        "generic_typed_disagreements": disagreements,
        "interpretation": {
            "retrieval_surface": "candidate event before the context gate",
            "prompt_surface": "structured event actually supplied downstream",
            "unsupported_prompt_exposure": (
                "a non-gold candidate event entered the prompt surface"
            ),
            "ineligible_prompt_exposure": (
                "prompt exposure despite raw-unavailable or materially ambiguous evidence"
            ),
            "primary_path": (
                "end-to-end development extractor; expected to expose a null when "
                "the primary already parses or abstains correctly"
            ),
            "controlled_path": (
                "secondary mechanism audit isolating corrupted/omitted candidate gating"
            ),
        },
    }


def evaluate_development_context_gate(
    repository_root: Path,
) -> tuple[list[ContextGateRow], dict[str, object]]:
    cases = build_development_cases(repository_root=repository_root)
    rows: list[ContextGateRow] = []
    for case in cases:
        for treatment in ContextGateTreatment:
            for architecture in _LEDGER_TYPES:
                rows.append(
                    evaluate_context_gate_case(
                        case,
                        treatment=treatment,
                        architecture=architecture,
                    )
                )
    return rows, summarize_context_gate_rows(rows)
