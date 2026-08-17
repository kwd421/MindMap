from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet, Optional


class EventKind(str, Enum):
    WORLD_UPDATE = "world_update"
    CLAIM = "claim"
    CORRECTION = "correction"
    RETRACTION = "retraction"


class QueryKind(str, Enum):
    WORLD = "world"
    BELIEF = "belief"
    SOURCE = "source"


UNKNOWN = "<unknown>"


@dataclass(frozen=True, slots=True)
class MemoryEvent:
    """Immutable event in the epistemic-temporal branch ledger.

    `audience` means actual possession/acquisition: who observed or received it.
    `read_acl` means governance: which current callers may retrieve it.
    These dimensions are deliberately distinct.
    """

    id: str
    scenario_id: str
    branch: str
    event_time: int
    tx_time: int
    subject: str
    predicate: str
    value: str
    kind: EventKind
    speaker: str
    audience: FrozenSet[str]
    read_acl: FrozenSet[str]
    trust: float
    retracts: Optional[str] = None
    provenance: tuple[str, ...] = field(default_factory=tuple)
    text: str = ""


@dataclass(frozen=True, slots=True)
class MemoryQuery:
    id: str
    scenario_id: str
    branch: str
    valid_at: int
    tx_at: int
    subject: str
    predicate: str
    kind: QueryKind
    caller: str
    viewpoint: Optional[str]
    answer: str
    category: str
    alt_branch_values: FrozenSet[str] = field(default_factory=frozenset)
    stale_values: FrozenSet[str] = field(default_factory=frozenset)
