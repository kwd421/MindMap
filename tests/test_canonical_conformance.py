from __future__ import annotations

import inspect

import pytest

from mindmap.canonical.evaluate import evaluate_fixtures, summarize
from mindmap.canonical.fixtures import all_fixtures
from mindmap.canonical.generic import GenericLedger
from mindmap.canonical.gold import GoldSemantics
from mindmap.canonical.model import CommonEvent, TargetSpace
from mindmap.canonical.typed import TypedLedger


@pytest.fixture(scope="module")
def rows():
    return evaluate_fixtures(all_fixtures())


def test_fixed_s_suite_has_target_coverage(rows):
    summary = summarize(rows)
    assert summary["n_fixtures"] == 14
    assert summary["n_cases"] >= 70
    assert set(summary["target_counts"]) == {target.value for target in TargetSpace}


def test_gold_generic_and_typed_conform_exactly(rows):
    failures = [row for row in rows if not row.all_agree]
    assert failures == []


def test_gold_module_does_not_import_implementation_resolvers():
    import mindmap.canonical.gold as gold_module

    source = inspect.getsource(gold_module)
    assert "from .generic" not in source
    assert "from .typed" not in source
    assert "GenericLedger" not in source
    assert "TypedLedger" not in source


def test_common_event_contract_contains_no_expected_answer_field():
    field_names = set(CommonEvent.__dataclass_fields__)
    forbidden = {"expected", "answer", "correct", "eligible", "current", "first_person"}
    assert field_names.isdisjoint(forbidden)


def test_world_branch_late_import_pair_is_present(rows):
    f01 = {row.invariant: row for row in rows if row.fixture_id == "F01"}
    assert f01["postfork_parent_update_not_inherited"].expected == "Room 1"
    assert f01["late_import_of_prefork_fact_visible"].expected == "Room 0"


def test_snapshot_manifest_is_object_selective(rows):
    f08 = {row.invariant: row for row in rows if row.fixture_id == "F08"}
    assert f08["manifest_member_inherited"].expected is True
    assert f08["post_snapshot_recovery_gap"].expected is False


def test_equal_information_implementations_receive_identical_events():
    fixture = all_fixtures()[0]
    generic = GenericLedger(fixture.events)
    typed = TypedLedger(fixture.events)
    assert generic.events == typed.common_events


def test_mutating_about_world_scope_is_detected_by_gold_fixture():
    fixture = next(fixture for fixture in all_fixtures() if fixture.fixture_id == "F09")
    mutated = tuple(
        CommonEvent(
            **{
                **{name: getattr(event, name) for name in event.__dataclass_fields__},
                "about_world_branch_id": "W2",
            }
        )
        if event.event_id == "F09.a"
        else event
        for event in fixture.events
    )
    query = next(case.query for case in fixture.cases if case.invariant == "attitude_held_in_w2_about_w1")
    assert GoldSemantics(fixture.events).answer(query) == "believe"
    assert GoldSemantics(mutated).answer(query) == "unknown"


def test_revoked_authorization_mutation_changes_replication_state():
    fixture = next(fixture for fixture in all_fixtures() if fixture.fixture_id == "F13")
    query = next(case.query for case in fixture.cases if case.invariant == "authorized_same_principal_replication")
    assert GoldSemantics(fixture.events).answer(query) is True
    mutated = tuple(
        CommonEvent(
            **{
                **{name: getattr(event, name) for name in event.__dataclass_fields__},
                "policy_operation": "revoke",
            }
        )
        if event.event_id == "F13.ag"
        else event
        for event in fixture.events
    )
    assert GoldSemantics(mutated).answer(query) is False
