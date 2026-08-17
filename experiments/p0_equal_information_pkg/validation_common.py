from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

from .model import *


REQUIRED_FIELDS: dict[str, set[str]] = {
    "branch_create": {"branch", "parent", "fork_valid", "fork_system"},
    "principal_create": {"principal"},
    "mind_create": {"instance", "principal"},
    "placement": {"instance", "branch", "operation"},
    "lineage": {"source_instance", "destination_instance", "kind", "cutoff_system", "authorization"},
    "evidence": {"object_id", "actor_instance", "branch", "source_family", "policy"},
    "world_claim": {"proposition", "value", "about_branch", "valid_from", "valid_to", "status", "source_object"},
    "exposure": {"destination_instance", "source_instance", "object_id", "operation", "attribution", "authorization", "branch"},
    "attitude": {"instance", "proposition", "about_branch", "stance", "value", "source_object"},
    "policy": {"object_id", "operation", "new_policy", "authorization"},
    "justification": {"claim_id", "proposition", "members", "min_independent"},
    "snapshot": {"snapshot_id", "source_instance", "cutoff_system", "members"},
}


@dataclass(frozen=True)
class TypedEvent:
    event_id: str
    event_type: str
    valid_time: int
    system_time: int
    payload: dict[str, Any]


class ValidationResult:
    def __init__(self, findings: Iterable[Finding] = (), counters: Optional[RunCounters] = None):
        self.findings = list(findings)
        self.counters = counters or RunCounters()

    @property
    def localized_ids(self) -> set[str]:
        return {eid for f in self.findings for eid in f.event_ids}


# Independent generic-audit implementation. It deliberately does not call the
# typed parser or typed cross-checker.

def _dedupe_findings(findings: Iterable[Finding]) -> list[Finding]:
    seen: set[tuple[str, tuple[str, ...]]] = set()
    out: list[Finding] = []
    for f in findings:
        key = (f.code, tuple(sorted(set(f.event_ids))))
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


# ---------------------------------------------------------------------------
# Independent query resolvers
# ---------------------------------------------------------------------------

