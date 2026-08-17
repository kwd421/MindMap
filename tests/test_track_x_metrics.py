from __future__ import annotations

from dataclasses import replace

import pytest

from mindmap.track_x import (
    DecisionRecord,
    EventRecord,
    brier_score,
    conditional_brier_score,
    expected_calibration_error,
    maximum_weight_alignment,
    operating_point,
    safe_coverage,
    select_safe_threshold,
    score_events,
)


def test_alignment_uses_global_optimum_and_threshold():
    gold = ("g0", "g1")
    predicted = ("p0", "p1")
    scores = {
        ("g0", "p0"): 0.90,
        ("g0", "p1"): 0.80,
        ("g1", "p0"): 0.85,
        ("g1", "p1"): 0.10,
    }
    pairs = maximum_weight_alignment(
        gold,
        predicted,
        lambda left, right: scores[(left, right)],
        minimum_score=0.5,
    )
    assert {(pair.gold_index, pair.predicted_index) for pair in pairs} == {
        (0, 1),
        (1, 0),
    }
    assert sum(pair.score for pair in pairs) == pytest.approx(1.65)


def test_event_metrics_penalize_false_positive_and_omitted_fields():
    gold = (
        EventRecord(
            "g0",
            "exposure",
            participants=("M1", "M2"),
            objects=("E1",),
            about_world_branch_id="main",
            context_world_branch_id="main",
            valid_from=2,
            valid_to=8,
            system_time=3,
            policy_label="private",
            epistemic_type="fact",
            attribution_kind="attributed_report",
            source_spans=("s1:t3",),
        ),
        EventRecord(
            "g1",
            "policy",
            participants=("M2",),
            objects=("E1",),
            about_world_branch_id="main",
            context_world_branch_id="main",
            valid_from=8,
            valid_to=None,
            system_time=9,
            policy_label="revoked",
            epistemic_type="fact",
            attribution_kind="direct_observation",
            source_spans=("s2:t1",),
        ),
    )
    predicted = (
        replace(gold[0], event_id="p0"),
        EventRecord(
            "p1",
            "policy",
            participants=("M2",),
            objects=("E1",),
            about_world_branch_id="main",
            context_world_branch_id="main",
            valid_from=8,
            valid_to=None,
            system_time=9,
            policy_label="public",
            epistemic_type="fact",
            attribution_kind="direct_observation",
            source_spans=(),
        ),
        EventRecord("fp", "unrelated", participants=("M9",)),
    )
    metrics = score_events(gold, predicted, horizon=20, minimum_match_score=0.5)
    assert metrics.n_matched == 2
    assert metrics.precision == pytest.approx(2 / 3)
    assert metrics.recall == 1.0
    assert metrics.f1 == pytest.approx(0.8)
    assert metrics.event_type_accuracy == 1.0
    assert metrics.policy_epistemic_accuracy < 1.0
    assert metrics.source_span_jaccard == pytest.approx(0.5)


def test_safe_coverage_selects_highest_valid_operating_point():
    decisions = (
        DecisionRecord("d1", "s1", 0.95, True, True, True, False),
        DecisionRecord("d2", "s1", 0.90, True, True, True, False),
        DecisionRecord("d3", "s2", 0.80, True, False, False, False),
        DecisionRecord("d4", "s2", 0.70, True, True, True, True),
    )
    point = safe_coverage(
        decisions,
        max_ordinary_risk=0.05,
        max_governance_risk=0.01,
    )
    assert point.threshold == pytest.approx(0.90)
    assert point.coverage == pytest.approx(0.50)
    assert point.ordinary_risk == 0.0
    assert point.governance_risk == 0.0
    assert point.governed_coverage == pytest.approx(2 / 3)


def test_safe_coverage_can_return_explicit_all_abstain_policy():
    decisions = (
        DecisionRecord("d1", "s1", 1.0, True, False, True, True),
    )
    point = safe_coverage(decisions, max_ordinary_risk=0.0, max_governance_risk=0.0)
    assert point.coverage == 0.0
    assert point.answered == 0


def test_calibration_metrics_have_known_values():
    decisions = (
        DecisionRecord("d1", "s1", 0.8, True, True),
        DecisionRecord("d2", "s1", 0.2, True, False),
    )
    assert brier_score(decisions) == pytest.approx(0.04)
    assert conditional_brier_score(decisions) == pytest.approx(0.04)
    assert expected_calibration_error(decisions, bins=2) == pytest.approx(0.2)


def test_decision_invariants_reject_impossible_rows():
    with pytest.raises(ValueError):
        DecisionRecord("bad", "s", 0.5, False, False, False, True)


def test_threshold_is_selected_on_development_and_frozen_on_test():
    development = (
        DecisionRecord("d1", "s1", 0.95, True, True, True, False),
        DecisionRecord("d2", "s1", 0.90, True, True, True, False),
        DecisionRecord("d3", "s2", 0.80, True, False, True, False),
    )
    threshold = select_safe_threshold(development)
    assert threshold == pytest.approx(0.90)

    held_out = (
        DecisionRecord("t1", "h1", 0.95, True, True, True, False),
        DecisionRecord("t2", "h1", 0.90, True, False, True, False),
        DecisionRecord("t3", "h2", 0.80, True, True, True, False),
    )
    point = operating_point(held_out, threshold=threshold)
    assert point.coverage == pytest.approx(2 / 3)
    assert point.ordinary_risk == pytest.approx(0.5)


def test_minimum_governed_coverage_prevents_selective_evasion():
    decisions = (
        DecisionRecord("o1", "s1", 0.95, True, True, False, False),
        DecisionRecord("o2", "s1", 0.90, True, True, False, False),
        DecisionRecord("g1", "s2", 0.20, True, True, True, True),
        DecisionRecord("g2", "s2", 0.10, True, True, True, True),
    )
    unconstrained = safe_coverage(decisions)
    constrained = safe_coverage(decisions, min_governed_coverage=0.5)
    assert unconstrained.coverage == pytest.approx(0.5)
    assert unconstrained.governed_coverage == 0.0
    assert constrained.coverage == 0.0


def test_rectangular_alignment_leaves_extra_predictions_unmatched():
    pairs = maximum_weight_alignment(
        ("g",),
        ("p0", "p1", "p2"),
        lambda left, right: {"p0": 0.2, "p1": 0.9, "p2": 0.7}[right],
        minimum_score=0.5,
    )
    assert len(pairs) == 1
    assert pairs[0].predicted_index == 1
