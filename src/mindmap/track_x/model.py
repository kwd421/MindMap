from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from mindmap.canonical.model import Answer, CommonEvent, TargetQuery


class DatasetSplit(StrEnum):
    DEVELOPMENT = "development"
    HELDOUT = "heldout"


class RenderingFamily(StrEnum):
    EXPLICIT = "explicit"
    CONVERSATIONAL = "conversational"
    ELLIPTICAL = "elliptical"


class CandidateCondition(StrEnum):
    CLEAN = "clean"
    FIELD_CORRUPTION = "field_corruption"
    CANDIDATE_OMITTED = "candidate_omitted"
    RAW_UNAVAILABLE = "raw_unavailable"


class VerificationStatus(StrEnum):
    ACCEPT = "accept"
    CORRECT = "correct"
    ABSTAIN = "abstain"
    REJECT = "reject"


@dataclass(frozen=True, slots=True)
class FieldEvidence:
    field_name: str
    value: object
    confidence: float
    span_start: int | None = None
    span_end: int | None = None

    def __post_init__(self) -> None:
        if not self.field_name:
            raise ValueError("field evidence requires a field name")
        if not isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("field confidence must be finite and in [0, 1]")
        if (self.span_start is None) != (self.span_end is None):
            raise ValueError("span_start and span_end must be supplied together")
        if self.span_start is not None:
            if self.span_start < 0 or self.span_end is None or self.span_end < self.span_start:
                raise ValueError("invalid evidence span")


@dataclass(frozen=True, slots=True)
class VerifierInput:
    """The complete deployment-visible verifier surface.

    This type deliberately excludes case IDs, topology/split metadata, gold
    events, expected answers, queries, mutation labels, and recoverability
    labels. Evaluation code is responsible for constructing this sanitized
    view before calling a verifier.
    """

    raw_text: str | None
    candidate_event: CommonEvent | None
    context_events: tuple[CommonEvent, ...]
    insertion_index: int

    def __post_init__(self) -> None:
        if self.insertion_index < 0 or self.insertion_index > len(self.context_events):
            raise ValueError("insertion index is outside context event bounds")


@dataclass(frozen=True, slots=True)
class VerificationDecision:
    status: VerificationStatus
    output_event: CommonEvent | None
    confidence: float
    field_evidence: tuple[FieldEvidence, ...] = ()
    reason_codes: tuple[str, ...] = ()
    parser_calls: int = 1

    def __post_init__(self) -> None:
        if not isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("decision confidence must be finite and in [0, 1]")
        if self.parser_calls < 0:
            raise ValueError("parser_calls cannot be negative")
        if self.status in {VerificationStatus.ACCEPT, VerificationStatus.CORRECT}:
            if self.output_event is None:
                raise ValueError(f"{self.status.value} requires an output event")
        elif self.output_event is not None:
            raise ValueError(f"{self.status.value} must not emit an output event")
        if len(set(self.reason_codes)) != len(self.reason_codes):
            raise ValueError("reason codes must be unique")


@dataclass(frozen=True, slots=True)
class RawCandidateCase:
    case_id: str
    topology_family: str
    split: DatasetSplit
    rendering_family: RenderingFamily
    raw_text: str | None
    gold_event: CommonEvent | None
    candidate_event: CommonEvent | None
    context_events: tuple[CommonEvent, ...]
    insertion_index: int
    query: TargetQuery
    expected_answer: Answer
    condition: CandidateCondition
    mutated_fields: tuple[str, ...]
    recoverable_from_raw: bool
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("case_id is required")
        if self.insertion_index < 0 or self.insertion_index > len(self.context_events):
            raise ValueError("insertion index is outside context event bounds")
        if self.condition is CandidateCondition.CLEAN:
            if self.gold_event != self.candidate_event:
                raise ValueError("clean case candidate must equal the gold event")
            if self.mutated_fields:
                raise ValueError("clean case cannot declare mutated fields")
        if self.condition is CandidateCondition.CANDIDATE_OMITTED:
            if self.candidate_event is not None:
                raise ValueError("candidate_omitted case must omit the candidate")
        if self.condition is CandidateCondition.RAW_UNAVAILABLE and self.raw_text is not None:
            raise ValueError("raw_unavailable case must omit raw text")
        if self.recoverable_from_raw and self.raw_text is None:
            raise ValueError("raw-recoverable case requires raw text")

    def verifier_input(self) -> VerifierInput:
        """Return the only object a verifier is allowed to inspect."""

        return VerifierInput(
            raw_text=self.raw_text,
            candidate_event=self.candidate_event,
            context_events=self.context_events,
            insertion_index=self.insertion_index,
        )

    def events_with(self, event: CommonEvent | None) -> tuple[CommonEvent, ...]:
        rows = list(self.context_events)
        if event is not None:
            rows.insert(self.insertion_index, event)
        return tuple(rows)
