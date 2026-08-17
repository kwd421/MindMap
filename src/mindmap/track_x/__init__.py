"""Track X scoring primitives for non-oracle extraction/generalization studies."""

from .alignment import maximum_weight_alignment
from .metrics import (
    EventSimilarityWeights,
    brier_score,
    event_similarity,
    expected_calibration_error,
    operating_point,
    risk_coverage_curve,
    safe_coverage,
    score_events,
)
from .model import (
    AlignmentPair,
    DecisionRecord,
    EventMetrics,
    EventRecord,
    OperatingPoint,
)

__all__ = [
    "AlignmentPair",
    "DecisionRecord",
    "EventMetrics",
    "EventRecord",
    "EventSimilarityWeights",
    "OperatingPoint",
    "brier_score",
    "event_similarity",
    "expected_calibration_error",
    "maximum_weight_alignment",
    "operating_point",
    "risk_coverage_curve",
    "safe_coverage",
    "score_events",
]
