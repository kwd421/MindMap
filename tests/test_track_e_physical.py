from mindmap.track_e.physical import (
    GenericPhysicalStore,
    TypedPhysicalStore,
    run_physical_case,
)
from mindmap.track_e.physical_evaluate import evaluate_physical_suite
from mindmap.track_e.physical_fixtures import all_physical_cases


def _results(case):
    return (
        run_physical_case(case, GenericPhysicalStore),
        run_physical_case(case, TypedPhysicalStore),
    )


def test_clean_controls_are_synchronized_and_unflagged():
    for case in all_physical_cases():
        if not case.clean_control:
            continue
        for result in _results(case):
            assert not result.detected, (case.case_id, result)
            assert result.pre_repair_correct
            assert not result.silent_incorrect_use
            assert not result.repair_attempted
            assert result.residue_after_repair == 0


def test_identifiable_physical_faults_are_detected_and_repaired():
    for case in all_physical_cases():
        if case.clean_control or not case.identifiable:
            continue
        for result in _results(case):
            assert result.detected, (case.case_id, result)
            assert result.repair_attempted
            assert result.repair_success, (case.case_id, result)
            assert result.residue_after_repair == 0


def test_unwitnessed_omission_remains_silent_and_wrong():
    case = next(case for case in all_physical_cases() if not case.identifiable)
    for result in _results(case):
        assert not result.detected
        assert not result.pre_repair_correct
        assert result.silent_incorrect_use
        assert not result.repair_attempted
        assert result.residue_after_repair == 1


def test_projection_faults_are_separated_from_journal_faults():
    cases = {case.case_id: case for case in all_physical_cases()}
    for result in _results(cases["P01"]):
        assert not result.journal_commitment_mismatch
        assert result.projection_head_mismatch
        assert result.projection_content_mismatch
    for result in _results(cases["P07"]):
        assert result.journal_commitment_mismatch
        assert not result.projection_head_mismatch
        assert result.projection_content_mismatch
    for result in _results(cases["P08"]):
        assert result.journal_commitment_mismatch
        assert not result.projection_head_mismatch
        assert not result.projection_content_mismatch
    for result in _results(cases["P10"]):
        assert not result.journal_commitment_mismatch
        assert not result.projection_head_mismatch
        assert result.projection_content_mismatch
    for result in _results(cases["P11"]):
        assert not result.journal_commitment_mismatch
        assert result.projection_head_mismatch
        assert not result.projection_content_mismatch


def test_generic_and_typed_physical_outcomes_match_on_fixed_suite():
    rows, summary = evaluate_physical_suite(all_physical_cases())
    assert len(rows) == 2 * len(all_physical_cases())
    assert summary["outcome_disagreements"] == {}
    for values in summary["implementations"].values():
        assert values["identifiable_detection_recall"] == 1.0
        assert values["clean_false_alarm_rate"] == 0.0
        assert values["silent_incorrect_use_rate_identifiable"] == 0.0
        assert values["repair_success_rate"] == 1.0
        assert values["total_residue_after_repair"] == 0


def test_full_rebuild_cost_is_explicit_and_equal():
    _, summary = evaluate_physical_suite(all_physical_cases())
    values = list(summary["implementations"].values())
    assert len(values) == 2
    assert values[0]["mean_repair_events_reprocessed"] == values[1]["mean_repair_events_reprocessed"]
    assert values[0]["mean_repair_query_recomputations"] == values[1]["mean_repair_query_recomputations"]
