from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from mindmap.canonical.model import Answer, CommonEvent, TargetQuery


class VerificationStatus(StrEnum):
    ACCEPT = "accept"
    CORRECT = "correct"
    ABSTAIN = "abstain"
    REJECT = "reject"


@dataclass(frozen=True, slots=True)
class VerificationDecision:
    status: VerificationStatus
    candidate_event: CommonEvent | None
    detected_fields: tuple[str, ...] = ()
    parsed_fields: tuple[tuple[str, object], ...] = ()
    reason: str = ""


@dataclass(frozen=True, slots=True)
class RawCandidateCase:
    case_id: str
    topology_family: str
    split: str                 # development | heldout
    rendering_family: str      # explicit | conversational | elliptical
    raw_text: str
    gold_event: CommonEvent
    candidate_event: CommonEvent
    context_events: tuple[CommonEvent, ...]
    insertion_index: int
    query: TargetQuery
    expected_answer: Answer
    error_mode: str            # clean or one controlled joint event error
    recoverable_from_raw: bool
    notes: str = ""

    def events_with(self, event: CommonEvent | None) -> tuple[CommonEvent, ...]:
        rows = list(self.context_events)
        if event is not None:
            rows.insert(self.insertion_index, event)
        return tuple(rows)
