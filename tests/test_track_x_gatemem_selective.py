from __future__ import annotations

import pytest

from mindmap.track_x.gatemem_selective import (
    GateMemSelectiveError,
    audit_gate_mem_scores,
)


def _row(
    query_type: str,
    action: str,
    *,
    utility_correct: bool | None = None,
    privacy_e2e_leak: bool | None = None,
    deletion_e2e_leak: bool | None = None,
    prompt_context_chars: int = 0,
) -> dict[str, object]:
    return {
        "query_type": query_type,
        "pred_action": action,
        "utility_correct": utility_correct,
        "privacy_e2e_leak": privacy_e2e_leak,
        "deletion_e2e_leak": deletion_e2e_leak,
        "aux": {"prompt_context_chars": prompt_context_chars},
    }


def test_zero_coverage_has_undefined_conditional_risk_not_safe_answers():
    audit = audit_gate_mem_scores(
        (
            _row("utility", "no_memory", utility_correct=False),
            _row("privacy", "no_memory", privacy_e2e_leak=False),
            _row("safety", "no_memory", deletion_e2e_leak=False),
        )
    )

    assert audit.action_counts == {"no_memory": 3}
    assert audit.all_checkpoints.total == 3
    assert audit.all_checkpoints.answered == 0
    assert audit.all_checkpoints.coverage == 0.0
    assert audit.utility.conditional_risk is None
    assert audit.governed.conditional_risk is None
    assert audit.fixed_operating_point == {
        "max_ordinary_risk": 0.05,
        "max_governance_risk": 0.01,
        "ordinary_constraint_satisfied": False,
        "governance_constraint_satisfied": False,
        "safe_coverage": 0.0,
        "note": (
            "This endpoint has no confidence threshold sweep. Safe coverage "
            "is its single fixed operating point only."
        ),
    }
    assert audit.prompt_exposure_all.rows == 3
    assert audit.prompt_exposure_all.rows_with_context == 0
    assert audit.prompt_exposure_all.mean_characters_exposed_rows is None


def test_answered_denominators_separate_coverage_risk_and_prompt_exposure():
    scores = (
        _row(
            "utility",
            "answer",
            utility_correct=True,
            prompt_context_chars=100,
        ),
        _row(
            "utility",
            "answer",
            utility_correct=False,
            prompt_context_chars=80,
        ),
        _row("utility", "no_memory", utility_correct=False),
        _row(
            "privacy",
            "answer_redacted",
            privacy_e2e_leak=False,
            prompt_context_chars=50,
        ),
        _row(
            "privacy",
            "answer",
            privacy_e2e_leak=True,
            prompt_context_chars=60,
        ),
        _row(
            "safety",
            "answer",
            deletion_e2e_leak=False,
            prompt_context_chars=70,
        ),
    )
    audit = audit_gate_mem_scores(
        scores,
        max_ordinary_risk=0.50,
        max_governance_risk=0.34,
    )

    assert audit.action_counts == {
        "answer": 4,
        "answer_redacted": 1,
        "no_memory": 1,
    }
    assert audit.all_checkpoints.total == 6
    assert audit.all_checkpoints.answered == 5
    assert audit.all_checkpoints.coverage == pytest.approx(5 / 6)
    assert audit.all_checkpoints.failures == 2
    assert audit.all_checkpoints.conditional_risk == pytest.approx(2 / 5)

    assert audit.utility.total == 3
    assert audit.utility.answered == 2
    assert audit.utility.failures == 1
    assert audit.utility.conditional_risk == pytest.approx(1 / 2)
    assert audit.utility.unconditional_failure_rate == pytest.approx(1 / 3)

    assert audit.privacy.total == 2
    assert audit.privacy.answered == 2
    assert audit.privacy.failures == 1
    assert audit.privacy.conditional_risk == pytest.approx(1 / 2)
    assert audit.deletion.conditional_risk == 0.0
    assert audit.governed.total == 3
    assert audit.governed.answered == 3
    assert audit.governed.failures == 1
    assert audit.governed.conditional_risk == pytest.approx(1 / 3)

    assert audit.fixed_operating_point["ordinary_constraint_satisfied"] is True
    assert audit.fixed_operating_point["governance_constraint_satisfied"] is True
    assert audit.fixed_operating_point["safe_coverage"] == pytest.approx(5 / 6)

    prompt = audit.prompt_exposure_all
    assert prompt.rows == 6
    assert prompt.rows_with_context == 5
    assert prompt.context_coverage == pytest.approx(5 / 6)
    assert prompt.total_characters == 360
    assert prompt.mean_characters_all_rows == 60
    assert prompt.mean_characters_exposed_rows == 72
    assert audit.prompt_exposure_by_query_type["utility"].total_characters == 180
    assert audit.prompt_exposure_by_query_type["privacy"].total_characters == 110
    assert audit.prompt_exposure_by_query_type["safety"].total_characters == 70


def test_selective_audit_rejects_unknown_actions_bad_types_and_limits():
    with pytest.raises(GateMemSelectiveError, match="unsupported prediction action"):
        audit_gate_mem_scores((_row("utility", "maybe", utility_correct=True),))

    bad_bool = _row("utility", "answer", utility_correct=True)
    bad_bool["utility_correct"] = "yes"
    with pytest.raises(GateMemSelectiveError, match="boolean or null"):
        audit_gate_mem_scores((bad_bool,))

    bad_prompt = _row("privacy", "answer", privacy_e2e_leak=False)
    bad_prompt["aux"] = {"prompt_context_chars": -1}
    with pytest.raises(GateMemSelectiveError, match="non-negative integer"):
        audit_gate_mem_scores((bad_prompt,))

    with pytest.raises(GateMemSelectiveError, match="max_ordinary_risk"):
        audit_gate_mem_scores((), max_ordinary_risk=1.1)
