from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Iterable


class EventType(StrEnum):
    MIND_CREATED = "mind_created"
    PLACEMENT = "placement"
    WORLD_FACT = "world_fact"
    EVIDENCE = "evidence"
    EXPOSURE = "exposure"
    ATTITUDE = "attitude"
    LINEAGE = "lineage"
    SNAPSHOT = "snapshot"
    POLICY = "policy"
    JUSTIFICATION = "justification"


class QueryTarget(StrEnum):
    WORLD = "world"
    EVER_EXPOSED = "ever_exposed"
    AVAILABLE = "available"
    ATTITUDE = "attitude"
    ATTRIBUTION = "attribution"
    DISCLOSE = "disclose"
    JUSTIFICATION = "justification"


ACQUISITION_OPERATIONS = frozenset(
    {
        "observe",
        "receive",
        "read",
        "evidence_copy",
        "state_replication",
        "restore",
        "reacquire",
    }
)

ATTRIBUTION_PRECEDENCE = {
    "unknown": 0,
    "reconstruction": 1,
    "attributed_report": 2,
    "evidence_copy": 3,
    "same_principal_snapshot_inheritance": 4,
    "same_principal_state_replication": 5,
    "direct_observation": 6,
}


@dataclass(frozen=True, slots=True)
class CommonEvent:
    event_id: str
    event_type: EventType
    system_time: int
    valid_from: int = 0
    valid_to: int | None = None

    actor_principal_id: str | None = None
    actor_mind_instance_id: str | None = None
    source_mind_instance_id: str | None = None
    destination_mind_instance_id: str | None = None

    placement_id: str | None = None
    world_branch_id: str | None = None
    about_world_branch_id: str | None = None

    object_kind: str | None = None
    object_id: str | None = None
    proposition_id: str | None = None

    operation: str | None = None
    lineage_kind: str | None = None
    snapshot_id: str | None = None
    snapshot_cutoff: int | None = None
    authorization_id: str | None = None
    authorized: bool | None = None

    stance: str | None = None
    attribution_kind: str | None = None
    truth_value: bool | None = None

    policy_label: str | None = None
    requester_id: str | None = None
    source_family_id: str | None = None

    support_set_id: str | None = None
    support_member_ids: tuple[str, ...] = field(default_factory=tuple)
    required_independent_sources: int = 1

    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def visible_at(self, system_time: int) -> bool:
        return self.system_time <= system_time

    def valid_at(self, valid_time: int) -> bool:
        return self.valid_from <= valid_time and (
            self.valid_to is None or valid_time < self.valid_to
        )


@dataclass(frozen=True, slots=True)
class Query:
    query_id: str
    target: QueryTarget
    system_time: int
    valid_time: int = 0
    proposition_id: str | None = None
    evidence_id: str | None = None
    world_branch_id: str | None = None
    mind_instance_id: str | None = None
    requester_id: str | None = None


@dataclass(frozen=True, slots=True)
class Answer:
    target: QueryTarget
    value: bool | str | tuple[str, ...] | None


@dataclass(frozen=True, slots=True)
class Fixture:
    fixture_id: str
    events: tuple[CommonEvent, ...]
    queries: tuple[Query, ...]

    @classmethod
    def from_iterables(
        cls,
        fixture_id: str,
        events: Iterable[CommonEvent],
        queries: Iterable[Query],
    ) -> "Fixture":
        return cls(fixture_id, tuple(events), tuple(queries))


def validate_event_log(events: Iterable[CommonEvent]) -> tuple[CommonEvent, ...]:
    materialized = tuple(events)
    ids: set[str] = set()
    minds: set[str] = set()
    snapshots: set[str] = set()

    for event in sorted(materialized, key=lambda item: (item.system_time, item.event_id)):
        if event.event_id in ids:
            raise ValueError(f"duplicate event_id: {event.event_id}")
        ids.add(event.event_id)

        if event.valid_to is not None and event.valid_to <= event.valid_from:
            raise ValueError(f"invalid valid interval: {event.event_id}")

        match event.event_type:
            case EventType.MIND_CREATED:
                if not event.destination_mind_instance_id or not event.actor_principal_id:
                    raise ValueError(f"mind_created missing identity fields: {event.event_id}")
                minds.add(event.destination_mind_instance_id)
            case EventType.PLACEMENT:
                if not event.destination_mind_instance_id or not event.world_branch_id:
                    raise ValueError(f"placement missing fields: {event.event_id}")
                if event.destination_mind_instance_id not in minds:
                    raise ValueError(f"placement references unknown mind: {event.event_id}")
            case EventType.SNAPSHOT:
                if not event.snapshot_id or not event.source_mind_instance_id:
                    raise ValueError(f"snapshot missing fields: {event.event_id}")
                if event.source_mind_instance_id not in minds:
                    raise ValueError(f"snapshot references unknown mind: {event.event_id}")
                snapshots.add(event.snapshot_id)
            case EventType.LINEAGE:
                if not event.source_mind_instance_id or not event.destination_mind_instance_id:
                    raise ValueError(f"lineage missing minds: {event.event_id}")
                if event.source_mind_instance_id not in minds:
                    raise ValueError(f"lineage source unknown: {event.event_id}")
                if event.destination_mind_instance_id not in minds:
                    raise ValueError(f"lineage destination unknown: {event.event_id}")
                if event.snapshot_id and event.snapshot_id not in snapshots:
                    raise ValueError(f"lineage snapshot unknown: {event.event_id}")
            case EventType.WORLD_FACT:
                if not event.proposition_id or not event.world_branch_id:
                    raise ValueError(f"world_fact missing fields: {event.event_id}")
                if event.truth_value is None:
                    raise ValueError(f"world_fact missing truth value: {event.event_id}")
            case EventType.EVIDENCE:
                if not event.object_id or not event.proposition_id:
                    raise ValueError(f"evidence missing fields: {event.event_id}")
            case EventType.EXPOSURE:
                if not event.destination_mind_instance_id or not event.object_id:
                    raise ValueError(f"exposure missing fields: {event.event_id}")
                if event.destination_mind_instance_id not in minds:
                    raise ValueError(f"exposure destination unknown: {event.event_id}")
                if not event.operation:
                    raise ValueError(f"exposure missing operation: {event.event_id}")
            case EventType.ATTITUDE:
                if not event.destination_mind_instance_id or not event.proposition_id:
                    raise ValueError(f"attitude missing fields: {event.event_id}")
                if not event.stance or not event.about_world_branch_id:
                    raise ValueError(f"attitude missing stance/scope: {event.event_id}")
            case EventType.POLICY:
                if not event.object_id or not event.operation:
                    raise ValueError(f"policy missing fields: {event.event_id}")
            case EventType.JUSTIFICATION:
                if not event.proposition_id or not event.support_set_id:
                    raise ValueError(f"justification missing fields: {event.event_id}")
                if not event.support_member_ids:
                    raise ValueError(f"justification has no members: {event.event_id}")
                if event.required_independent_sources < 1:
                    raise ValueError(f"invalid independent-source threshold: {event.event_id}")

    return materialized


def policy_allows(label: str | None, requester_id: str | None) -> bool:
    if label is None or label in {"revoked", "deleted", "quarantined"}:
        return False
    if label == "public":
        return True
    if requester_id is None:
        return False
    if label.startswith("private:"):
        return requester_id == label.removeprefix("private:")
    if label.startswith("shared:"):
        members = {value.strip() for value in label.removeprefix("shared:").split(",")}
        return requester_id in members
    return False
