from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import statistics
import time
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence


UNKNOWN = "unknown"
ABSTAIN = "abstain:fault"

CLEARANCE = {"public_user": 0, "trusted_user": 1, "admin": 2}
POLICY_RANK = {"public": 0, "private": 1, "sealed": 2, "deleted": 99}
ACQUIRE_OPS = {
    "observe",
    "receive",
    "read",
    "evidence_copy",
    "state_replication",
    "restore",
    "reacquire",
}


@dataclass(frozen=True)
class CommonEvent:
    event_id: str
    event_type: str
    valid_time: int
    system_time: int
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Query:
    query_id: str
    target: str
    expected: str
    valid_time: int
    system_time: int
    branch: str = "root"
    instance: Optional[str] = None
    requester: str = "public_user"
    proposition: Optional[str] = None
    object_id: Optional[str] = None
    claim_id: Optional[str] = None
    source_instance: Optional[str] = None
    destination_instance: Optional[str] = None
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    archetype: str
    events: tuple[CommonEvent, ...]
    queries: tuple[Query, ...]


@dataclass(frozen=True)
class Fault:
    fault_id: str
    fault_class: str  # enforceable | well_formed_semantic | missing_event
    fixture_id: str
    target_event_id: Optional[str]
    description: str
    mutated_events: tuple[CommonEvent, ...]


@dataclass(frozen=True)
class Finding:
    code: str
    event_ids: tuple[str, ...]
    message: str
    stage: str


@dataclass
class RunCounters:
    local_checks: int = 0
    cross_checks: int = 0
    scanned_events: int = 0


# ---------------------------------------------------------------------------
# Fixture construction
# ---------------------------------------------------------------------------


class Builder:
    def __init__(self, fixture_id: str, archetype: str):
        self.fixture_id = fixture_id
        self.archetype = archetype
        self.events: list[CommonEvent] = []
        self.queries: list[Query] = []
        self._event_n = 0
        self._query_n = 0

    def e(self, event_type: str, tv: int, ts: int, **payload: Any) -> str:
        self._event_n += 1
        eid = f"{self.fixture_id}-e{self._event_n:02d}"
        self.events.append(CommonEvent(eid, event_type, tv, ts, payload))
        return eid

    def q(
        self,
        target: str,
        expected: str,
        tv: int,
        ts: int,
        *,
        branch: str = "root",
        instance: Optional[str] = None,
        requester: str = "public_user",
        proposition: Optional[str] = None,
        object_id: Optional[str] = None,
        claim_id: Optional[str] = None,
        source_instance: Optional[str] = None,
        destination_instance: Optional[str] = None,
        depends_on: Iterable[str] = (),
    ) -> None:
        self._query_n += 1
        self.queries.append(
            Query(
                query_id=f"{self.fixture_id}-q{self._query_n:02d}",
                target=target,
                expected=expected,
                valid_time=tv,
                system_time=ts,
                branch=branch,
                instance=instance,
                requester=requester,
                proposition=proposition,
                object_id=object_id,
                claim_id=claim_id,
                source_instance=source_instance,
                destination_instance=destination_instance,
                depends_on=tuple(depends_on),
            )
        )

    def build(self) -> Fixture:
        return Fixture(self.fixture_id, self.archetype, tuple(self.events), tuple(self.queries))

