from __future__ import annotations

import pytest

from mindmap.canonical.generic import GenericLedger
from mindmap.canonical.gold import GoldSemantics
from mindmap.canonical.model import (
    CommonEvent,
    freeze_attrs,
    validate_temporal_references,
)
from mindmap.canonical.typed import TypedLedger


IMPLEMENTATIONS = (GoldSemantics, GenericLedger, TypedLedger)


def event(event_id: str, event_type: str, system_time: int, **kwargs) -> CommonEvent:
    attributes = kwargs.pop("attributes", {})
    return CommonEvent(
        event_id=event_id,
        event_type=event_type,
        system_time=system_time,
        attributes=freeze_attrs(attributes),
        **kwargs,
    )


@pytest.mark.parametrize("implementation", IMPLEMENTATIONS)
def test_future_created_replication_destination_is_rejected(implementation):
    events = (
        event("principal", "principal_create", 0, object_id="P"),
        event(
            "source",
            "mind_create",
            0,
            object_id="R3",
            actor_principal_id="P",
        ),
        event("world", "world_create", 0, object_id="main"),
        event(
            "lineage",
            "lineage",
            1,
            source_mind_instance_id="R3",
            destination_mind_instance_id="R4",
            lineage_kind="operational_replica",
        ),
        event(
            "evidence",
            "evidence",
            2,
            object_id="E",
            proposition_id="fact",
            actor_principal_id="P",
            actor_mind_instance_id="R3",
            about_world_branch_id="main",
        ),
        event(
            "observe",
            "exposure",
            2,
            destination_mind_instance_id="R3",
            object_id="E",
            transfer_kind="observe",
        ),
        event(
            "authorization",
            "authorization",
            3,
            object_id="AUTH",
            source_mind_instance_id="R3",
            destination_mind_instance_id="R4",
            policy_operation="grant",
        ),
        event(
            "replicate",
            "exposure",
            6,
            source_mind_instance_id="R3",
            destination_mind_instance_id="R4",
            object_id="E",
            transfer_kind="state_replication",
            authorization_id="AUTH",
        ),
        event(
            "destination",
            "mind_create",
            7,
            object_id="R4",
            actor_principal_id="P",
        ),
    )

    with pytest.raises(ValueError, match=r"lineage.*future entity R4"):
        implementation(events)


@pytest.mark.parametrize("implementation", IMPLEMENTATIONS)
def test_future_created_restore_destination_is_rejected(implementation):
    events = (
        event("principal", "principal_create", 0, object_id="P"),
        event(
            "source",
            "mind_create",
            0,
            object_id="M0",
            actor_principal_id="P",
        ),
        event("world", "world_create", 0, object_id="main"),
        event(
            "evidence",
            "evidence",
            1,
            object_id="E",
            proposition_id="fact",
            actor_principal_id="P",
            actor_mind_instance_id="M0",
            about_world_branch_id="main",
        ),
        event(
            "observe",
            "exposure",
            2,
            destination_mind_instance_id="M0",
            object_id="E",
            transfer_kind="observe",
        ),
        event(
            "snapshot",
            "snapshot_member",
            5,
            snapshot_id="S",
            object_kind="evidence",
            object_id="E",
        ),
        event(
            "restore",
            "lineage",
            6,
            source_mind_instance_id="M0",
            destination_mind_instance_id="M1",
            lineage_kind="restore",
            snapshot_id="S",
            snapshot_cutoff=5,
        ),
        event(
            "destination",
            "mind_create",
            7,
            object_id="M1",
            actor_principal_id="P",
        ),
    )

    with pytest.raises(ValueError, match=r"restore.*future entity M1"):
        implementation(events)


@pytest.mark.parametrize(
    ("events", "field"),
    [
        (
            (
                event("mind", "mind_create", 1, object_id="M", actor_principal_id="P"),
                event("principal", "principal_create", 2, object_id="P"),
            ),
            "actor_principal_id",
        ),
        (
            (
                event(
                    "child",
                    "world_create",
                    1,
                    object_id="child",
                    attributes={"parent": "parent"},
                ),
                event("parent", "world_create", 2, object_id="parent"),
            ),
            "parent",
        ),
        (
            (
                event("world", "world_create", 0, object_id="main"),
                event(
                    "placement",
                    "placement",
                    1,
                    object_id="PL",
                    destination_mind_instance_id="M",
                    about_world_branch_id="main",
                ),
                event("principal", "principal_create", 0, object_id="P"),
                event(
                    "mind",
                    "mind_create",
                    2,
                    object_id="M",
                    actor_principal_id="P",
                ),
            ),
            "destination_mind_instance_id",
        ),
        (
            (
                event("principal", "principal_create", 0, object_id="P"),
                event("world", "world_create", 0, object_id="main"),
                event(
                    "evidence",
                    "evidence",
                    1,
                    object_id="E",
                    actor_principal_id="P",
                    actor_mind_instance_id="M",
                    about_world_branch_id="main",
                ),
                event(
                    "mind",
                    "mind_create",
                    2,
                    object_id="M",
                    actor_principal_id="P",
                ),
            ),
            "actor_mind_instance_id",
        ),
        (
            (
                event("world", "world_create", 2, object_id="main"),
                event(
                    "claim",
                    "world_claim",
                    1,
                    proposition_id="fact",
                    about_world_branch_id="main",
                ),
            ),
            "about_world_branch_id",
        ),
        (
            (
                event("principal", "principal_create", 0, object_id="P"),
                event(
                    "mind",
                    "mind_create",
                    0,
                    object_id="M",
                    actor_principal_id="P",
                ),
                event(
                    "exposure",
                    "exposure",
                    1,
                    destination_mind_instance_id="M",
                    object_id="E",
                    transfer_kind="observe",
                ),
                event("evidence", "evidence", 2, object_id="E"),
            ),
            "object_id",
        ),
        (
            (
                event("principal", "principal_create", 0, object_id="P"),
                event(
                    "source",
                    "mind_create",
                    0,
                    object_id="M0",
                    actor_principal_id="P",
                ),
                event(
                    "destination",
                    "mind_create",
                    0,
                    object_id="M1",
                    actor_principal_id="P",
                ),
                event("evidence", "evidence", 0, object_id="E"),
                event(
                    "exposure",
                    "exposure",
                    1,
                    source_mind_instance_id="M0",
                    destination_mind_instance_id="M1",
                    object_id="E",
                    transfer_kind="state_replication",
                    authorization_id="AUTH",
                ),
                event(
                    "authorization",
                    "authorization",
                    2,
                    object_id="AUTH",
                    source_mind_instance_id="M0",
                    destination_mind_instance_id="M1",
                    policy_operation="grant",
                ),
            ),
            "authorization_id",
        ),
        (
            (
                event(
                    "snapshot",
                    "snapshot_member",
                    1,
                    snapshot_id="S",
                    object_kind="evidence",
                    object_id="E",
                ),
                event("evidence", "evidence", 2, object_id="E"),
            ),
            "object_id",
        ),
        (
            (
                event("principal", "principal_create", 0, object_id="P"),
                event(
                    "source",
                    "mind_create",
                    0,
                    object_id="M0",
                    actor_principal_id="P",
                ),
                event(
                    "authorization",
                    "authorization",
                    1,
                    object_id="AUTH",
                    source_mind_instance_id="M0",
                    destination_mind_instance_id="M1",
                    policy_operation="grant",
                ),
                event(
                    "destination",
                    "mind_create",
                    2,
                    object_id="M1",
                    actor_principal_id="P",
                ),
            ),
            "destination_mind_instance_id",
        ),
    ],
)
def test_temporal_reference_matrix_rejects_future_entities(events, field):
    with pytest.raises(ValueError, match=rf"{field}.*future entity"):
        validate_temporal_references(events)


@pytest.mark.parametrize("implementation", IMPLEMENTATIONS)
def test_same_system_time_reference_is_allowed(implementation):
    events = (
        event("z-principal", "principal_create", 0, object_id="P"),
        event(
            "z-mind",
            "mind_create",
            0,
            object_id="M",
            actor_principal_id="P",
        ),
        event("z-world", "world_create", 0, object_id="main"),
        event(
            "a-evidence",
            "evidence",
            0,
            object_id="E",
            actor_principal_id="P",
            actor_mind_instance_id="M",
            about_world_branch_id="main",
        ),
        event(
            "a-exposure",
            "exposure",
            0,
            destination_mind_instance_id="M",
            object_id="E",
            transfer_kind="observe",
        ),
    )

    implementation(events)
