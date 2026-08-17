from __future__ import annotations

from dataclasses import replace

from mindmap.canonical.fixtures import all_fixtures
from mindmap.canonical.gold import GoldSemantics
from mindmap.canonical.model import Answer, Fixture, TargetQuery

from .physical import PhysicalFaultCase


def _fixture(fixture_id: str) -> Fixture:
    return next(value for value in all_fixtures() if value.fixture_id == fixture_id)


def _query(fixture: Fixture, query_id: str) -> TargetQuery:
    return next(case.query for case in fixture.cases if case.query.query_id == query_id)


def _case(
    *,
    case_id: str,
    family: str,
    fixture_id: str,
    query_ids: tuple[str, ...],
    journal_events=None,
    projection_events=None,
    overrides: dict[str, Answer] | None = None,
    observe_external_journal_commitment: bool = True,
    observe_projection_commitment: bool = True,
    clean_control: bool = False,
    identifiable: bool = True,
    repair_authority_available: bool = True,
    notes: str = "",
) -> PhysicalFaultCase:
    fixture = _fixture(fixture_id)
    clean = tuple(fixture.events)
    queries = tuple(_query(fixture, query_id) for query_id in query_ids)
    gold = GoldSemantics(clean)
    expected = tuple((query.query_id, gold.answer(query)) for query in queries)
    return PhysicalFaultCase(
        case_id=case_id,
        family=family,
        clean_events=clean,
        faulty_journal_events=tuple(clean if journal_events is None else journal_events),
        faulty_projection_events=tuple(
            clean if projection_events is None else projection_events
        ),
        queries=queries,
        expected_answers=expected,
        projection_overrides=tuple(sorted((overrides or {}).items())),
        observe_external_journal_commitment=observe_external_journal_commitment,
        observe_projection_commitment=observe_projection_commitment,
        clean_control=clean_control,
        identifiable=identifiable,
        repair_authority_available=repair_authority_available,
        notes=notes,
    )


def crash_after_revoke_before_projection() -> PhysicalFaultCase:
    fixture = _fixture("F10")
    projection = tuple(
        event for event in fixture.events if event.event_id != "F10.r"
    )
    return _case(
        case_id="P01",
        family="crash_after_revoke_before_projection",
        fixture_id="F10",
        query_ids=("F10.q4", "F10.q5"),
        projection_events=projection,
        notes="Journal contains revoke; projection remains at the pre-revoke head.",
    )


def crash_after_seal_before_projection() -> PhysicalFaultCase:
    fixture = _fixture("F07")
    projection = tuple(
        event for event in fixture.events if event.event_id != "F07.seal"
    )
    return _case(
        case_id="P02",
        family="crash_after_self_seal_before_projection",
        fixture_id="F07",
        query_ids=("F07.q2", "F07.q3"),
        projection_events=projection,
    )


def partial_restore_projection() -> PhysicalFaultCase:
    fixture = _fixture("F08")
    projection = tuple(
        event for event in fixture.events if event.event_id != "F08.l"
    )
    return _case(
        case_id="P03",
        family="restore_lineage_missing_from_projection",
        fixture_id="F08",
        query_ids=("F08.q1", "F08.q3", "F08.q4", "F08.q5"),
        projection_events=projection,
    )


def replication_projection_stale() -> PhysicalFaultCase:
    fixture = _fixture("F13")
    projection = tuple(
        event for event in fixture.events if event.event_id != "F13.rep"
    )
    return _case(
        case_id="P04",
        family="authorized_replication_missing_from_projection",
        fixture_id="F13",
        query_ids=("F13.q2", "F13.q3", "F13.q4"),
        projection_events=projection,
    )


def revocation_projection_stale_support_path() -> PhysicalFaultCase:
    fixture = _fixture("F11")
    projection = tuple(
        event for event in fixture.events if event.event_id != "F11.rs"
    )
    return _case(
        case_id="P05",
        family="revoked_private_support_remains_in_projection",
        fixture_id="F11",
        query_ids=("F11.q4",),
        projection_events=projection,
    )


def late_import_projection_stale() -> PhysicalFaultCase:
    fixture = _fixture("F01")
    projection = tuple(
        event for event in fixture.events if event.event_id != "F01.c0"
    )
    return _case(
        case_id="P06",
        family="late_prefork_import_missing_from_projection",
        fixture_id="F01",
        query_ids=("F01.q3",),
        projection_events=projection,
    )


def committed_journal_omission() -> PhysicalFaultCase:
    fixture = _fixture("F10")
    faulty = tuple(
        event for event in fixture.events if event.event_id != "F10.r"
    )
    return _case(
        case_id="P07",
        family="authoritative_journal_revoke_omitted",
        fixture_id="F10",
        query_ids=("F10.q4", "F10.q5"),
        journal_events=faulty,
        projection_events=faulty,
    )


def committed_append_order_change() -> PhysicalFaultCase:
    fixture = _fixture("F14")
    events = list(fixture.events)
    events[-1], events[-2] = events[-2], events[-1]
    faulty = tuple(events)
    return _case(
        case_id="P08",
        family="authoritative_append_order_changed",
        fixture_id="F14",
        query_ids=("F14.q1", "F14.q2", "F14.q5"),
        journal_events=faulty,
        projection_events=faulty,
        notes="Semantic answers remain equal; the append-order commitment changes.",
    )


def committed_duplicate_replay() -> PhysicalFaultCase:
    fixture = _fixture("F14")
    duplicate = next(
        event for event in fixture.events if event.event_id == "F14.x"
    )
    faulty = tuple(fixture.events) + (duplicate,)
    return _case(
        case_id="P09",
        family="duplicate_event_replayed_into_journal",
        fixture_id="F14",
        query_ids=("F14.q3", "F14.q4"),
        journal_events=faulty,
        projection_events=faulty,
    )


def projection_content_corruption() -> PhysicalFaultCase:
    fixture = _fixture("F14")
    query = _query(fixture, "F14.q5")
    return _case(
        case_id="P10",
        family="projection_row_content_corrupted",
        fixture_id="F14",
        query_ids=("F14.q5",),
        overrides={query.query_id: False},
    )


def projection_built_from_wrong_but_answer_equivalent_prefix() -> PhysicalFaultCase:
    fixture = _fixture("F14")
    projection = tuple(
        event for event in fixture.events if event.event_id != "F14.a"
    )
    return _case(
        case_id="P11",
        family="projection_bound_to_wrong_journal_head_with_equal_answer",
        fixture_id="F14",
        query_ids=("F14.q1", "F14.q2"),
        projection_events=projection,
        notes="The selected world answers happen to match; head binding still exposes staleness.",
    )


def unwitnessed_journal_omission() -> PhysicalFaultCase:
    fixture = _fixture("F10")
    faulty = tuple(
        event for event in fixture.events if event.event_id != "F10.r"
    )
    return _case(
        case_id="P12",
        family="unwitnessed_revoke_omission",
        fixture_id="F10",
        query_ids=("F10.q4",),
        journal_events=faulty,
        projection_events=faulty,
        observe_external_journal_commitment=False,
        observe_projection_commitment=False,
        identifiable=False,
        repair_authority_available=False,
        notes="No external journal or projection witness binds the omitted revoke.",
    )


def clean_fully_synchronized() -> PhysicalFaultCase:
    return _case(
        case_id="PC01",
        family="clean_fully_synchronized",
        fixture_id="F14",
        query_ids=("F14.q1", "F14.q2", "F14.q3", "F14.q4", "F14.q5"),
        clean_control=True,
    )


def clean_authenticated_revocation() -> PhysicalFaultCase:
    return _case(
        case_id="PC02",
        family="clean_authenticated_revocation",
        fixture_id="F10",
        query_ids=("F10.q4", "F10.q5"),
        clean_control=True,
    )


def clean_snapshot_projection() -> PhysicalFaultCase:
    return _case(
        case_id="PC03",
        family="clean_snapshot_projection",
        fixture_id="F08",
        query_ids=("F08.q1", "F08.q2", "F08.q3", "F08.q4", "F08.q5", "F08.q6"),
        clean_control=True,
    )


def all_physical_cases() -> tuple[PhysicalFaultCase, ...]:
    return (
        crash_after_revoke_before_projection(),
        crash_after_seal_before_projection(),
        partial_restore_projection(),
        replication_projection_stale(),
        revocation_projection_stale_support_path(),
        late_import_projection_stale(),
        committed_journal_omission(),
        committed_append_order_change(),
        committed_duplicate_replay(),
        projection_content_corruption(),
        projection_built_from_wrong_but_answer_equivalent_prefix(),
        unwitnessed_journal_omission(),
        clean_fully_synchronized(),
        clean_authenticated_revocation(),
        clean_snapshot_projection(),
    )
