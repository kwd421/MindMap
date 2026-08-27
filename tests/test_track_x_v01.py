from dataclasses import fields

from mindmap.canonical.fixtures import all_fixtures
from mindmap.track_x.evaluate import evaluate_raw_verifier_suite
from mindmap.track_x.fixtures import all_raw_verifier_cases
from mindmap.track_x.manifest import FROZEN_MANIFEST, validate_manifest
from mindmap.track_x.model import (
    CandidateCondition,
    DatasetSplit,
    VerificationStatus,
    VerifierInput,
)
from mindmap.track_x.verifier import RawEvidenceVerifier


def test_manifest_is_topology_disjoint_and_resolves_canonical_ids():
    validate_manifest()
    fixtures = {fixture.fixture_id: fixture for fixture in all_fixtures()}
    development = {
        entry.topology_family
        for entry in FROZEN_MANIFEST
        if entry.split is DatasetSplit.DEVELOPMENT
    }
    heldout = {
        entry.topology_family
        for entry in FROZEN_MANIFEST
        if entry.split is DatasetSplit.HELDOUT
    }
    assert development
    assert heldout
    assert development.isdisjoint(heldout)
    assert len(development) == len(heldout) == 7

    for entry in FROZEN_MANIFEST:
        fixture = fixtures[entry.fixture_id]
        assert fixture.family == entry.topology_family
        assert entry.event_id in {event.event_id for event in fixture.events}
        assert entry.query_id in {case.query.query_id for case in fixture.cases}


def test_verifier_input_excludes_evaluator_only_metadata():
    visible = {definition.name for definition in fields(VerifierInput)}
    forbidden = {
        "case_id",
        "topology_family",
        "split",
        "rendering_family",
        "gold_event",
        "query",
        "expected_answer",
        "condition",
        "mutated_fields",
        "recoverable_from_raw",
    }
    assert visible == {
        "raw_text",
        "candidate_event",
        "context_events",
        "insertion_index",
    }
    assert visible.isdisjoint(forbidden)


def test_clean_candidates_are_accepted_without_false_correction():
    verifier = RawEvidenceVerifier()
    for case in all_raw_verifier_cases():
        if case.condition is not CandidateCondition.CLEAN:
            continue
        decision = verifier.verify(case.verifier_input())
        assert decision.status is VerificationStatus.ACCEPT, case.case_id
        assert decision.output_event == case.gold_event, case.case_id


def test_corrupt_and_omitted_candidates_are_reconstructed_from_raw():
    verifier = RawEvidenceVerifier()
    for case in all_raw_verifier_cases():
        if case.condition not in {
            CandidateCondition.FIELD_CORRUPTION,
            CandidateCondition.CANDIDATE_OMITTED,
        }:
            continue
        decision = verifier.verify(case.verifier_input())
        assert decision.status is VerificationStatus.CORRECT, case.case_id
        assert decision.output_event == case.gold_event, case.case_id


def test_raw_unavailable_cases_abstain():
    verifier = RawEvidenceVerifier()
    for case in all_raw_verifier_cases():
        if case.condition is not CandidateCondition.RAW_UNAVAILABLE:
            continue
        decision = verifier.verify(case.verifier_input())
        assert decision.status is VerificationStatus.ABSTAIN, case.case_id
        assert decision.output_event is None


def test_evaluation_preserves_safety_and_reports_fixed_boundary():
    verification_rows, downstream_rows, summary = evaluate_raw_verifier_suite(
        all_raw_verifier_cases()
    )
    assert len(verification_rows) == 56
    assert len(downstream_rows) == 56 * 3 * 2
    assert summary["n_topology_families"] == 14

    overall = summary["verification"]["overall"]
    assert overall["decision_accuracy"] == 1.0
    assert overall["clean_false_correction_rate"] == 0.0
    assert overall["corrupted_false_accept_rate"] == 0.0
    assert overall["missing_candidate_recovery_rate"] == 1.0
    assert overall["raw_unavailable_abstention_rate"] == 1.0
    assert overall["coverage"] == 0.75
    assert overall["selective_risk"] == 0.0

    downstream = summary["downstream"]
    for split in ("development", "heldout"):
        for architecture in ("G_generic", "T_typed"):
            verified = downstream[f"{split}:raw_verifier:{architecture}"]
            ceiling = downstream[f"{split}:oracle_raw_ceiling:{architecture}"]
            assert verified["answer_accuracy"] == 0.75
            assert verified["abstention_rate"] == 0.25
            assert verified["silent_wrong_use_rate"] == 0.0
            assert verified["unsafe_disclosure_rate"] == 0.0
            assert ceiling["answer_accuracy"] == 1.0
            assert ceiling["abstention_rate"] == 0.0

            structured = downstream[f"{split}:structured_only:{architecture}"]
            expected_projection_errors = {
                "development": 6 / 28,
                "heldout": 8 / 28,
            }[split]
            expected_silent_wrong_use = {
                "development": 15 / 28,
                "heldout": 13 / 28,
            }[split]
            assert structured["answer_accuracy"] == 0.25
            assert structured["projection_error_rate"] == expected_projection_errors
            assert structured["abstention_rate"] == expected_projection_errors
            assert structured["silent_wrong_use_rate"] == expected_silent_wrong_use

    non_structured_disagreements = {
        key: value
        for key, value in summary["generic_typed_disagreements"].items()
        if not key.endswith(":structured_only")
    }
    assert non_structured_disagreements == {}
