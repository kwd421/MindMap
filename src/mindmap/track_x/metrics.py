from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from math import isfinite

from .alignment import maximum_weight_alignment
from .model import DecisionRecord, EventMetrics, EventRecord, OperatingPoint


@dataclass(frozen=True, slots=True)
class EventSimilarityWeights:
    event_type: float = 0.22
    participants: float = 0.16
    objects: float = 0.12
    temporal: float = 0.16
    world_context: float = 0.10
    policy_epistemic: float = 0.14
    source_spans: float = 0.10

    def __post_init__(self) -> None:
        values = (
            self.event_type,
            self.participants,
            self.objects,
            self.temporal,
            self.world_context,
            self.policy_epistemic,
            self.source_spans,
        )
        if any(value < 0 for value in values):
            raise ValueError("similarity weights must be non-negative")
        if abs(sum(values) - 1.0) > 1e-9:
            raise ValueError("similarity weights must sum to one")


def _set_jaccard(left: Sequence[str], right: Sequence[str]) -> float:
    a = set(left)
    b = set(right)
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def _optional_exact(left: object, right: object) -> float:
    return 1.0 if left == right else 0.0


def _interval_iou(
    left_start: int | None,
    left_end: int | None,
    right_start: int | None,
    right_end: int | None,
    *,
    horizon: int,
) -> float:
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    if left_start is None and left_end is None and right_start is None and right_end is None:
        return 1.0

    ls = 0 if left_start is None else left_start
    rs = 0 if right_start is None else right_start
    le = horizon if left_end is None else left_end
    re = horizon if right_end is None else right_end
    if le < ls or re < rs:
        return 0.0
    intersection = max(0, min(le, re) - max(ls, rs))
    union = max(le, re) - min(ls, rs)
    if union == 0:
        return 1.0 if (ls, le) == (rs, re) else 0.0
    return intersection / union


def _temporal_similarity(left: EventRecord, right: EventRecord, *, horizon: int) -> float:
    interval = _interval_iou(
        left.valid_from,
        left.valid_to,
        right.valid_from,
        right.valid_to,
        horizon=horizon,
    )
    system = _optional_exact(left.system_time, right.system_time)
    return 0.75 * interval + 0.25 * system


def _world_context_similarity(left: EventRecord, right: EventRecord) -> float:
    return 0.5 * _optional_exact(
        left.about_world_branch_id, right.about_world_branch_id
    ) + 0.5 * _optional_exact(
        left.context_world_branch_id, right.context_world_branch_id
    )


def _policy_epistemic_similarity(left: EventRecord, right: EventRecord) -> float:
    return (
        _optional_exact(left.policy_label, right.policy_label)
        + _optional_exact(left.epistemic_type, right.epistemic_type)
        + _optional_exact(left.attribution_kind, right.attribution_kind)
    ) / 3.0


def event_similarity(
    left: EventRecord,
    right: EventRecord,
    *,
    horizon: int,
    weights: EventSimilarityWeights | None = None,
) -> float:
    w = weights or EventSimilarityWeights()
    components = (
        (w.event_type, _optional_exact(left.event_type, right.event_type)),
        (w.participants, _set_jaccard(left.participants, right.participants)),
        (w.objects, _set_jaccard(left.objects, right.objects)),
        (w.temporal, _temporal_similarity(left, right, horizon=horizon)),
        (w.world_context, _world_context_similarity(left, right)),
        (w.policy_epistemic, _policy_epistemic_similarity(left, right)),
        (w.source_spans, _set_jaccard(left.source_spans, right.source_spans)),
    )
    return sum(weight * value for weight, value in components)


def score_events(
    gold: Sequence[EventRecord],
    predicted: Sequence[EventRecord],
    *,
    horizon: int,
    minimum_match_score: float = 0.5,
    weights: EventSimilarityWeights | None = None,
) -> EventMetrics:
    scorer = lambda left, right: event_similarity(
        left, right, horizon=horizon, weights=weights
    )
    pairs = maximum_weight_alignment(
        gold,
        predicted,
        scorer,
        minimum_score=minimum_match_score,
    )
    matched = len(pairs)
    precision = matched / len(predicted) if predicted else (1.0 if not gold else 0.0)
    recall = matched / len(gold) if gold else (1.0 if not predicted else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    # Field metrics are gold-normalized: every unmatched gold event contributes
    # zero. This prevents a system from improving field accuracy by omitting
    # difficult events.
    denominator = len(gold)
    if denominator == 0:
        perfect = 1.0 if not predicted else 0.0
        return EventMetrics(
            n_gold=0,
            n_predicted=len(predicted),
            n_matched=0,
            precision=precision,
            recall=recall,
            f1=f1,
            mean_match_score=perfect,
            event_type_accuracy=perfect,
            participant_jaccard=perfect,
            object_jaccard=perfect,
            temporal_similarity=perfect,
            world_context_accuracy=perfect,
            policy_epistemic_accuracy=perfect,
            source_span_jaccard=perfect,
        )

    totals = {
        "match": 0.0,
        "event_type": 0.0,
        "participants": 0.0,
        "objects": 0.0,
        "temporal": 0.0,
        "world": 0.0,
        "policy": 0.0,
        "source": 0.0,
    }
    for pair in pairs:
        left = gold[pair.gold_index]
        right = predicted[pair.predicted_index]
        totals["match"] += pair.score
        totals["event_type"] += _optional_exact(left.event_type, right.event_type)
        totals["participants"] += _set_jaccard(left.participants, right.participants)
        totals["objects"] += _set_jaccard(left.objects, right.objects)
        totals["temporal"] += _temporal_similarity(left, right, horizon=horizon)
        totals["world"] += _world_context_similarity(left, right)
        totals["policy"] += _policy_epistemic_similarity(left, right)
        totals["source"] += _set_jaccard(left.source_spans, right.source_spans)

    return EventMetrics(
        n_gold=len(gold),
        n_predicted=len(predicted),
        n_matched=matched,
        precision=precision,
        recall=recall,
        f1=f1,
        mean_match_score=totals["match"] / denominator,
        event_type_accuracy=totals["event_type"] / denominator,
        participant_jaccard=totals["participants"] / denominator,
        object_jaccard=totals["objects"] / denominator,
        temporal_similarity=totals["temporal"] / denominator,
        world_context_accuracy=totals["world"] / denominator,
        policy_epistemic_accuracy=totals["policy"] / denominator,
        source_span_jaccard=totals["source"] / denominator,
    )


def operating_point(
    decisions: Sequence[DecisionRecord],
    *,
    threshold: float,
) -> OperatingPoint:
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must lie in [0, 1]")
    selected = [
        decision
        for decision in decisions
        if decision.answered and decision.confidence >= threshold
    ]
    governed = [decision for decision in selected if decision.governed]
    ordinary_errors = sum(not decision.correct for decision in selected)
    violations = sum(decision.governance_violation for decision in governed)
    ordinary_risk = ordinary_errors / len(selected) if selected else 0.0
    governance_risk = violations / len(governed) if governed else 0.0
    return OperatingPoint(
        threshold=threshold,
        coverage=len(selected) / len(decisions) if decisions else 0.0,
        ordinary_risk=ordinary_risk,
        governance_risk=governance_risk,
        answered=len(selected),
        governed_answered=len(governed),
        ordinary_errors=ordinary_errors,
        governance_violations=violations,
    )


def risk_coverage_curve(
    decisions: Sequence[DecisionRecord],
) -> tuple[OperatingPoint, ...]:
    thresholds = {1.0, 0.0}
    thresholds.update(decision.confidence for decision in decisions if decision.answered)
    points = [operating_point(decisions, threshold=value) for value in thresholds]
    return tuple(
        sorted(
            points,
            key=lambda point: (
                point.coverage,
                point.ordinary_risk,
                point.governance_risk,
                -point.threshold,
            ),
        )
    )


def safe_coverage(
    decisions: Sequence[DecisionRecord],
    *,
    max_ordinary_risk: float = 0.05,
    max_governance_risk: float = 0.01,
) -> OperatingPoint:
    for value in (max_ordinary_risk, max_governance_risk):
        if not 0.0 <= value <= 1.0:
            raise ValueError("risk limits must lie in [0, 1]")
    candidates = [
        point
        for point in risk_coverage_curve(decisions)
        if point.ordinary_risk <= max_ordinary_risk
        and point.governance_risk <= max_governance_risk
    ]
    if not candidates:
        # The explicit all-abstain policy is always available, even when a
        # confidence-1 attempted answer prevents thresholding it away.
        return OperatingPoint(1.0, 0.0, 0.0, 0.0, 0, 0, 0, 0)
    return max(
        candidates,
        key=lambda point: (
            point.coverage,
            -point.governance_risk,
            -point.ordinary_risk,
            point.threshold,
        ),
    )


def brier_score(decisions: Iterable[DecisionRecord]) -> float:
    rows = tuple(decisions)
    if not rows:
        return 0.0
    return sum(
        (decision.confidence - float(decision.answered and decision.correct)) ** 2
        for decision in rows
    ) / len(rows)


def expected_calibration_error(
    decisions: Iterable[DecisionRecord],
    *,
    bins: int = 10,
) -> float:
    if bins <= 0:
        raise ValueError("bins must be positive")
    rows = tuple(decisions)
    if not rows:
        return 0.0
    buckets: list[list[DecisionRecord]] = [[] for _ in range(bins)]
    for decision in rows:
        index = min(bins - 1, int(decision.confidence * bins))
        buckets[index].append(decision)
    ece = 0.0
    for bucket in buckets:
        if not bucket:
            continue
        confidence = sum(row.confidence for row in bucket) / len(bucket)
        accuracy = sum(row.answered and row.correct for row in bucket) / len(bucket)
        ece += len(bucket) / len(rows) * abs(confidence - accuracy)
    if not isfinite(ece):
        raise ArithmeticError("non-finite calibration result")
    return ece
