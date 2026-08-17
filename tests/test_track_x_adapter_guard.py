from __future__ import annotations

from copy import deepcopy

import pytest

from mindmap.track_x.adapter_guard import (
    HiddenAnnotationError,
    HiddenPathRule,
    PredictionCoverageError,
    assert_hidden_annotations_absent,
    assert_prediction_coverage_complete,
    canonical_json_sha256,
    prediction_coverage,
    scan_hidden_annotations,
    strip_hidden_annotations,
)
from mindmap.track_x.benchmark_specs import (
    BENCHMARK_SPEC_BY_NAME,
    GATEMEM,
    HALUMEM,
    LOCOMO_PLUS,
    LONGMEMEVAL_V2,
)


def test_gatemem_guard_removes_scorer_only_fields_and_preserves_visible_query():
    checkpoint = {
        "checkpoint_id": "ckpt-1",
        "as_of_turn_id": "t054",
        "asker": {"principal_id": "p1", "role": "patient"},
        "query_text": "What is my current appointment?",
        "query_type": "privacy",
        "attack_type": "role_mismatch",
        "expected_action": "refuse",
        "judge_spec": {"not_include": ["secret"]},
        "leak_targets": ["secret"],
        "gold_answer_structured": {"value": "secret"},
        "gold_refusal_category": "access_control",
        "policy_snapshot": {"allow": False},
    }
    original = deepcopy(checkpoint)
    result = strip_hidden_annotations(checkpoint, GATEMEM.hidden_paths)

    assert checkpoint == original
    assert result.payload == {
        "checkpoint_id": "ckpt-1",
        "as_of_turn_id": "t054",
        "asker": {"principal_id": "p1", "role": "patient"},
        "query_text": "What is my current appointment?",
    }
    assert set(result.removed_paths) == {
        "$.attack_type",
        "$.expected_action",
        "$.gold_answer_structured",
        "$.gold_refusal_category",
        "$.judge_spec",
        "$.leak_targets",
        "$.policy_snapshot",
        "$.query_type",
    }
    assert result.source_sha256 != result.payload_sha256
    assert_hidden_annotations_absent(result.payload, GATEMEM.hidden_paths)


def test_gatemem_guard_redacts_wrapped_checkpoint_before_agent_code_receives_it():
    wrapped = {
        "episode_id": "e1",
        "checkpoint": {
            "checkpoint_id": "c1",
            "query_text": "What may I see?",
            "query_type": "privacy",
            "expected_action": "answer_redacted",
            "policy_snapshot": {"scope": "logistics_only"},
        },
    }
    result = strip_hidden_annotations(wrapped, GATEMEM.hidden_paths)
    assert result.payload == {
        "episode_id": "e1",
        "checkpoint": {
            "checkpoint_id": "c1",
            "query_text": "What may I see?",
        },
    }


def test_halumem_guard_keeps_dialogue_and_question_but_removes_gold_layers():
    user = {
        "uuid": "u1",
        "persona_info": "A careful user",
        "sessions": [
            {
                "dialogue": [{"role": "user", "content": "I moved to Busan."}],
                "memory_points": ["The user moved to Busan."],
                "questions": [
                    {
                        "question": "Where does the user live?",
                        "answer": "Busan",
                        "evidence": ["I moved to Busan."],
                    }
                ],
            }
        ],
    }
    result = strip_hidden_annotations(user, HALUMEM.hidden_paths)
    question = result.payload["sessions"][0]["questions"][0]

    assert result.payload["sessions"][0]["dialogue"] == user["sessions"][0]["dialogue"]
    assert question == {"question": "Where does the user live?"}
    assert "memory_points" not in result.payload["sessions"][0]
    assert set(result.removed_paths) == {
        "$.sessions[0].memory_points",
        "$.sessions[0].questions[0].answer",
        "$.sessions[0].questions[0].evidence",
    }


def test_locomo_plus_guard_keeps_model_input_and_trigger_but_hides_judge_data():
    sample = {
        "sample_id": "cog-1",
        "input_prompt": "Earlier conversation ... later query ...",
        "trigger": "What should I remember before deciding?",
        "category": "Cognitive",
        "evidence": "The earlier cue said to avoid crowds.",
        "answer": "Avoid crowds.",
    }
    result = strip_hidden_annotations(sample, LOCOMO_PLUS.hidden_paths)
    assert result.payload == {
        "sample_id": "cog-1",
        "input_prompt": "Earlier conversation ... later query ...",
        "trigger": "What should I remember before deciding?",
        "category": "Cognitive",
    }


def test_guard_detects_hidden_values_without_mutating_payload():
    payload = {"visible": 1, "nested": {"gold": 2}}
    rules = (HiddenPathRule(("nested", "gold"), "gold annotation"),)
    hits = scan_hidden_annotations(payload, rules)
    assert [hit.path for hit in hits] == ["$.nested.gold"]
    with pytest.raises(HiddenAnnotationError, match=r"\$\.nested\.gold"):
        assert_hidden_annotations_absent(payload, rules)


def test_canonical_digest_is_stable_under_mapping_key_order():
    left = {"b": [2, 1], "a": {"x": "한글"}}
    right = {"a": {"x": "한글"}, "b": [2, 1]}
    assert canonical_json_sha256(left) == canonical_json_sha256(right)


def test_prediction_coverage_reports_missing_unexpected_and_duplicate_ids():
    report = prediction_coverage(
        ("c1", "c2", "c3"),
        ("c1", "c1", "c3", "extra"),
    )
    assert report.expected_count == 3
    assert report.observed_count == 4
    assert report.unique_observed_count == 3
    assert report.missing_ids == ("c2",)
    assert report.unexpected_ids == ("extra",)
    assert report.duplicate_ids == ("c1",)
    assert not report.complete
    with pytest.raises(PredictionCoverageError):
        assert_prediction_coverage_complete(
            ("c1", "c2", "c3"),
            ("c1", "c1", "c3", "extra"),
        )


def test_prediction_coverage_rejects_duplicate_expected_ids():
    with pytest.raises(ValueError, match="not unique"):
        prediction_coverage(("c1", "c1"), ("c1",))


def test_external_specs_are_pinned_and_have_distinct_names():
    assert set(BENCHMARK_SPEC_BY_NAME) == {
        "GateMem",
        "HaluMem",
        "LoCoMo-Plus",
        "LongMemEval-V2",
    }
    for spec in (GATEMEM, HALUMEM, LOCOMO_PLUS, LONGMEMEVAL_V2):
        assert len(spec.audited_commit) == 40
        assert spec.official_metrics
        assert spec.output_contract
