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


def normalize_answer(value: Answer) -> Answer:
    if isinstance(value, tuple):
        return tuple(sorted(value))
    return value
