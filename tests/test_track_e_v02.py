from mindmap.canonical.gold import GoldSemantics
from mindmap.track_e.evaluate import evaluate_suite
from mindmap.track_e.fixtures import all_fault_cases
from mindmap.track_e.model import ObserverSurface
from mindmap.track_e.observers import GenericObserver, TypedObserver


def _surface(case):
    return ObserverSurface.SEMANTIC_JOURNAL if not case.identifiable else case.required_surface


def _alerts(observer, case):
    return observer.inspect(
        case.faulty_events,
        surface=_surface(case),
        journal_commitment=case.journal_commitment,
        projection_commitment=case.projection_commitment,
        projection_rows=case.faulty_projection_rows,
    )


def test_clean_expected_answers_are_generated_by_independent_gold():
    for case in all_fault_cases():
        assert GoldSemantics(case.clean_events).answer(case.query) == case.expected_clean_answer


def test_clean_controls_have_no_false_alerts():
    for case in all_fault_cases():
        if not case.clean_control:
            continue
        assert not _alerts(GenericObserver(), case), case.case_id
        assert not _alerts(TypedObserver(), case), case.case_id


def test_every_identifiable_fault_is_detected_by_both_observers():
    for case in all_fault_cases():
        if case.clean_control or not case.identifiable:
            continue
        assert _alerts(GenericObserver(), case), case.case_id
        assert _alerts(TypedObserver(), case), case.case_id


def test_unwitnessed_omission_is_not_falsely_detected():
    case = next(case for case in all_fault_cases() if not case.identifiable)
    assert not _alerts(GenericObserver(), case)
    assert not _alerts(TypedObserver(), case)


def test_forward_reference_faults_are_order_independent():
    cases = {
        case.case_id: case
        for case in all_fault_cases()
        if case.case_id in {"E08", "E09"}
    }
    for observer in (GenericObserver(), TypedObserver()):
        laundering = {alert.rule for alert in _alerts(observer, cases["E08"])}
        independence = {alert.rule for alert in _alerts(observer, cases["E09"])}
        assert any("policy_laundering" in rule for rule in laundering)
        assert any("non_independent_support" in rule for rule in independence)


def test_external_commitment_is_order_sensitive_and_out_of_band():
    case = next(case for case in all_fault_cases() if case.case_id == "E12")
    for observer in (GenericObserver(), TypedObserver()):
        rules = {alert.rule for alert in _alerts(observer, case)}
        assert any("sequence_or_membership_mismatch" in rule for rule in rules)
        assert any("journal_head_mismatch" in rule for rule in rules)


def test_projection_commitment_detects_stale_rows():
    case = next(case for case in all_fault_cases() if case.case_id == "E13")
    for observer in (GenericObserver(), TypedObserver()):
        rules = {alert.rule for alert in _alerts(observer, case)}
        assert any("projection_content_mismatch" in rule for rule in rules)


def test_evaluation_reports_no_generic_typed_outcome_disagreement():
    rows, summary = evaluate_suite(all_fault_cases())
    assert len(rows) == 2 * len(all_fault_cases())
    assert summary["outcome_disagreements"] == {}
    for observer_summary in summary["observers"].values():
        assert observer_summary["identifiable_detection_recall"] == 1.0
        assert observer_summary["clean_false_alarm_rate"] == 0.0
        assert observer_summary["non_identifiable_detected"] == 0
