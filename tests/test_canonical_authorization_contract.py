from __future__ import annotations

import pytest

from mindmap.canonical.fixture_common import E, base_identity
from mindmap.canonical.generic import GenericLedger
from mindmap.canonical.gold import GoldSemantics
from mindmap.canonical.model import TargetQuery, TargetSpace
from mindmap.canonical.typed import TypedLedger


SYSTEMS = (GoldSemantics, GenericLedger, TypedLedger)


def _query() -> TargetQuery:
    return TargetQuery(
        query_id="AUTH.q",
        target_space=TargetSpace.AVAILABLE,
        system_time=10,
        evidence_id="E.sync",
        mind_instance_id="R4",
    )


def _base() -> list:
    events = base_identity(
        "AUTH",
        minds=(("R1", "P"), ("R2", "P"), ("R3", "P"), ("R4", "P")),
    )
    events += [
        E(
            "AUTH.l34",
            "lineage",
            1,
            lineage_kind="operational_replica",
            source_mind_instance_id="R3",
            destination_mind_instance_id="R4",
        ),
        E(
            "AUTH.e",
            "evidence",
            2,
            object_id="E.sync",
            proposition_id="sync_p",
            actor_principal_id="P",
            actor_mind_instance_id="R3",
            about_world_branch_id="main",
            source_family_id="sync-source",
        ),
        E(
            "AUTH.observe",
            "exposure",
            2,
            object_id="E.sync",
            destination_mind_instance_id="R3",
            transfer_kind="observe",
        ),
    ]
    return events


def _replication() -> object:
    return E(
        "AUTH.rep",
        "exposure",
        6,
        object_id="E.sync",
        source_mind_instance_id="R3",
        destination_mind_instance_id="R4",
        transfer_kind="state_replication",
        authorization_id="AUTH-1",
    )


def test_authorization_is_bound_to_granted_source_destination_scope() -> None:
    events = _base()
    events += [
        E(
            "AUTH.grant.wrong-scope",
            "authorization",
            3,
            object_id="AUTH-1",
            source_mind_instance_id="R1",
            destination_mind_instance_id="R2",
            policy_operation="grant",
        ),
        _replication(),
    ]

    assert [system(events).answer(_query()) for system in SYSTEMS] == [False, False, False]


def test_matching_scoped_authorization_still_allows_replication() -> None:
    events = _base()
    events += [
        E(
            "AUTH.grant.correct-scope",
            "authorization",
            3,
            object_id="AUTH-1",
            source_mind_instance_id="R3",
            destination_mind_instance_id="R4",
            policy_operation="grant",
        ),
        _replication(),
    ]

    assert [system(events).answer(_query()) for system in SYSTEMS] == [True, True, True]


def test_authorization_identifier_cannot_change_scope_across_revisions() -> None:
    events = _base()
    events += [
        E(
            "AUTH.grant.first-scope",
            "authorization",
            3,
            object_id="AUTH-1",
            source_mind_instance_id="R1",
            destination_mind_instance_id="R2",
            policy_operation="grant",
        ),
        E(
            "AUTH.grant.second-scope",
            "authorization",
            4,
            object_id="AUTH-1",
            source_mind_instance_id="R3",
            destination_mind_instance_id="R4",
            policy_operation="grant",
        ),
        _replication(),
    ]

    for system in SYSTEMS:
        with pytest.raises(ValueError, match="authorization scope changed"):
            system(events).answer(_query())


def test_conflicting_same_time_authorization_revisions_are_ambiguous() -> None:
    events = _base()
    events += [
        E(
            "AUTH.a-revoke",
            "authorization",
            3,
            object_id="AUTH-1",
            source_mind_instance_id="R3",
            destination_mind_instance_id="R4",
            policy_operation="revoke",
        ),
        E(
            "AUTH.z-grant",
            "authorization",
            3,
            object_id="AUTH-1",
            source_mind_instance_id="R3",
            destination_mind_instance_id="R4",
            policy_operation="grant",
        ),
        _replication(),
    ]

    for system in SYSTEMS:
        with pytest.raises(ValueError, match="ambiguous same-time authorization revisions"):
            system(events).answer(_query())
