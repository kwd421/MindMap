from __future__ import annotations

from typing import Any, Optional, Sequence

from .model import *
from .validation_common import TypedEvent

def _events_up_to(events: Sequence[CommonEvent], ts: int) -> list[CommonEvent]:
    return [e for e in events if e.system_time <= ts]


def _branch_path(events: Sequence[CommonEvent], branch: str) -> list[tuple[str, Optional[int]]]:
    branches = {
        e.payload["branch"]: (e.payload["parent"], e.payload["fork_valid"])
        for e in events
        if e.event_type == "branch_create"
    }
    out: list[tuple[str, Optional[int]]] = []
    cur: Optional[str] = branch
    visited: set[str] = set()
    while cur is not None and cur in branches and cur not in visited:
        visited.add(cur)
        parent, fork_valid = branches[cur]
        out.append((cur, fork_valid))
        cur = parent
    return out


def _generic_branch_visible(events: Sequence[CommonEvent], event_branch: str, event_tv: int, query_branch: str) -> bool:
    if event_branch == query_branch:
        return True
    path = _branch_path(events, query_branch)
    for idx, (node, fork_valid) in enumerate(path):
        if idx + 1 < len(path) and path[idx + 1][0] == event_branch:
            cutoffs = [fv for _, fv in path[: idx + 1] if fv is not None]
            return all(event_tv <= cutoff for cutoff in cutoffs)
    return False


def _policy_at(events: Sequence[CommonEvent], object_id: str, ts: int) -> str:
    initial = next((e.payload["policy"] for e in events if e.event_type == "evidence" and e.payload.get("object_id") == object_id), "public")
    updates = [e for e in events if e.event_type == "policy" and e.payload.get("object_id") == object_id and e.system_time <= ts]
    if not updates:
        return initial
    return max(updates, key=lambda e: (e.system_time, e.event_id)).payload["new_policy"]


def _source_family(events: Sequence[CommonEvent], object_id: str) -> Optional[str]:
    ev = next((e for e in events if e.event_type == "evidence" and e.payload.get("object_id") == object_id), None)
    return ev.payload.get("source_family") if ev else None


def generic_answer(events: Sequence[CommonEvent], q: Query, mutant: Optional[str] = None) -> str:
    visible = _events_up_to(events, q.system_time)
    if q.target == "world":
        candidates = []
        for e in visible:
            if e.event_type != "world_claim" or e.payload.get("proposition") != q.proposition:
                continue
            about = e.payload.get("about_branch")
            start = e.payload.get("valid_from")
            end = e.payload.get("valid_to")
            if mutant == "branch_collapse":
                branch_ok = True
            elif mutant == "system_time_fork":
                # Incorrectly uses ingest time as fork-visibility time.
                branch_ok = _generic_branch_visible(visible, about, e.system_time, q.branch)
            else:
                branch_ok = _generic_branch_visible(visible, about, start, q.branch)
            if not branch_ok or not (start <= q.valid_time and (end is None or q.valid_time < end)):
                continue
            if e.payload.get("status") != "active":
                continue
            candidates.append(e)
        if not candidates:
            return UNKNOWN
        selected = max(candidates, key=lambda e: (e.payload["valid_from"], e.system_time, e.event_id))
        return str(selected.payload["value"])

    if q.target in {"ever_exposed", "available", "attribution"}:
        transitions = [
            e
            for e in visible
            if e.event_type == "exposure"
            and e.payload.get("destination_instance") == q.instance
            and e.payload.get("object_id") == q.object_id
        ]
        if q.target == "ever_exposed":
            if mutant == "forget_erases_history" and transitions:
                return "yes" if max(transitions, key=lambda e: (e.system_time, e.event_id)).payload["operation"] in ACQUIRE_OPS else "no"
            return "yes" if any(e.payload["operation"] in ACQUIRE_OPS for e in transitions) else "no"
        if not transitions:
            return UNKNOWN if q.target == "attribution" else "no"
        latest = max(transitions, key=lambda e: (e.system_time, e.event_id))
        if q.target == "available":
            return "yes" if latest.payload["operation"] in ACQUIRE_OPS else "no"
        op = latest.payload["operation"]
        if mutant == "identity_fork_first_person" and op in {"evidence_copy", "state_replication"}:
            return "same_principal_state_replication"
        if op == "observe":
            return "direct_observation"
        if op == "state_replication":
            # Derive from lineage rather than trusting the declared field.
            src, dst = latest.payload.get("source_instance"), latest.payload.get("destination_instance")
            minds = {e.payload["instance"]: e.payload["principal"] for e in visible if e.event_type == "mind_create"}
            eligible = any(
                e.event_type == "lineage"
                and e.payload.get("source_instance") == src
                and e.payload.get("destination_instance") == dst
                and e.payload.get("kind") in {"operational_replica", "checkpoint_branch"}
                and e.payload.get("authorization")
                and minds.get(src) == minds.get(dst)
                for e in visible
            )
            return "same_principal_state_replication" if eligible else "evidence_copy"
        if op == "restore":
            return "same_principal_snapshot_inheritance"
        if latest.payload.get("attribution") == "reconstruction":
            return "reconstruction"
        return "evidence_copy" if op == "evidence_copy" else "attributed_report"

    if q.target == "attitude":
        proposition, about = (q.proposition or ""), q.branch
        if "@" in proposition:
            proposition, about = proposition.rsplit("@", 1)
        candidates = [
            e
            for e in visible
            if e.event_type == "attitude"
            and e.payload.get("instance") == q.instance
            and e.payload.get("proposition") == proposition
            and e.payload.get("about_branch") == about
        ]
        if mutant == "receipt_implies_belief" and not candidates:
            receipts = [
                e
                for e in visible
                if e.event_type == "exposure"
                and e.payload.get("destination_instance") == q.instance
                and e.payload.get("operation") in {"receive", "evidence_copy", "state_replication", "restore"}
            ]
            if receipts:
                return "believe:true"
        if not candidates:
            return UNKNOWN
        latest = max(candidates, key=lambda e: (e.system_time, e.event_id))
        return f"{latest.payload['stance']}:{latest.payload['value']}"

    if q.target == "source_actor":
        ev = next((e for e in visible if e.event_type == "evidence" and e.payload.get("object_id") == q.object_id), None)
        return str(ev.payload.get("actor_instance")) if ev else UNKNOWN

    if q.target == "merge_eligible":
        minds = {e.payload["instance"]: e.payload["principal"] for e in visible if e.event_type == "mind_create"}
        edges = [
            e
            for e in visible
            if e.event_type == "lineage"
            and e.payload.get("source_instance") == q.source_instance
            and e.payload.get("destination_instance") == q.destination_instance
        ]
        if not edges:
            return "no"
        edge = max(edges, key=lambda e: (e.system_time, e.event_id))
        ok = (
            minds.get(q.source_instance) == minds.get(q.destination_instance)
            and edge.payload.get("kind") in {"operational_replica", "checkpoint_branch"}
            and bool(edge.payload.get("authorization"))
        )
        return "yes" if ok else "no"

    if q.target in {"disclose", "justification"}:
        paths = [
            e
            for e in visible
            if e.event_type == "justification" and e.payload.get("claim_id") == q.claim_id
        ]
        eligible: list[tuple[CommonEvent, tuple[str, ...]]] = []
        for path in paths:
            members = tuple(path.payload.get("members", ()))
            families = tuple(sorted({f for m in members if (f := _source_family(visible, m)) is not None}))
            if mutant == "same_origin_independent":
                independence = len(members)
            else:
                independence = len(families)
            if independence < int(path.payload.get("min_independent", 1)):
                continue
            if mutant == "flatten_policy":
                policies = ["public"]
            else:
                policies = [_policy_at(visible, m, q.system_time) for m in members]
            if all(POLICY_RANK.get(p, 99) <= CLEARANCE.get(q.requester, 0) for p in policies):
                eligible.append((path, families))
        if not eligible:
            return "no" if q.target == "disclose" else "withhold"
        chosen = min(eligible, key=lambda item: (len(item[1]), item[0].event_id))
        if q.target == "disclose":
            return "yes"
        return ",".join(chosen[1]) if chosen[1] else "withhold"

    raise ValueError(f"unsupported target: {q.target}")


class TypedState:
    """Materialized typed projection used by the typed resolver.

    This is intentionally implemented independently from generic_answer. It is
    still fed the same CommonEvent information.
    """

    def __init__(self, typed: Sequence[TypedEvent]):
        self.events = list(typed)
        self.principal_by_instance: dict[str, str] = {}
        self.branch_parent: dict[str, Optional[str]] = {}
        self.branch_fork_valid: dict[str, Optional[int]] = {}
        self.lineages: list[TypedEvent] = []
        self.exposures: list[TypedEvent] = []
        self.attitudes: list[TypedEvent] = []
        self.world_claims: list[TypedEvent] = []
        self.evidence: dict[str, TypedEvent] = {}
        self.policies: list[TypedEvent] = []
        self.justifications: list[TypedEvent] = []
        for e in typed:
            p = e.payload
            if e.event_type == "mind_create":
                self.principal_by_instance[p["instance"]] = p["principal"]
            elif e.event_type == "branch_create":
                self.branch_parent[p["branch"]] = p["parent"]
                self.branch_fork_valid[p["branch"]] = p["fork_valid"]
            elif e.event_type == "lineage":
                self.lineages.append(e)
            elif e.event_type == "exposure":
                self.exposures.append(e)
            elif e.event_type == "attitude":
                self.attitudes.append(e)
            elif e.event_type == "world_claim":
                self.world_claims.append(e)
            elif e.event_type == "evidence":
                self.evidence[p["object_id"]] = e
            elif e.event_type == "policy":
                self.policies.append(e)
            elif e.event_type == "justification":
                self.justifications.append(e)

    def branch_visible(self, event_branch: str, event_tv: int, query_branch: str) -> bool:
        if event_branch == query_branch:
            return True
        cur = query_branch
        cutoffs: list[int] = []
        seen: set[str] = set()
        while cur in self.branch_parent and cur not in seen:
            seen.add(cur)
            parent = self.branch_parent[cur]
            fork = self.branch_fork_valid.get(cur)
            if fork is not None:
                cutoffs.append(fork)
            if parent == event_branch:
                return all(event_tv <= cutoff for cutoff in cutoffs)
            if parent is None:
                return False
            cur = parent
        return False

    def policy_at(self, object_id: str, ts: int) -> str:
        base = self.evidence.get(object_id)
        initial = base.payload["policy"] if base else "public"
        updates = [e for e in self.policies if e.payload["object_id"] == object_id and e.system_time <= ts]
        return max(updates, key=lambda e: (e.system_time, e.event_id)).payload["new_policy"] if updates else initial

    def family(self, object_id: str) -> Optional[str]:
        ev = self.evidence.get(object_id)
        return ev.payload.get("source_family") if ev else None

    def answer(self, q: Query) -> str:
        if q.target == "world":
            candidates = [
                e
                for e in self.world_claims
                if e.system_time <= q.system_time
                and e.payload["proposition"] == q.proposition
                and self.branch_visible(e.payload["about_branch"], e.payload["valid_from"], q.branch)
                and e.payload["valid_from"] <= q.valid_time
                and (e.payload["valid_to"] is None or q.valid_time < e.payload["valid_to"])
                and e.payload["status"] == "active"
            ]
            if not candidates:
                return UNKNOWN
            return str(max(candidates, key=lambda e: (e.payload["valid_from"], e.system_time, e.event_id)).payload["value"])

        if q.target in {"ever_exposed", "available", "attribution"}:
            xs = [
                e
                for e in self.exposures
                if e.system_time <= q.system_time
                and e.payload["destination_instance"] == q.instance
                and e.payload["object_id"] == q.object_id
            ]
            if q.target == "ever_exposed":
                return "yes" if any(e.payload["operation"] in ACQUIRE_OPS for e in xs) else "no"
            if not xs:
                return UNKNOWN if q.target == "attribution" else "no"
            latest = max(xs, key=lambda e: (e.system_time, e.event_id))
            if q.target == "available":
                return "yes" if latest.payload["operation"] in ACQUIRE_OPS else "no"
            op = latest.payload["operation"]
            if op == "observe":
                return "direct_observation"
            if op == "state_replication":
                src, dst = latest.payload["source_instance"], latest.payload["destination_instance"]
                eligible = any(
                    l.payload["source_instance"] == src
                    and l.payload["destination_instance"] == dst
                    and l.payload["kind"] in {"operational_replica", "checkpoint_branch"}
                    and l.payload["authorization"]
                    and self.principal_by_instance.get(src) == self.principal_by_instance.get(dst)
                    for l in self.lineages
                    if l.system_time <= q.system_time
                )
                return "same_principal_state_replication" if eligible else "evidence_copy"
            if op == "restore":
                return "same_principal_snapshot_inheritance"
            if latest.payload["attribution"] == "reconstruction":
                return "reconstruction"
            return "evidence_copy" if op == "evidence_copy" else "attributed_report"

        if q.target == "attitude":
            proposition, about = (q.proposition or ""), q.branch
            if "@" in proposition:
                proposition, about = proposition.rsplit("@", 1)
            xs = [
                e
                for e in self.attitudes
                if e.system_time <= q.system_time
                and e.payload["instance"] == q.instance
                and e.payload["proposition"] == proposition
                and e.payload["about_branch"] == about
            ]
            if not xs:
                return UNKNOWN
            latest = max(xs, key=lambda e: (e.system_time, e.event_id))
            return f"{latest.payload['stance']}:{latest.payload['value']}"

        if q.target == "source_actor":
            ev = self.evidence.get(q.object_id or "")
            return str(ev.payload.get("actor_instance")) if ev and ev.system_time <= q.system_time else UNKNOWN

        if q.target == "merge_eligible":
            xs = [
                e
                for e in self.lineages
                if e.system_time <= q.system_time
                and e.payload["source_instance"] == q.source_instance
                and e.payload["destination_instance"] == q.destination_instance
            ]
            if not xs:
                return "no"
            edge = max(xs, key=lambda e: (e.system_time, e.event_id))
            ok = (
                self.principal_by_instance.get(q.source_instance) == self.principal_by_instance.get(q.destination_instance)
                and edge.payload["kind"] in {"operational_replica", "checkpoint_branch"}
                and edge.payload["authorization"]
            )
            return "yes" if ok else "no"

        if q.target in {"disclose", "justification"}:
            paths = [e for e in self.justifications if e.system_time <= q.system_time and e.payload["claim_id"] == q.claim_id]
            eligible: list[tuple[TypedEvent, tuple[str, ...]]] = []
            for path in paths:
                members = tuple(path.payload["members"])
                families = tuple(sorted({f for m in members if (f := self.family(m)) is not None}))
                if len(families) < int(path.payload["min_independent"]):
                    continue
                if all(POLICY_RANK.get(self.policy_at(m, q.system_time), 99) <= CLEARANCE.get(q.requester, 0) for m in members):
                    eligible.append((path, families))
            if not eligible:
                return "no" if q.target == "disclose" else "withhold"
            chosen = min(eligible, key=lambda item: (len(item[1]), item[0].event_id))
            return "yes" if q.target == "disclose" else ",".join(chosen[1])

        raise ValueError(f"unsupported target: {q.target}")
