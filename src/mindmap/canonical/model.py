from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Optional


class TargetSpace(str, Enum):
    WORLD = "WORLD"
    EVER_EXPOSED = "EVER_EXPOSED"
    AVAILABLE = "AVAILABLE"
    ATTITUDE = "ATTITUDE"
    ATTRIBUTION = "ATTRIBUTION"
    DISCLOSE = "DISCLOSE"
    JUSTIFICATION = "JUSTIFICATION"


class Attribution(str, Enum):
    DIRECT_OBSERVATION = "direct_observation"
    SAME_PRINCIPAL_SNAPSHOT_INHERITANCE = "same_principal_snapshot_inheritance"
    SAME_PRINCIPAL_STATE_REPLICATION = "same_principal_state_replication"
    ATTRIBUTED_REPORT = "attributed_report"
    EVIDENCE_COPY = "evidence_copy"
    RECONSTRUCTION = "reconstruction"
    UNKNOWN = "unknown"


class Attitude(str, Enum):
    BELIEVE = "believe"
    DISBELIEVE = "disbelieve"
    SUSPECT = "suspect"
    SUSPEND = "suspend"
    UNKNOWN = "unknown"


Answer = bool | str | tuple[str, ...]


def freeze_attrs(values: Optional[Mapping[str, Any]] = None, /, **kwargs: Any) -> tuple[tuple[str, str], ...]:
    merged: dict[str, Any] = {}
    if values:
        merged.update(values)
    merged.update(kwargs)
    return tuple(sorted((str(key), str(value)) for key, value in merged.items()))


def attrs_dict(event: "CommonEvent") -> dict[str, str]:
    return dict(event.attributes)


def attr_bool(event: "CommonEvent", key: str, default: bool = False) -> bool:
    value = attrs_dict(event).get(key)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on", "active", "allow", "allowed"}


def attr_int(event: "CommonEvent", key: str, default: Optional[int] = None) -> Optional[int]:
    value = attrs_dict(event).get(key)
    if value is None or value == "None":
        return default
    return int(value)


@dataclass(frozen=True, slots=True)
class CommonEvent:
    """One append-only input event shared byte-for-byte by G and T.

    The schema intentionally uses one sparse record for the S-track input
    contract. Typed T normalizes it into domain relations; generic G retains it
    as an event relation. No answer-defining final state is present.
    """

    event_id: str
    event_type: str
    system_time: int
    valid_from: int = 0
    valid_to: Optional[int] = None
    actor_principal_id: Optional[str] = None
    actor_mind_instance_id: Optional[str] = None
    source_mind_instance_id: Optional[str] = None
    destination_mind_instance_id: Optional[str] = None
    source_placement_id: Optional[str] = None
    destination_placement_id: Optional[str] = None
    object_kind: Optional[str] = None
    object_id: Optional[str] = None
    proposition_id: Optional[str] = None
    about_world_branch_id: Optional[str] = None
    lineage_kind: Optional[str] = None
    snapshot_id: Optional[str] = None
    snapshot_cutoff: Optional[int] = None
    transfer_kind: Optional[str] = None
    attitude_transition: Optional[str] = None
    attribution_kind: Optional[str] = None
    authorization_id: Optional[str] = None
    policy_operation: Optional[str] = None
    policy_label: Optional[str] = None
    source_family_id: Optional[str] = None
    derivation_members: tuple[str, ...] = ()
    raw_evidence_ref: Optional[str] = None
    attributes: tuple[tuple[str, str], ...] = ()

    def active_at(self, valid_time: int) -> bool:
        return self.valid_from <= valid_time and (self.valid_to is None or valid_time < self.valid_to)

    def attr(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return dict(self.attributes).get(key, default)


@dataclass(frozen=True, slots=True)
class TargetQuery:
    query_id: str
    target_space: TargetSpace
    system_time: int
    valid_time: int = 0
    proposition_id: Optional[str] = None
    evidence_id: Optional[str] = None
    world_branch_id: Optional[str] = None
    mind_instance_id: Optional[str] = None
    requester_id: Optional[str] = None


@dataclass(frozen=True, slots=True)
class ExpectedCase:
    query: TargetQuery
    expected: Answer
    invariant: str


@dataclass(frozen=True, slots=True)
class Fixture:
    fixture_id: str
    family: str
    events: tuple[CommonEvent, ...]
    cases: tuple[ExpectedCase, ...]
    notes: str = ""
    tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EvaluationRow:
    fixture_id: str
    family: str
    query_id: str
    target_space: str
    invariant: str
    expected: Answer
    gold: Answer
    generic: Answer
    typed: Answer

    @property
    def gold_correct(self) -> bool:
        return self.gold == self.expected

    @property
    def generic_correct(self) -> bool:
        return self.generic == self.expected

    @property
    def typed_correct(self) -> bool:
        return self.typed == self.expected

    @property
    def all_agree(self) -> bool:
        return self.gold == self.generic == self.typed == self.expected


def sorted_events(events: Iterable[CommonEvent], *, through_system_time: Optional[int] = None) -> tuple[CommonEvent, ...]:
    selected = [event for event in events if through_system_time is None or event.system_time <= through_system_time]
    return tuple(sorted(selected, key=lambda event: (event.system_time, event.event_id)))


def validate_temporal_references(events: Iterable[CommonEvent]) -> None:
    """Reject references to entities that do not yet exist at event time.

    System time is the append-only observation axis. A reference is valid when
    its target was created at or before the referencing event's system time;
    a target that appears only in a later event must not retroactively make an
    earlier lineage, exposure, placement, or claim valid.
    """

    ordered = sorted_events(events)

    def creation_times(
        event_type: str, *, use_event_id: bool = False
    ) -> dict[str, int]:
        result: dict[str, int] = {}
        for event in ordered:
            if event.event_type != event_type:
                continue
            object_id = event.event_id if use_event_id else event.object_id
            if object_id is not None:
                result[object_id] = min(
                    result.get(object_id, event.system_time), event.system_time
                )
        return result

    principals = creation_times("principal_create")
    minds = creation_times("mind_create")
    branches = creation_times("world_create")
    placements = creation_times("placement")
    evidence = creation_times("evidence")
    assertions = creation_times("assertion")
    claims = creation_times("world_claim", use_event_id=True)
    attitudes = creation_times("attitude", use_event_id=True)
    policies = creation_times("policy", use_event_id=True)
    authorizations = creation_times("authorization")

    # The finite CommonEvent runtime does not yet project the standalone
    # Snapshot entity from SCHEMA_V0_2.md. Until it does, the first manifest
    # entry is the explicit runtime creation point for a snapshot identifier.
    snapshots: dict[str, int] = {}
    for event in ordered:
        if event.event_type != "snapshot_member" or event.snapshot_id is None:
            continue
        snapshots[event.snapshot_id] = min(
            snapshots.get(event.snapshot_id, event.system_time), event.system_time
        )

    def require(
        event: CommonEvent,
        field: str,
        target_id: Optional[str],
        targets: dict[str, int],
    ) -> None:
        if target_id is None:
            return
        created_at = targets.get(target_id)
        if created_at is None:
            raise ValueError(
                f"{event.event_id}.{field} references missing entity: {target_id}"
            )
        if created_at > event.system_time:
            raise ValueError(
                f"{event.event_id}.{field} references future entity {target_id}: "
                f"created at {created_at}, referenced at {event.system_time}"
            )

    def require_typed_object(
        event: CommonEvent,
        field: str,
        target_id: Optional[str],
        object_kind: Optional[str],
        *,
        default_kind: Optional[str],
        allowed_kinds: frozenset[str],
    ) -> None:
        if target_id is None:
            return
        kind = object_kind or default_kind
        if kind is None or kind not in allowed_kinds:
            raise ValueError(
                f"{event.event_id}.{field} has unsupported object_kind: {kind}"
            )
        targets_by_kind = {
            "evidence": evidence,
            "assertion": assertions,
            "claim": claims,
            "snapshot": snapshots,
            "attitude": attitudes,
            "policy": policies,
        }
        require(event, field, target_id, targets_by_kind[kind])

    def require_derivation_member(event: CommonEvent, member_id: str) -> None:
        matches = [
            targets[member_id]
            for targets in (evidence, assertions, claims)
            if member_id in targets
        ]
        if not matches:
            raise ValueError(
                f"{event.event_id}.derivation_members references missing entity: "
                f"{member_id}"
            )
        if len(matches) > 1:
            raise ValueError(
                f"{event.event_id}.derivation_members has ambiguous untyped entity: "
                f"{member_id}"
            )
        if matches[0] > event.system_time:
            raise ValueError(
                f"{event.event_id}.derivation_members references future entity "
                f"{member_id}: created at {matches[0]}, "
                f"referenced at {event.system_time}"
            )

    for event in ordered:
        attrs = attrs_dict(event)
        if event.event_type == "mind_create":
            require(event, "actor_principal_id", event.actor_principal_id, principals)
        elif event.event_type == "world_create":
            require(event, "parent", attrs.get("parent") or None, branches)
        elif event.event_type == "placement":
            require(
                event,
                "destination_mind_instance_id",
                event.destination_mind_instance_id,
                minds,
            )
            require(
                event,
                "about_world_branch_id",
                event.about_world_branch_id,
                branches,
            )
        elif event.event_type == "lineage":
            require(
                event,
                "source_mind_instance_id",
                event.source_mind_instance_id,
                minds,
            )
            require(
                event,
                "destination_mind_instance_id",
                event.destination_mind_instance_id,
                minds,
            )
            require(event, "snapshot_id", event.snapshot_id, snapshots)
            require(
                event,
                "authorization_id",
                event.authorization_id,
                authorizations,
            )
        elif event.event_type == "evidence":
            require(event, "actor_principal_id", event.actor_principal_id, principals)
            require(
                event,
                "actor_mind_instance_id",
                event.actor_mind_instance_id,
                minds,
            )
            require(
                event,
                "source_placement_id",
                event.source_placement_id,
                placements,
            )
            require(
                event,
                "destination_placement_id",
                event.destination_placement_id,
                placements,
            )
            require(
                event,
                "about_world_branch_id",
                event.about_world_branch_id,
                branches,
            )
        elif event.event_type == "world_claim":
            require(
                event,
                "about_world_branch_id",
                event.about_world_branch_id,
                branches,
            )
            require(
                event,
                "destination_placement_id",
                event.destination_placement_id,
                placements,
            )
        elif event.event_type == "attitude":
            require(
                event,
                "destination_mind_instance_id",
                event.destination_mind_instance_id,
                minds,
            )
            require(
                event,
                "about_world_branch_id",
                event.about_world_branch_id,
                branches,
            )
            require(
                event,
                "destination_placement_id",
                event.destination_placement_id,
                placements,
            )
        elif event.event_type == "exposure":
            require(
                event,
                "source_mind_instance_id",
                event.source_mind_instance_id,
                minds,
            )
            require(
                event,
                "destination_mind_instance_id",
                event.destination_mind_instance_id,
                minds,
            )
            require(
                event,
                "source_placement_id",
                event.source_placement_id,
                placements,
            )
            require(
                event,
                "destination_placement_id",
                event.destination_placement_id,
                placements,
            )
            require_typed_object(
                event,
                "object_id",
                event.object_id,
                event.object_kind,
                default_kind="evidence",
                allowed_kinds=frozenset(
                    {"evidence", "assertion", "claim", "snapshot"}
                ),
            )
            require(
                event,
                "authorization_id",
                event.authorization_id,
                authorizations,
            )
        elif event.event_type == "snapshot_member":
            require(event, "snapshot_id", event.snapshot_id, snapshots)
            require_typed_object(
                event,
                "object_id",
                event.object_id,
                event.object_kind,
                default_kind=None,
                allowed_kinds=frozenset(
                    {"evidence", "assertion", "claim", "attitude", "policy"}
                ),
            )
        elif event.event_type == "authorization":
            require(event, "actor_principal_id", event.actor_principal_id, principals)
            require(
                event,
                "source_mind_instance_id",
                event.source_mind_instance_id,
                minds,
            )
            require(
                event,
                "destination_mind_instance_id",
                event.destination_mind_instance_id,
                minds,
            )
        elif event.event_type == "policy":
            require(event, "actor_principal_id", event.actor_principal_id, principals)
            require(
                event,
                "destination_mind_instance_id",
                event.destination_mind_instance_id,
                minds,
            )
            require_typed_object(
                event,
                "object_id",
                event.object_id,
                event.object_kind,
                default_kind="evidence",
                allowed_kinds=frozenset(
                    {"evidence", "assertion", "claim", "snapshot", "attitude"}
                ),
            )
        elif event.event_type == "justification":
            for member_id in event.derivation_members:
                require_derivation_member(event, member_id)


def normalize_answer(value: Answer) -> Answer:
    if isinstance(value, tuple):
        return tuple(sorted(value))
    return value
