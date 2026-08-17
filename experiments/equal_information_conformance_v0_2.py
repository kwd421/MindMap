from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable
import hashlib
import json
import platform
from pathlib import Path

SUITE_VERSION = "equal-information-conformance-v0.2.0"


# This script is intentionally standard-library only.
# Gold target vectors are literal fixture data. Candidate resolvers never call a gold helper.


@dataclass(frozen=True)
class WorldBranch:
    branch_id: str
    parent_branch_id: str | None
    fork_valid_time: int | None


@dataclass(frozen=True)
class MindInstance:
    instance_id: str
    principal_id: str


@dataclass(frozen=True)
class LineageEdge:
    kind: str
    source_instance_id: str
    destination_instance_id: str
    authorized: bool
    system_time: int
    snapshot_id: str | None = None


@dataclass(frozen=True)
class EvidenceEvent:
    evidence_id: str
    proposition: str
    truth_value: bool
    about_branch_id: str
    valid_time: int
    system_time: int
    witnesses: tuple[str, ...] = ()
    policy: str = "public"
    allowed_requesters: tuple[str, ...] = ()
    origin_family_id: str | None = None


@dataclass(frozen=True)
class TransferEvent:
    evidence_id: str
    source_instance_id: str
    destination_instance_id: str
    kind: str
    received_valid_time: int
    system_time: int
    authorized: bool
    source_branch_id: str
    destination_branch_id: str


@dataclass(frozen=True)
class AdoptionEvent:
    evidence_id: str
    destination_instance_id: str
    stance: str
    valid_time: int
    system_time: int
    attitude_context_branch_id: str


@dataclass(frozen=True)
class ExposureEvent:
    evidence_id: str
    destination_instance_id: str
    operation: str
    valid_time: int
    system_time: int


@dataclass(frozen=True)
class PolicyEvent:
    evidence_id: str
    operation: str
    valid_time: int
    system_time: int
    requester: str | None = None


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    source_instance_id: str
    cutoff_system_time: int
    entries: tuple[str, ...]


@dataclass(frozen=True)
class RestoreEvent:
    snapshot_id: str
    destination_instance_id: str
    valid_time: int
    system_time: int


@dataclass(frozen=True)
class Justification:
    justification_id: str
    claim_id: str
    source_evidence_ids: tuple[str, ...]


@dataclass
class TypedLedger:
    branches: dict[str, WorldBranch] = field(default_factory=dict)
    instances: dict[str, MindInstance] = field(default_factory=dict)
    lineage: list[LineageEdge] = field(default_factory=list)
    evidence: dict[str, EvidenceEvent] = field(default_factory=dict)
    transfers: list[TransferEvent] = field(default_factory=list)
    adoptions: list[AdoptionEvent] = field(default_factory=list)
    exposures: list[ExposureEvent] = field(default_factory=list)
    policies: list[PolicyEvent] = field(default_factory=list)
    snapshots: dict[str, Snapshot] = field(default_factory=dict)
    restores: list[RestoreEvent] = field(default_factory=list)
    justifications: list[Justification] = field(default_factory=list)


@dataclass(frozen=True)
class Query:
    query_id: str
    target: str
    valid_time: int
    system_time: int
    proposition: str | None = None
    branch_id: str | None = None
    instance_id: str | None = None
    evidence_id: str | None = None
    claim_id: str | None = None
    requester: str | None = None


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    events: tuple[dict[str, Any], ...]
    queries: tuple[Query, ...]
    expected: dict[str, Any]


def compile_typed(events: Iterable[dict[str, Any]]) -> TypedLedger:
    ledger = TypedLedger()
    for row in events:
        kind = row["type"]
        if kind == "branch":
            obj = WorldBranch(row["id"], row.get("parent"), row.get("fork_valid"))
            ledger.branches[obj.branch_id] = obj
        elif kind == "instance":
            obj = MindInstance(row["id"], row["principal"])
            ledger.instances[obj.instance_id] = obj
        elif kind == "lineage":
            ledger.lineage.append(LineageEdge(
                row["kind"], row["source"], row["destination"], row.get("authorized", False),
                row["system_time"], row.get("snapshot_id")
            ))
        elif kind == "evidence":
            obj = EvidenceEvent(
                evidence_id=row["id"],
                proposition=row["proposition"],
                truth_value=row["truth"],
                about_branch_id=row["about_branch"],
                valid_time=row["valid_time"],
                system_time=row["system_time"],
                witnesses=tuple(row.get("witnesses", ())),
                policy=row.get("policy", "public"),
                allowed_requesters=tuple(row.get("allowed_requesters", ())),
                origin_family_id=row.get("origin_family", row["id"]),
            )
            ledger.evidence[obj.evidence_id] = obj
        elif kind == "transfer":
            ledger.transfers.append(TransferEvent(
                row["evidence"], row["source"], row["destination"], row["kind"],
                row["valid_time"], row["system_time"], row.get("authorized", False),
                row["source_branch"], row["destination_branch"],
            ))
        elif kind == "adoption":
            ledger.adoptions.append(AdoptionEvent(
                row["evidence"], row["destination"], row["stance"],
                row["valid_time"], row["system_time"], row["context_branch"],
            ))
        elif kind == "exposure":
            ledger.exposures.append(ExposureEvent(
                row["evidence"], row["destination"], row["operation"],
                row["valid_time"], row["system_time"],
            ))
        elif kind == "policy":
            ledger.policies.append(PolicyEvent(
                row["evidence"], row["operation"], row["valid_time"],
                row["system_time"], row.get("requester"),
            ))
        elif kind == "snapshot":
            obj = Snapshot(row["id"], row["source"], row["cutoff_system"], tuple(row["entries"]))
            ledger.snapshots[obj.snapshot_id] = obj
        elif kind == "restore":
            ledger.restores.append(RestoreEvent(
                row["snapshot"], row["destination"], row["valid_time"], row["system_time"],
            ))
        elif kind == "justification":
            ledger.justifications.append(Justification(
                row["id"], row["claim"], tuple(row["sources"])
            ))
        else:
            raise ValueError(f"unknown event type: {kind}")
    return ledger


def compile_generic(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i, row in enumerate(events):
        payload = dict(row)
        payload.setdefault("_row_id", f"g{i:04d}")
        rows.append(payload)
    return rows


class TypedResolver:
    def __init__(self, ledger: TypedLedger):
        self.l = ledger

    def resolve(self, q: Query) -> Any:
        dispatch = {
            "WORLD": self._world,
            "EVER_EXPOSED": self._ever_exposed,
            "AVAILABLE": self._available,
            "ATTITUDE": self._attitude,
            "MEMORY_ATTRIBUTION": self._attribution,
            "DISCLOSE": self._disclose,
            "JUSTIFICATION": self._justification,
        }
        return dispatch[q.target](q)

    def _branch_visible(self, evidence_branch: str, query_branch: str, evidence_valid: int) -> bool:
        current = query_branch
        while True:
            if current == evidence_branch:
                return True
            branch = self.l.branches.get(current)
            if branch is None or branch.parent_branch_id is None:
                return False
            if branch.fork_valid_time is not None and evidence_valid > branch.fork_valid_time:
                return False
            current = branch.parent_branch_id

    def _visible_evidence(self, q: Query) -> list[EvidenceEvent]:
        assert q.branch_id is not None and q.proposition is not None
        out = []
        for ev in self.l.evidence.values():
            if ev.proposition != q.proposition:
                continue
            if ev.valid_time > q.valid_time or ev.system_time > q.system_time:
                continue
            if self._branch_visible(ev.about_branch_id, q.branch_id, ev.valid_time):
                out.append(ev)
        return out

    def _world(self, q: Query) -> Any:
        candidates = self._visible_evidence(q)
        if not candidates:
            return None
        candidates.sort(key=lambda e: (e.valid_time, e.system_time, e.evidence_id))
        return candidates[-1].truth_value

    def _acquisitions(self, instance: str, evidence: str, q: Query) -> list[tuple[int, int, str, str | None]]:
        out: list[tuple[int, int, str, str | None]] = []
        ev = self.l.evidence[evidence]
        if instance in ev.witnesses and ev.valid_time <= q.valid_time and ev.system_time <= q.system_time:
            out.append((ev.valid_time, ev.system_time, "observe", None))
        for tr in self.l.transfers:
            if tr.destination_instance_id == instance and tr.evidence_id == evidence:
                if tr.received_valid_time <= q.valid_time and tr.system_time <= q.system_time:
                    out.append((tr.received_valid_time, tr.system_time, tr.kind, tr.source_instance_id))
        for ex in self.l.exposures:
            if ex.destination_instance_id == instance and ex.evidence_id == evidence:
                if ex.valid_time <= q.valid_time and ex.system_time <= q.system_time:
                    out.append((ex.valid_time, ex.system_time, ex.operation, None))
        for restore in self.l.restores:
            if restore.destination_instance_id != instance:
                continue
            if restore.valid_time > q.valid_time or restore.system_time > q.system_time:
                continue
            snap = self.l.snapshots[restore.snapshot_id]
            if evidence in snap.entries:
                src_ev = self.l.evidence[evidence]
                if src_ev.system_time <= snap.cutoff_system_time:
                    out.append((restore.valid_time, restore.system_time, "restore", snap.source_instance_id))
        return sorted(out)

    def _ever_exposed(self, q: Query) -> bool:
        assert q.instance_id and q.evidence_id
        return bool(self._acquisitions(q.instance_id, q.evidence_id, q))

    def _available(self, q: Query) -> bool:
        assert q.instance_id and q.evidence_id
        if not self._acquisitions(q.instance_id, q.evidence_id, q):
            return False
        state = True
        transitions = []
        for ex in self.l.exposures:
            if ex.destination_instance_id == q.instance_id and ex.evidence_id == q.evidence_id:
                if ex.valid_time <= q.valid_time and ex.system_time <= q.system_time:
                    transitions.append((ex.valid_time, ex.system_time, ex.operation))
        for _, _, op in sorted(transitions):
            if op in {"self_seal", "forget"}:
                state = False
            elif op in {"self_unseal", "reacquire", "read", "observe", "receive", "copy", "restore"}:
                state = True
        if not self._policy_allows(q.evidence_id, q.instance_id, q.valid_time, q.system_time, self_access=True):
            state = False
        return state

    def _attitude(self, q: Query) -> str:
        assert q.instance_id and q.evidence_id
        events = [
            a for a in self.l.adoptions
            if a.destination_instance_id == q.instance_id
            and a.evidence_id == q.evidence_id
            and a.valid_time <= q.valid_time
            and a.system_time <= q.system_time
        ]
        if not events:
            return "unknown"
        events.sort(key=lambda a: (a.valid_time, a.system_time))
        return events[-1].stance

    def _attribution(self, q: Query) -> str:
        assert q.instance_id and q.evidence_id
        ev = self.l.evidence[q.evidence_id]
        if q.instance_id in ev.witnesses and ev.valid_time <= q.valid_time and ev.system_time <= q.system_time:
            return "direct_observation"
        acquisitions = self._acquisitions(q.instance_id, q.evidence_id, q)
        if not acquisitions:
            return "none"
        # Latest acquisition controls the present attribution label for this minimal fixture set.
        _, _, op, source = acquisitions[-1]
        if op == "restore":
            return "restored_snapshot"
        if op == "attributed_report":
            return "attributed_report"
        if op == "evidence_copy":
            return "copied_artifact"
        if op == "authorized_state_replication":
            src = self.l.instances[source] if source else None
            dst = self.l.instances[q.instance_id]
            lineage_ok = any(
                edge.source_instance_id == source
                and edge.destination_instance_id == q.instance_id
                and edge.kind == "operational_replica"
                and edge.authorized
                and edge.system_time <= q.system_time
                for edge in self.l.lineage
            )
            if src and src.principal_id == dst.principal_id and lineage_ok:
                return "authorized_same_principal_replication"
            return "copied_artifact"
        if op in {"read", "receive", "copy", "reacquire"}:
            return "copied_artifact"
        return "unknown"

    def _policy_state(self, evidence_id: str, valid_time: int, system_time: int) -> tuple[bool, set[str] | None]:
        ev = self.l.evidence[evidence_id]
        active = True
        if ev.policy == "public":
            allowed: set[str] | None = None
        else:
            allowed = set(ev.allowed_requesters)
        events = [
            p for p in self.l.policies
            if p.evidence_id == evidence_id
            and p.valid_time <= valid_time
            and p.system_time <= system_time
        ]
        for p in sorted(events, key=lambda p: (p.valid_time, p.system_time)):
            if p.operation in {"delete", "quarantine", "revoke_all"}:
                active = False
            elif p.operation == "restore_active":
                active = True
            elif p.operation == "grant_public":
                active = True
                allowed = None
            elif p.operation == "grant" and p.requester:
                active = True
                if allowed is None:
                    allowed = set()
                allowed.add(p.requester)
            elif p.operation == "revoke" and p.requester:
                if allowed is None:
                    # Convert public to explicitly denied-everyone-except impossible in this minimal suite.
                    allowed = set()
                allowed.discard(p.requester)
        return active, allowed

    def _policy_allows(
        self, evidence_id: str, requester: str, valid_time: int, system_time: int, self_access: bool = False
    ) -> bool:
        active, allowed = self._policy_state(evidence_id, valid_time, system_time)
        if not active:
            return False
        if allowed is None:
            return True
        return requester in allowed

    def _eligible_justifications(self, q: Query) -> list[str]:
        assert q.claim_id and q.requester
        eligible = []
        for j in self.l.justifications:
            if j.claim_id != q.claim_id:
                continue
            if all(
                self._policy_allows(eid, q.requester, q.valid_time, q.system_time)
                for eid in j.source_evidence_ids
            ):
                eligible.append(j.justification_id)
        return sorted(eligible)

    def _disclose(self, q: Query) -> bool:
        return bool(self._eligible_justifications(q))

    def _justification(self, q: Query) -> list[str]:
        return self._eligible_justifications(q)


class GenericResolver:
    """Independent generic-row implementation. It does not call TypedResolver helpers."""

    def __init__(self, rows: list[dict[str, Any]]):
        self.rows = rows

    def _rows(self, kind: str) -> list[dict[str, Any]]:
        return [r for r in self.rows if r["type"] == kind]

    def resolve(self, q: Query) -> Any:
        if q.target == "WORLD":
            return self._resolve_world(q)
        if q.target == "EVER_EXPOSED":
            return len(self._exposure_history(q)) > 0
        if q.target == "AVAILABLE":
            return self._resolve_available(q)
        if q.target == "ATTITUDE":
            return self._resolve_attitude(q)
        if q.target == "MEMORY_ATTRIBUTION":
            return self._resolve_attribution(q)
        if q.target == "DISCLOSE":
            return bool(self._eligible_paths(q))
        if q.target == "JUSTIFICATION":
            return self._eligible_paths(q)
        raise ValueError(q.target)

    def _branch_map(self) -> dict[str, dict[str, Any]]:
        return {r["id"]: r for r in self._rows("branch")}

    def _is_inherited(self, source_branch: str, target_branch: str, event_valid: int) -> bool:
        branches = self._branch_map()
        cursor = target_branch
        while cursor != source_branch:
            row = branches.get(cursor)
            if row is None or row.get("parent") is None:
                return False
            cutoff = row.get("fork_valid")
            if cutoff is not None and event_valid > cutoff:
                return False
            cursor = row["parent"]
        return True

    def _resolve_world(self, q: Query) -> Any:
        assert q.proposition is not None and q.branch_id is not None
        possible = []
        for r in self._rows("evidence"):
            if r["proposition"] != q.proposition:
                continue
            if r["valid_time"] > q.valid_time or r["system_time"] > q.system_time:
                continue
            if self._is_inherited(r["about_branch"], q.branch_id, r["valid_time"]):
                possible.append(r)
        if not possible:
            return None
        possible.sort(key=lambda r: (r["valid_time"], r["system_time"], r["id"]))
        return possible[-1]["truth"]

    def _evidence_row(self, evidence_id: str) -> dict[str, Any]:
        return next(r for r in self._rows("evidence") if r["id"] == evidence_id)

    def _instance_map(self) -> dict[str, str]:
        return {r["id"]: r["principal"] for r in self._rows("instance")}

    def _exposure_history(self, q: Query) -> list[tuple[int, int, str, str | None]]:
        assert q.instance_id and q.evidence_id
        history: list[tuple[int, int, str, str | None]] = []
        ev = self._evidence_row(q.evidence_id)
        if q.instance_id in ev.get("witnesses", ()) and ev["valid_time"] <= q.valid_time and ev["system_time"] <= q.system_time:
            history.append((ev["valid_time"], ev["system_time"], "observe", None))
        for r in self._rows("transfer"):
            if r["destination"] == q.instance_id and r["evidence"] == q.evidence_id:
                if r["valid_time"] <= q.valid_time and r["system_time"] <= q.system_time:
                    history.append((r["valid_time"], r["system_time"], r["kind"], r["source"]))
        for r in self._rows("exposure"):
            if r["destination"] == q.instance_id and r["evidence"] == q.evidence_id:
                if r["valid_time"] <= q.valid_time and r["system_time"] <= q.system_time:
                    history.append((r["valid_time"], r["system_time"], r["operation"], None))
        snapshots = {r["id"]: r for r in self._rows("snapshot")}
        for r in self._rows("restore"):
            if r["destination"] != q.instance_id:
                continue
            if r["valid_time"] > q.valid_time or r["system_time"] > q.system_time:
                continue
            snap = snapshots[r["snapshot"]]
            if q.evidence_id in snap["entries"]:
                if ev["system_time"] <= snap["cutoff_system"]:
                    history.append((r["valid_time"], r["system_time"], "restore", snap["source"]))
        return sorted(history)

    def _policy(self, evidence_id: str, q: Query) -> tuple[bool, set[str] | None]:
        ev = self._evidence_row(evidence_id)
        active = True
        allowed: set[str] | None
        if ev.get("policy", "public") == "public":
            allowed = None
        else:
            allowed = set(ev.get("allowed_requesters", ()))
        changes = [
            r for r in self._rows("policy")
            if r["evidence"] == evidence_id
            and r["valid_time"] <= q.valid_time
            and r["system_time"] <= q.system_time
        ]
        changes.sort(key=lambda r: (r["valid_time"], r["system_time"]))
        for r in changes:
            op = r["operation"]
            if op in {"delete", "quarantine", "revoke_all"}:
                active = False
            elif op == "restore_active":
                active = True
            elif op == "grant_public":
                active, allowed = True, None
            elif op == "grant" and r.get("requester"):
                active = True
                if allowed is None:
                    allowed = set()
                allowed.add(r["requester"])
            elif op == "revoke" and r.get("requester"):
                if allowed is None:
                    allowed = set()
                allowed.discard(r["requester"])
        return active, allowed

    def _can_use(self, evidence_id: str, requester: str, q: Query) -> bool:
        active, allowed = self._policy(evidence_id, q)
        return active and (allowed is None or requester in allowed)

    def _resolve_available(self, q: Query) -> bool:
        assert q.instance_id and q.evidence_id
        if not self._exposure_history(q):
            return False
        local = True
        ops = [
            r for r in self._rows("exposure")
            if r["destination"] == q.instance_id
            and r["evidence"] == q.evidence_id
            and r["valid_time"] <= q.valid_time
            and r["system_time"] <= q.system_time
        ]
        ops.sort(key=lambda r: (r["valid_time"], r["system_time"]))
        for r in ops:
            if r["operation"] in {"self_seal", "forget"}:
                local = False
            elif r["operation"] in {"self_unseal", "reacquire", "read", "observe", "receive", "copy", "restore"}:
                local = True
        return local and self._can_use(q.evidence_id, q.instance_id, q)

    def _resolve_attitude(self, q: Query) -> str:
        assert q.instance_id and q.evidence_id
        options = [
            r for r in self._rows("adoption")
            if r["destination"] == q.instance_id
            and r["evidence"] == q.evidence_id
            and r["valid_time"] <= q.valid_time
            and r["system_time"] <= q.system_time
        ]
        if not options:
            return "unknown"
        options.sort(key=lambda r: (r["valid_time"], r["system_time"]))
        return options[-1]["stance"]

    def _resolve_attribution(self, q: Query) -> str:
        assert q.instance_id and q.evidence_id
        ev = self._evidence_row(q.evidence_id)
        if q.instance_id in ev.get("witnesses", ()) and ev["valid_time"] <= q.valid_time and ev["system_time"] <= q.system_time:
            return "direct_observation"
        history = self._exposure_history(q)
        if not history:
            return "none"
        _, _, op, source = history[-1]
        if op == "restore":
            return "restored_snapshot"
        if op == "attributed_report":
            return "attributed_report"
        if op == "evidence_copy":
            return "copied_artifact"
        if op == "authorized_state_replication":
            principals = self._instance_map()
            lineage_ok = any(
                r["source"] == source
                and r["destination"] == q.instance_id
                and r["kind"] == "operational_replica"
                and r.get("authorized", False)
                and r["system_time"] <= q.system_time
                for r in self._rows("lineage")
            )
            if source and principals.get(source) == principals.get(q.instance_id) and lineage_ok:
                return "authorized_same_principal_replication"
            return "copied_artifact"
        if op in {"read", "receive", "copy", "reacquire"}:
            return "copied_artifact"
        return "unknown"

    def _eligible_paths(self, q: Query) -> list[str]:
        assert q.claim_id and q.requester
        out = []
        for r in self._rows("justification"):
            if r["claim"] != q.claim_id:
                continue
            if all(self._can_use(eid, q.requester, q) for eid in r["sources"]):
                out.append(r["id"])
        return sorted(out)


def fixtures() -> list[Fixture]:
    base = (
        {"type": "branch", "id": "W0", "parent": None, "fork_valid": None},
        {"type": "branch", "id": "W1", "parent": "W0", "fork_valid": 10},
        {"type": "branch", "id": "W2", "parent": None, "fork_valid": None},
        {"type": "instance", "id": "M1", "principal": "P"},
        {"type": "instance", "id": "M2", "principal": "P"},
        {"type": "instance", "id": "M3", "principal": "Q"},
        {"type": "lineage", "kind": "operational_replica", "source": "M1", "destination": "M2", "authorized": True, "system_time": 1},
        {"type": "lineage", "kind": "identity_fork", "source": "M1", "destination": "M3", "authorized": True, "system_time": 1},
    )

    out: list[Fixture] = []

    events = base + (
        {"type": "evidence", "id": "EX", "proposition": "key=room4", "truth": True, "about_branch": "W0",
         "valid_time": 5, "system_time": 5, "witnesses": ["M1"]},
    )
    qs = (
        Query("m1_direct", "MEMORY_ATTRIBUTION", 9, 9, instance_id="M1", evidence_id="EX"),
        Query("m2_not_exposed", "EVER_EXPOSED", 9, 9, instance_id="M2", evidence_id="EX"),
        Query("m3_not_exposed", "EVER_EXPOSED", 9, 9, instance_id="M3", evidence_id="EX"),
    )
    out.append(Fixture("unsynchronized_replicas", events, qs, {
        "m1_direct": "direct_observation", "m2_not_exposed": False, "m3_not_exposed": False
    }))

    events = base + (
        {"type": "evidence", "id": "EX", "proposition": "key=room4", "truth": True, "about_branch": "W0",
         "valid_time": 5, "system_time": 5, "witnesses": ["M1"]},
        {"type": "transfer", "evidence": "EX", "source": "M1", "destination": "M3", "kind": "evidence_copy",
         "valid_time": 12, "system_time": 12, "authorized": True, "source_branch": "W0", "destination_branch": "W2"},
        {"type": "adoption", "evidence": "EX", "destination": "M3", "stance": "believe",
         "valid_time": 13, "system_time": 13, "context_branch": "W2"},
    )
    qs = (
        Query("fork_exposed", "EVER_EXPOSED", 14, 14, instance_id="M3", evidence_id="EX"),
        Query("fork_belief", "ATTITUDE", 14, 14, instance_id="M3", evidence_id="EX"),
        Query("fork_attribution", "MEMORY_ATTRIBUTION", 14, 14, instance_id="M3", evidence_id="EX"),
        Query("w2_world", "WORLD", 14, 14, proposition="key=room4", branch_id="W2"),
        Query("w0_world", "WORLD", 14, 14, proposition="key=room4", branch_id="W0"),
    )
    out.append(Fixture("identity_fork_copy_cross_world", events, qs, {
        "fork_exposed": True,
        "fork_belief": "believe",
        "fork_attribution": "copied_artifact",
        "w2_world": None,
        "w0_world": True,
    }))

    events = base + (
        {"type": "evidence", "id": "ER", "proposition": "bridge=open", "truth": True, "about_branch": "W0",
         "valid_time": 4, "system_time": 4, "witnesses": ["M1"]},
        {"type": "transfer", "evidence": "ER", "source": "M1", "destination": "M3", "kind": "attributed_report",
         "valid_time": 8, "system_time": 8, "authorized": True, "source_branch": "W0", "destination_branch": "W2"},
        {"type": "adoption", "evidence": "ER", "destination": "M3", "stance": "disbelieve",
         "valid_time": 9, "system_time": 9, "context_branch": "W2"},
    )
    qs = (
        Query("reported", "MEMORY_ATTRIBUTION", 10, 10, instance_id="M3", evidence_id="ER"),
        Query("rejected", "ATTITUDE", 10, 10, instance_id="M3", evidence_id="ER"),
        Query("still_exposed", "EVER_EXPOSED", 10, 10, instance_id="M3", evidence_id="ER"),
    )
    out.append(Fixture("receipt_rejection", events, qs, {
        "reported": "attributed_report", "rejected": "disbelieve", "still_exposed": True
    }))

    events = base + (
        {"type": "evidence", "id": "ES", "proposition": "diagnosis=X", "truth": True, "about_branch": "W0",
         "valid_time": 2, "system_time": 2, "witnesses": ["M2"], "policy": "private",
         "allowed_requesters": ["M2"]},
        {"type": "exposure", "evidence": "ES", "destination": "M2", "operation": "self_seal",
         "valid_time": 7, "system_time": 7},
        {"type": "exposure", "evidence": "ES", "destination": "M2", "operation": "self_unseal",
         "valid_time": 11, "system_time": 11},
        {"type": "exposure", "evidence": "ES", "destination": "M2", "operation": "forget",
         "valid_time": 14, "system_time": 14},
        {"type": "exposure", "evidence": "ES", "destination": "M2", "operation": "reacquire",
         "valid_time": 18, "system_time": 18},
    )
    qs = (
        Query("hist_after_seal", "EVER_EXPOSED", 8, 8, instance_id="M2", evidence_id="ES"),
        Query("unavailable_sealed", "AVAILABLE", 8, 8, instance_id="M2", evidence_id="ES"),
        Query("available_unsealed", "AVAILABLE", 12, 12, instance_id="M2", evidence_id="ES"),
        Query("unavailable_forgotten", "AVAILABLE", 15, 15, instance_id="M2", evidence_id="ES"),
        Query("available_reacquired", "AVAILABLE", 19, 19, instance_id="M2", evidence_id="ES"),
    )
    out.append(Fixture("exposure_availability_lifecycle", events, qs, {
        "hist_after_seal": True,
        "unavailable_sealed": False,
        "available_unsealed": True,
        "unavailable_forgotten": False,
        "available_reacquired": True,
    }))

    events = base + (
        {"type": "evidence", "id": "EP", "proposition": "route=safe", "truth": True, "about_branch": "W0",
         "valid_time": 2, "system_time": 2, "witnesses": ["M1"], "policy": "private",
         "allowed_requesters": ["U"]},
        {"type": "evidence", "id": "EU", "proposition": "route=safe", "truth": True, "about_branch": "W0",
         "valid_time": 3, "system_time": 3, "witnesses": ["M2"], "policy": "public"},
        {"type": "justification", "id": "J_PRIVATE", "claim": "C_ROUTE", "sources": ["EP"]},
        {"type": "justification", "id": "J_PUBLIC", "claim": "C_ROUTE", "sources": ["EU"]},
        {"type": "policy", "evidence": "EP", "operation": "revoke", "requester": "U",
         "valid_time": 10, "system_time": 10},
    )
    qs = (
        Query("pre_revoke_paths", "JUSTIFICATION", 9, 9, claim_id="C_ROUTE", requester="U"),
        Query("post_revoke_paths", "JUSTIFICATION", 11, 11, claim_id="C_ROUTE", requester="U"),
        Query("post_revoke_disclose", "DISCLOSE", 11, 11, claim_id="C_ROUTE", requester="U"),
    )
    out.append(Fixture("alternative_public_support", events, qs, {
        "pre_revoke_paths": ["J_PRIVATE", "J_PUBLIC"],
        "post_revoke_paths": ["J_PUBLIC"],
        "post_revoke_disclose": True,
    }))

    events = base + (
        {"type": "evidence", "id": "EP", "proposition": "route=safe", "truth": True, "about_branch": "W0",
         "valid_time": 2, "system_time": 2, "witnesses": ["M1"], "policy": "private",
         "allowed_requesters": ["U"]},
        {"type": "justification", "id": "J_PRIVATE", "claim": "C_ROUTE", "sources": ["EP"]},
        {"type": "policy", "evidence": "EP", "operation": "revoke", "requester": "U",
         "valid_time": 10, "system_time": 10},
    )
    qs = (
        Query("protected_only_pre", "DISCLOSE", 9, 9, claim_id="C_ROUTE", requester="U"),
        Query("protected_only_post", "DISCLOSE", 11, 11, claim_id="C_ROUTE", requester="U"),
    )
    out.append(Fixture("protected_only_revocation", events, qs, {
        "protected_only_pre": True, "protected_only_post": False
    }))

    events = base + (
        {"type": "evidence", "id": "E_PRE", "proposition": "flag=pre", "truth": True, "about_branch": "W0",
         "valid_time": 5, "system_time": 20},
        {"type": "evidence", "id": "E_POST", "proposition": "flag=post", "truth": True, "about_branch": "W0",
         "valid_time": 15, "system_time": 15},
    )
    qs = (
        Query("late_before_ingest", "WORLD", 6, 19, proposition="flag=pre", branch_id="W1"),
        Query("late_after_ingest", "WORLD", 6, 21, proposition="flag=pre", branch_id="W1"),
        Query("postfork_parent_hidden", "WORLD", 16, 20, proposition="flag=post", branch_id="W1"),
        Query("postfork_parent_root", "WORLD", 16, 20, proposition="flag=post", branch_id="W0"),
    )
    out.append(Fixture("fork_cutoff_vs_late_import", events, qs, {
        "late_before_ingest": None,
        "late_after_ingest": True,
        "postfork_parent_hidden": None,
        "postfork_parent_root": True,
    }))

    events = base + (
        {"type": "evidence", "id": "EA", "proposition": "task=A", "truth": True, "about_branch": "W0",
         "valid_time": 4, "system_time": 4, "witnesses": ["M1"]},
        {"type": "evidence", "id": "EB", "proposition": "task=B", "truth": True, "about_branch": "W0",
         "valid_time": 14, "system_time": 14, "witnesses": ["M1"]},
        {"type": "snapshot", "id": "S1", "source": "M1", "cutoff_system": 10, "entries": ["EA"]},
        {"type": "lineage", "kind": "restore", "source": "M1", "destination": "M2",
         "authorized": True, "system_time": 20, "snapshot_id": "S1"},
        {"type": "restore", "snapshot": "S1", "destination": "M2", "valid_time": 20, "system_time": 20},
        {"type": "transfer", "evidence": "EB", "source": "M1", "destination": "M2", "kind": "attributed_report",
         "valid_time": 22, "system_time": 22, "authorized": True, "source_branch": "W0", "destination_branch": "W0"},
    )
    qs = (
        Query("restored_pre", "EVER_EXPOSED", 21, 21, instance_id="M2", evidence_id="EA"),
        Query("restored_attr", "MEMORY_ATTRIBUTION", 21, 21, instance_id="M2", evidence_id="EA"),
        Query("gap_not_inherited", "EVER_EXPOSED", 21, 21, instance_id="M2", evidence_id="EB"),
        Query("gap_reported_later", "MEMORY_ATTRIBUTION", 23, 23, instance_id="M2", evidence_id="EB"),
    )
    out.append(Fixture("snapshot_restore_gap", events, qs, {
        "restored_pre": True,
        "restored_attr": "restored_snapshot",
        "gap_not_inherited": False,
        "gap_reported_later": "attributed_report",
    }))

    events = base + (
        {"type": "evidence", "id": "EC", "proposition": "code=42", "truth": True, "about_branch": "W0",
         "valid_time": 4, "system_time": 4, "witnesses": ["M1"]},
        {"type": "transfer", "evidence": "EC", "source": "M1", "destination": "M2",
         "kind": "authorized_state_replication", "valid_time": 6, "system_time": 6,
         "authorized": True, "source_branch": "W0", "destination_branch": "W0"},
    )
    qs = (
        Query("authorized_replication", "MEMORY_ATTRIBUTION", 7, 7, instance_id="M2", evidence_id="EC"),
    )
    out.append(Fixture("authorized_same_principal_replication", events, qs, {
        "authorized_replication": "authorized_same_principal_replication"
    }))

    return out


def run() -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    total = 0
    typed_correct = 0
    generic_correct = 0
    agreement = 0

    for fixture in fixtures():
        typed = TypedResolver(compile_typed(fixture.events))
        generic = GenericResolver(compile_generic(fixture.events))
        for q in fixture.queries:
            expected = fixture.expected[q.query_id]
            typed_value = typed.resolve(q)
            generic_value = generic.resolve(q)
            total += 1
            t_ok = typed_value == expected
            g_ok = generic_value == expected
            a_ok = typed_value == generic_value
            typed_correct += int(t_ok)
            generic_correct += int(g_ok)
            agreement += int(a_ok)
            row = {
                "fixture_id": fixture.fixture_id,
                "query_id": q.query_id,
                "target": q.target,
                "expected": expected,
                "typed": typed_value,
                "generic": generic_value,
                "typed_correct": t_ok,
                "generic_correct": g_ok,
                "systems_agree": a_ok,
            }
            results.append(row)
            if not (t_ok and g_ok and a_ok):
                failures.append(row)

    fixture_ids = [fixture.fixture_id for fixture in fixtures()]
    summary = {
        "suite_version": SUITE_VERSION,
        "fixture_ids": fixture_ids,
        "fixture_count": len(fixture_ids),
        "query_count": total,
        "typed_correct": typed_correct,
        "generic_correct": generic_correct,
        "systems_agree": agreement,
        "typed_accuracy": typed_correct / total,
        "generic_accuracy": generic_correct / total,
        "agreement_rate": agreement / total,
        "failure_count": len(failures),
        "interpretation": (
            "Independent literal fixture gold; equal-information typed and generic "
            "implementations are expected to agree. This is semantic conformance, "
            "not evidence that either representation is architecturally superior."
        ),
    }
    return {"summary": summary, "rows": results, "failures": failures}


def write_outputs(output_dir: Path) -> dict[str, Any]:
    report = run()
    output_dir.mkdir(parents=True, exist_ok=True)
    script_path = Path(__file__).resolve()
    manifest = {
        "suite_version": SUITE_VERSION,
        "script": str(script_path.name),
        "script_sha256": hashlib.sha256(script_path.read_bytes()).hexdigest(),
        "python_version": platform.python_version(),
        "fixture_ids": report["summary"]["fixture_ids"],
        "inferential_statistics": False,
        "independent_unit": "fixed_fixture",
        "gold_contract": "literal expected target values embedded in fixtures; no candidate resolver call",
    }
    with (output_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(report["summary"], f, indent=2, ensure_ascii=False)
        f.write("\n")
    with (output_dir / "manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with (output_dir / "per_query.jsonl").open("w", encoding="utf-8") as f:
        for row in report["rows"]:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return report


if __name__ == "__main__":
    report = write_outputs(Path("results/equal_information_conformance_v0_2"))
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    if report["failures"]:
        raise SystemExit(1)
