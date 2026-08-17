from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Optional

from .model import EventKind, MemoryEvent, MemoryQuery, QueryKind, UNKNOWN


@dataclass(frozen=True, slots=True)
class Resolution:
    answer: str
    evidence_id: Optional[str]


class EpistemicBranchStore:
    """Deterministic reference resolver for NCM³-E semantics.

    It isolates branch ancestry, valid/transaction time, actual possession,
    caller authorization, provenance reliability, and explicit retraction.
    """

    def __init__(self, branch_parent: dict[str, Optional[str]] | None = None) -> None:
        self.branch_parent = branch_parent or {"root": None, "main": "root", "alt": "root"}
        self._events: list[MemoryEvent] = []
        self._index: dict[tuple[str, str, str], list[MemoryEvent]] = defaultdict(list)

    def append(self, event: MemoryEvent) -> None:
        if event.branch not in self.branch_parent:
            raise ValueError(f"Unknown branch: {event.branch}")
        if not 0.0 <= event.trust <= 1.0:
            raise ValueError("trust must be in [0, 1]")
        self._events.append(event)
        self._index[(event.scenario_id, event.subject, event.predicate)].append(event)

    def extend(self, events: Iterable[MemoryEvent]) -> None:
        for event in events:
            self.append(event)

    def ancestors(self, branch: str) -> set[str]:
        if branch not in self.branch_parent:
            raise ValueError(f"Unknown branch: {branch}")
        result: set[str] = set()
        current: Optional[str] = branch
        while current is not None:
            result.add(current)
            current = self.branch_parent[current]
        return result

    def _eligible(
        self,
        query: MemoryQuery,
        *,
        use_branch: bool,
        use_time: bool,
        use_viewpoint: bool,
        use_acl: bool,
    ) -> list[MemoryEvent]:
        branches = self.ancestors(query.branch) if use_branch else set(self.branch_parent)
        result: list[MemoryEvent] = []
        for event in self._index.get((query.scenario_id, query.subject, query.predicate), []):
            if event.branch not in branches:
                continue
            if use_time and (event.event_time > query.valid_at or event.tx_time > query.tx_at):
                continue
            if query.kind is not QueryKind.WORLD:
                if use_viewpoint and (
                    query.viewpoint is None or query.viewpoint not in event.audience
                ):
                    continue
                if use_acl and query.caller not in event.read_acl:
                    continue
            result.append(event)
        return result

    @staticmethod
    def _active_claims(
        events: list[MemoryEvent], *, apply_retractions: bool
    ) -> list[MemoryEvent]:
        retracted: set[str] = set()
        if apply_retractions:
            retracted = {
                event.retracts
                for event in events
                if event.kind is EventKind.RETRACTION and event.retracts
            }
        return [
            event
            for event in events
            if event.kind in {
                EventKind.WORLD_UPDATE,
                EventKind.CLAIM,
                EventKind.CORRECTION,
            }
            and event.id not in retracted
        ]

    def resolve(
        self,
        query: MemoryQuery,
        *,
        use_branch: bool = True,
        use_time: bool = True,
        use_viewpoint: bool = True,
        use_acl: bool = True,
        use_trust: bool = True,
        apply_retractions: bool = True,
    ) -> Resolution:
        events = self._eligible(
            query,
            use_branch=use_branch,
            use_time=use_time,
            use_viewpoint=use_viewpoint,
            use_acl=use_acl,
        )

        if query.kind is QueryKind.WORLD:
            candidates = [e for e in events if e.kind is EventKind.WORLD_UPDATE]
            if not candidates:
                return Resolution(UNKNOWN, None)
            selected = max(candidates, key=lambda e: (e.event_time, e.tx_time, e.id))
            return Resolution(selected.value, selected.id)

        candidates = self._active_claims(events, apply_retractions=apply_retractions)
        if not candidates:
            return Resolution(UNKNOWN, None)

        if use_trust:
            selected = max(
                candidates,
                key=lambda e: (e.trust, e.event_time, e.tx_time, e.id),
            )
        else:
            selected = max(
                candidates,
                key=lambda e: (e.event_time, e.tx_time, e.id),
            )

        if query.kind is QueryKind.SOURCE:
            return Resolution(selected.speaker, selected.id)
        return Resolution(selected.value, selected.id)


SYSTEM_CONFIGS: dict[str, dict[str, bool]] = {
    "FlatGlobal": {
        "use_branch": False,
        "use_time": False,
        "use_viewpoint": False,
        "use_acl": False,
        "use_trust": False,
        "apply_retractions": False,
    },
    "BitemporalACL": {
        "use_branch": True,
        "use_time": True,
        "use_viewpoint": False,
        "use_acl": True,
        "use_trust": False,
        "apply_retractions": False,
    },
    "BitemporalPerspective": {
        "use_branch": True,
        "use_time": True,
        "use_viewpoint": True,
        "use_acl": False,
        "use_trust": False,
        "apply_retractions": False,
    },
    "EpistemicTemporalLatest": {
        "use_branch": True,
        "use_time": True,
        "use_viewpoint": True,
        "use_acl": True,
        "use_trust": False,
        "apply_retractions": False,
    },
    "NCM3E": {
        "use_branch": True,
        "use_time": True,
        "use_viewpoint": True,
        "use_acl": True,
        "use_trust": True,
        "apply_retractions": True,
    },
}
