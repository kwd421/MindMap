from pathlib import Path

from mindmap.track_x.v02_bundles import expand_bundles, load_bundle_json
from mindmap.track_x.v02_cases import (
    build_development_cases,
    expected_controlled_status,
    expected_primary_status,
)
from mindmap.track_x.v02_data import PassageCondition
from mindmap.track_x.v02_evaluate import evaluate_development


ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = (
    ROOT
    / "data"
    / "track_x_v02"
    / "development"
    / "session_b.json"
)


def test_session_b_bundle_expands_all_development_conditions():
    bundles = load_bundle_json(BUNDLE_PATH, split="development")
    assert len(bundles) == 7
    assert {bundle.author_session for bundle in bundles} == {"B"}
    records = expand_bundles(bundles, split="development")
    assert len(records) == 42
    for topology in {record.topology_family for record in records}:
        conditions = {
            record.candidate_condition
            for record in records
            if record.topology_family == topology
        }
        assert conditions == set(PassageCondition)


def test_complete_passages_are_primary_parseable_but_ambiguous_passages_are_not():
    cases = build_development_cases(repository_root=ROOT)
    for case in cases:
        condition = case.record.candidate_condition
        if condition in {
            PassageCondition.CLEAN,
            PassageCondition.FIELD_CORRUPTION,
            PassageCondition.CANDIDATE_OMITTED,
            PassageCondition.MISLEADING_CONTEXT,
        }:
            assert (
                case.primary_extraction.event == case.gold_event
            ), case.record.passage_id
        elif condition in {
            PassageCondition.AMBIGUOUS_RAW,
            PassageCondition.RAW_UNAVAILABLE,
        }:
            assert case.primary_extraction.event is None, case.record.passage_id


def test_independent_verifier_tracks_primary_and_controlled_candidates_separately():
    cases = build_development_cases(repository_root=ROOT)
    for case in cases:
        condition = case.record.candidate_condition
        primary_expected = expected_primary_status(condition)
        controlled_expected = expected_controlled_status(condition)

        assert (
            case.primary_verifier_decision.status is primary_expected
        ), case.record.passage_id
        assert (
            case.controlled_verifier_decision.status is controlled_expected
        ), case.record.passage_id

        if primary_expected.value in {"accept", "correct"}:
            assert case.primary_verifier_decision.output_event == case.gold_event
        else:
            assert case.primary_verifier_decision.output_event is None

        if controlled_expected.value in {"accept", "correct"}:
            assert case.controlled_verifier_decision.output_event == case.gold_event
        else:
            assert case.controlled_verifier_decision.output_event is None


def test_development_evaluator_preserves_safety_and_generic_typed_equality():
    verification_rows, downstream_rows, summary = evaluate_development(ROOT)
    assert len(verification_rows) == 42
    assert len(downstream_rows) == 42 * 5 * 2
    assert summary["n_topologies"] == 7
    assert summary["generic_typed_disagreements"] == {}

    verification = summary["verification"]
    assert verification["primary_verifier"]["status_accuracy"] == 1.0
    assert verification["primary_verifier"]["covered_output_exact_rate"] == 1.0
    assert verification["controlled_verifier"]["status_accuracy"] == 1.0
    assert (
        verification["controlled_verifier"]["covered_output_exact_rate"]
        == 1.0
    )
    assert verification["primary_clean_false_correction_rate"] == 0.0
    assert verification["controlled_clean_false_correction_rate"] == 0.0
    assert verification["controlled_false_accept_rate"] == 0.0
    assert verification["primary_ambiguous_abstention_rate"] == 1.0
    assert verification["controlled_ambiguous_abstention_rate"] == 1.0
    assert verification["primary_raw_unavailable_abstention_rate"] == 1.0
    assert (
        verification["controlled_raw_unavailable_abstention_rate"] == 1.0
    )
    assert verification["controlled_misleading_context_correction_rate"] == 1.0

    for architecture in ("G_generic", "T_typed"):
        primary = summary["downstream"][
            f"primary_extractor_only:{architecture}"
        ]
        primary_verified = summary["downstream"][
            f"primary_plus_verifier:{architecture}"
        ]
        controlled_verified = summary["downstream"][
            f"controlled_plus_verifier:{architecture}"
        ]
        oracle = summary["downstream"][f"oracle_raw_ceiling:{architecture}"]

        for result in (primary, primary_verified, controlled_verified):
            assert result["answer_accuracy"] == 2 / 3
            assert result["abstention_rate"] == 1 / 3
            assert result["silent_wrong_use_rate"] == 0.0
            assert result["unsafe_disclosure_rate"] == 0.0
        assert oracle["answer_accuracy"] == 1.0
        assert oracle["abstention_rate"] == 0.0
