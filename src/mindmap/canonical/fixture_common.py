from __future__ import annotations

from .model import CommonEvent, ExpectedCase, TargetQuery, TargetSpace, freeze_attrs


def E(event_id: str, event_type: str, system_time: int, **kwargs) -> CommonEvent:
    attrs = kwargs.pop("attrs", None)
    return CommonEvent(
        event_id=event_id,
        event_type=event_type,
        system_time=system_time,
        attributes=freeze_attrs(attrs or {}),
        **kwargs,
    )

def Q(
    query_id: str,
    target: TargetSpace,
    expected,
    invariant: str,
    *,
    system_time: int,
    valid_time: int = 0,
    proposition_id: str | None = None,
    evidence_id: str | None = None,
    world_branch_id: str | None = None,
    mind_instance_id: str | None = None,
    requester_id: str | None = None,
) -> ExpectedCase:
    return ExpectedCase(
        TargetQuery(
            query_id=query_id,
            target_space=target,
            system_time=system_time,
            valid_time=valid_time,
            proposition_id=proposition_id,
            evidence_id=evidence_id,
            world_branch_id=world_branch_id,
            mind_instance_id=mind_instance_id,
            requester_id=requester_id,
        ),
        expected,
        invariant,
    )

def base_identity(prefix: str, *, principals=("P",), minds=(("M", "P"),), branches=(("main", None, None, 0),)) -> list[CommonEvent]:
    events: list[CommonEvent] = []
    for principal in principals:
        events.append(E(f"{prefix}.principal.{principal}", "principal_create", 0, object_id=principal))
    for mind, principal in minds:
        events.append(E(f"{prefix}.mind.{mind}", "mind_create", 0, object_id=mind, actor_principal_id=principal))
    for branch, parent, fork_valid, fork_system in branches:
        events.append(
            E(
                f"{prefix}.world.{branch}",
                "world_create",
                fork_system,
                object_id=branch,
                attrs={"parent": parent or "", "fork_valid_time": fork_valid},
            )
        )
    return events

def placement(prefix: str, placement_id: str, mind: str, branch: str, system_time: int = 0, valid_from: int = 0) -> CommonEvent:
    return E(
        f"{prefix}.placement.{placement_id}",
        "placement",
        system_time,
        object_id=placement_id,
        destination_mind_instance_id=mind,
        about_world_branch_id=branch,
        valid_from=valid_from,
    )
