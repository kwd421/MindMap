from __future__ import annotations

from typing import Optional, Sequence

from .model import *
from .validation_common import REQUIRED_FIELDS, ValidationResult, _dedupe_findings

def validate_generic_audited(events: Sequence[CommonEvent]) -> ValidationResult:
    c = RunCounters()
    findings: list[Finding] = []
    seen: dict[str, int] = {}
    event_map: dict[str, CommonEvent] = {}
    for position, e in enumerate(events):
        c.scanned_events += 1
        c.local_checks += 4
        if e.event_id in seen:
            findings.append(Finding("duplicate_event_id", (e.event_id,), "duplicate event id", "audit"))
        seen[e.event_id] = position
        event_map[e.event_id] = e
        if not isinstance(e.valid_time, int) or not isinstance(e.system_time, int) or e.valid_time < 0 or e.system_time < 0:
            findings.append(Finding("invalid_time", (e.event_id,), "time must be non-negative integers", "audit"))
        required = REQUIRED_FIELDS.get(e.event_type)
        if required is None:
            findings.append(Finding("unknown_event_type", (e.event_id,), e.event_type, "audit"))
        else:
            missing = sorted(required.difference(e.payload))
            if missing:
                findings.append(Finding("missing_required_field", (e.event_id,), ",".join(missing), "audit"))

    # Build generic relation views from dictionaries.
    principals = {e.payload.get("principal") for e in events if e.event_type == "principal_create"}
    minds = {e.payload.get("instance"): e.payload.get("principal") for e in events if e.event_type == "mind_create"}
    branches = {e.payload.get("branch"): e for e in events if e.event_type == "branch_create"}
    lineages = [e for e in events if e.event_type == "lineage"]
    exposures = [e for e in events if e.event_type == "exposure"]
    attitudes = [e for e in events if e.event_type == "attitude"]
    snapshots = {e.payload.get("snapshot_id"): e for e in events if e.event_type == "snapshot"}
    evidence = {e.payload.get("object_id"): e for e in events if e.event_type == "evidence"}

    for instance, principal in minds.items():
        c.cross_checks += 1
        if principal not in principals:
            culprit = next((e.event_id for e in events if e.event_type == "mind_create" and e.payload.get("instance") == instance), "")
            findings.append(Finding("unknown_principal", (culprit,), str(principal), "audit"))

    # Generic SQL-like DAG checks.
    def find_cycles(edges: Mapping[str, Optional[str]], code: str) -> None:
        for node in edges:
            c.cross_checks += 1
            seen_local: set[str] = set()
            cur: Optional[str] = node
            while cur is not None and cur in edges:
                if cur in seen_local:
                    related = tuple(
                        e.event_id
                        for e in events
                        if (e.event_type == "branch_create" and e.payload.get("branch") in seen_local)
                        or (e.event_type == "lineage" and e.payload.get("destination_instance") in seen_local)
                    )
                    findings.append(Finding(code, related or (node,), "cycle", "audit"))
                    break
                seen_local.add(cur)
                cur = edges[cur]

    branch_parent = {str(k): v.payload.get("parent") for k, v in branches.items() if k is not None}
    find_cycles(branch_parent, "branch_cycle")

    # Lineage can be a DAG with multiple parents. Detect cycles through DFS.
    children: dict[str, list[tuple[str, str]]] = {}
    for e in lineages:
        src = e.payload.get("source_instance")
        dst = e.payload.get("destination_instance")
        children.setdefault(str(src), []).append((str(dst), e.event_id))
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str, path_events: list[str]) -> None:
        c.cross_checks += 1
        if node in visiting:
            findings.append(Finding("lineage_cycle", tuple(path_events), "cycle", "audit"))
            return
        if node in visited:
            return
        visiting.add(node)
        for nxt, eid in children.get(node, []):
            dfs(nxt, path_events + [eid])
        visiting.remove(node)
        visited.add(node)

    for node in list(children):
        dfs(node, [])

    for e in lineages:
        c.cross_checks += 5
        src = e.payload.get("source_instance")
        dst = e.payload.get("destination_instance")
        kind = e.payload.get("kind")
        if src not in minds or dst not in minds:
            findings.append(Finding("unknown_lineage_instance", (e.event_id,), f"{src}->{dst}", "audit"))
            continue
        same = minds[src] == minds[dst]
        if kind == "identity_fork" and same:
            findings.append(Finding("identity_fork_same_principal", (e.event_id,), "identity fork must create a new principal", "audit"))
        if kind == "operational_replica" and not same:
            findings.append(Finding("replica_principal_mismatch", (e.event_id,), "replica must preserve principal", "audit"))
        if kind in {"operational_replica", "checkpoint_branch"} and not e.payload.get("authorization"):
            findings.append(Finding("missing_replication_authorization", (e.event_id,), "authorization required", "audit"))
        snap_id = e.payload.get("snapshot_id")
        if kind == "restore" and snap_id not in snapshots:
            findings.append(Finding("missing_snapshot", (e.event_id,), str(snap_id), "audit"))

    # Exposure constraints and transfer/adoption ordering.
    for e in exposures:
        c.cross_checks += 5
        dst = e.payload.get("destination_instance")
        src = e.payload.get("source_instance")
        obj = e.payload.get("object_id")
        op = e.payload.get("operation")
        if dst not in minds:
            findings.append(Finding("unknown_exposure_instance", (e.event_id,), str(dst), "audit"))
        if obj not in evidence and op != "restore":
            findings.append(Finding("unknown_exposure_object", (e.event_id,), str(obj), "audit"))
        if op == "state_replication":
            eligible = [
                l
                for l in lineages
                if l.payload.get("source_instance") == src
                and l.payload.get("destination_instance") == dst
                and l.payload.get("kind") in {"operational_replica", "checkpoint_branch"}
                and l.payload.get("authorization")
                and minds.get(src) == minds.get(dst)
            ]
            if not eligible or not e.payload.get("authorization"):
                findings.append(Finding("invalid_state_replication", (e.event_id,), "no eligible lineage/authorization", "audit"))
            if e.payload.get("attribution") != "same_principal_state_replication":
                findings.append(Finding("state_replication_attribution_mismatch", (e.event_id,), str(e.payload.get("attribution")), "audit"))
        if op == "evidence_copy" and e.payload.get("attribution") == "direct_observation":
            findings.append(Finding("copy_claims_direct_observation", (e.event_id,), "copy cannot be direct observation", "audit"))
        if op == "observe" and e.payload.get("attribution") != "direct_observation":
            findings.append(Finding("observation_attribution_mismatch", (e.event_id,), str(e.payload.get("attribution")), "audit"))
        if op == "restore":
            snap_id = e.payload.get("snapshot_id")
            snap = snapshots.get(snap_id)
            if snap is None or obj not in tuple(snap.payload.get("members", ())):
                findings.append(Finding("restore_object_not_in_snapshot", (e.event_id,) + ((snap.event_id,) if snap else ()), str(obj), "audit"))

    for e in snapshots.values():
        c.cross_checks += 1
        cutoff = e.payload.get("cutoff_system")
        for member in tuple(e.payload.get("members", ())):
            ev = evidence.get(member)
            if ev is None or ev.system_time > cutoff:
                ids = (e.event_id,) + ((ev.event_id,) if ev else ())
                findings.append(Finding("snapshot_member_after_cutoff", ids, str(member), "audit"))

    for e in attitudes:
        c.cross_checks += 1
        inst = e.payload.get("instance")
        obj = e.payload.get("source_object")
        prior = [
            x
            for x in exposures
            if x.payload.get("destination_instance") == inst
            and x.payload.get("object_id") == obj
            and x.system_time <= e.system_time
            and x.payload.get("operation") in ACQUIRE_OPS
        ]
        if not prior:
            findings.append(Finding("attitude_without_prior_exposure", (e.event_id,), f"{inst}:{obj}", "audit"))

    return ValidationResult(_dedupe_findings(findings), c)

