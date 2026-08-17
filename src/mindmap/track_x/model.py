from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class EventRecord:
    """Normalized event used only by the Track X scoring layer.

    Predicted identifiers are never compared with gold identifiers. The
    remaining fields intentionally cover both flat-generic and normalized typed
    extraction outputs so the scorer does not privilege either representation.
    """

    event_id: str
    event_type: str
    participants: tuple[str, ...] = ()
    objects: tuple[str, ...] = ()
    about_world_branch_id: Optional[str] = None
    context_world_branch_id: Optional[str] = None
    valid_from: Optional[int] = None
    valid_to: Optional[int] = None
    system_time: Optional[int] = None
    policy_label: Optional[str] = None
    epistemic_type: Optional[str] = None
    attribution_kind: Optional[str] = None
    source_spans: tuple[str, ...] = ()
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must lie in [0, 1]")


@dataclass(frozen=True, slots=True)
class AlignmentPair:
    gold_index: int
    predicted_index: int
    score: float


@dataclass(frozen=True, slots=True)
class EventMetrics:
    n_gold: int
    n_predicted: int
    n_matched: int
    precision: float
    recall: float
    f1: float
    mean_match_score: float
    event_type_accuracy: float
    participant_jaccard: float
    object_jaccard: float
    temporal_similarity: float
    world_context_accuracy: float
    policy_epistemic_accuracy: float
    source_span_jaccard: float


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    """One paired answer/use checkpoint for selective-risk evaluation."""

    decision_id: str
    scenario_id: str
    confidence: float
    answered: bool
    correct: bool
    governed: bool = False
    governance_violation: bool = False

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must lie in [0, 1]")
        if self.governance_violation and not self.governed:
            raise ValueError("a governance violation must belong to a governed decision")
        if self.governance_violation and not self.answered:
            raise ValueError("an abstention cannot be a governance violation")
        if self.correct and not self.answered:
            raise ValueError("an abstention cannot be marked correct")


@dataclass(frozen=True, slots=True)
class OperatingPoint:
    threshold: float
    coverage: float
    ordinary_risk: float
    governance_risk: float
    answered: int
    governed_answered: int
    governed_total: int
    governed_coverage: float
    ordinary_errors: int
    governance_violations: int
