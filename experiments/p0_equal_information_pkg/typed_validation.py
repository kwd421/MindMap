from __future__ import annotations

from typing import Optional, Sequence

from .model import *
from .validation_common import REQUIRED_FIELDS, TypedEvent, ValidationResult, _dedupe_findings

def parse_typed(events: Sequence[CommonEvent]) -> tuple[list[TypedEvent], ValidationResult]:
    c = RunCounters()
    typed: list[TypedEvent] = []
    findings: list[Finding] = []
    seen: set[str] = set()
    for e in events:
        c.scanned_events += 1
        c.local_checks += 5
        if e.event_id in seen:
            findings.append(Finding("duplicate_event_id", (e.event_id,), "duplicate event id", "typed_ingest"))
        seen.add(e.event_id)
        required = REQUIRED_FIELDS.get(e.event_type)
        if required is None:
            findings.append(Finding("unknown_event_type", (e.event_id,), e.event_type, "typed_ingest"))
            continue
        if not isinstance(e.valid_time, int) or not isinstance(e.system_time, int) or e.valid_time < 0 or e.system_time < 0:
            findings.append(Finding("invalid_time", (e.event_id,), "time must be non-negative integers", "typed_ingest"))
        missing = sorted(required.difference(e.payload))
        if missing:
            findings.append(Finding("missing_required_field", (e.event_id,), ",".join(missing), "typed_ingest"))
            continue
        # Local discriminated-union constraints.
        p = dict(e.payload)
        if e.event_type == "exposure":
            op = p["operation"]
            if op == "observe" and p["source_instance"] is not None:
                findings.append(Finding("observation_has_source_instance", (e.event_id,), str(p["source_instance"]), "typed_ingest"))
            if op in {"receive", "evidence_copy", "state_replication", "reacquire"} and p["source_instance"] is None:
                findings.append(Finding("transfer_missing_source", (e.event_id,), op, "typed_ingest"))
        if e.event_type == "policy" and not p["authorization"]:
            findings.append(Finding("unauthorized_policy_event", (e.event_id,), p["operation"], "typed_ingest"))
        typed.append(TypedEvent(e.event_id, e.event_type, e.valid_time, e.system_time, p))

    # An independently written typed cross-checker. It intentionally does not
    # call validate_generic_audited.
    principals: set[str] = set()
    minds: dict[str, str] = {}
    branches: dict[str, tuple[Optional[str], Optional[int], Optional[int], str]] = {}
    lineages: list[TypedEvent] = []
    exposures: list[TypedEvent] = []
    attitudes: list[TypedEvent] = []
    snapshots: dict[str, TypedEvent] = {}
    evidence: dict[str, TypedEvent] = {}
    for e in typed:
        c.cross_checks += 1
        p = e.payload
        if e.event_type == "principal_create":
            principals.add(p["principal"])
        elif e.event_type == "mind_create":
            minds[p["instance"]] = p["principal"]
        elif e.event_type == "branch_create":
            branches[p["branch"]] = (p["parent"], p["fork_valid"], p["fork_system"], e.event_id)
        elif e.event_type == "lineage":
            lineages.append(e)
        elif e.event_type == "exposure":
            exposures.append(e)
        elif e.event_type == "attitude":
            attitudes.append(e)
        elif e.event_type == "snapshot":
            snapshots[p["snapshot_id"]] = e
        elif e.event_type == "evidence":
            evidence[p["object_id"]] = e

    for inst, principal in minds.items():
        c.cross_checks += 1
        if principal not in principals:
            culprit = next((e.event_id for e in typed if e.event_type == "mind_create" and e.payload["instance"] == inst), inst)
            findings.append(Finding("unknown_principal", (culprit,), principal, "typed_cross"))

    # Branch cycle detection.
    for start in branches:
        c.cross_checks += 1
        cur: Optional[str] = start
        seen_nodes: list[str] = []
        while cur is not None and cur in branches:
            if cur in seen_nodes:
                ids = tuple(branches[n][3] for n in seen_nodes if n in branches)
                findings.append(Finding("branch_cycle", ids, "cycle", "typed_cross"))
                break
            seen_nodes.append(cur)
            cur = branches[cur][0]

    # Lineage DAG and kind constraints.
    adjacency: dict[str, list[tuple[str, str]]] = {}
    for e in lineages:
        p = e.payload
        adjacency.setdefault(p["source_instance"], []).append((p["destination_instance"], e.event_id))
        src, dst, kind = p["source_instance"], p["destination_instance"], p["kind"]
        c.cross_checks += 5
        if src not in minds or dst not in minds:
            findings.append(Finding("unknown_lineage_instance", (e.event_id,), f"{src}->{dst}", "typed_cross"))
            continue
        same = minds[src] == minds[dst]
        if kind == "identity_fork" and same:
            findings.append(Finding("identity_fork_same_principal", (e.event_id,), "identity fork must create new principal", "typed_cross"))
        if kind == "operational_replica" and not same:
            findings.append(Finding("replica_principal_mismatch", (e.event_id,), "replica must preserve principal", "typed_cross"))
        if kind in {"operational_replica", "checkpoint_branch"} and not p["authorization"]:
            findings.append(Finding("missing_replication_authorization", (e.event_id,), "authorization required", "typed_cross"))
        if kind == "restore" and p.get("snapshot_id") not in snapshots:
            findings.append(Finding("missing_snapshot", (e.event_id,), str(p.get("snapshot_id")), "typed_cross"))

    def visit(node: str, active: list[str], active_edges: list[str], done: set[str]) -> None:
        c.cross_checks += 1
        if node in active:
            findings.append(Finding("lineage_cycle", tuple(active_edges), "cycle", "typed_cross"))
            return
        if node in done:
            return
        active.append(node)
        for nxt, eid in adjacency.get(node, []):
            visit(nxt, active, active_edges + [eid], done)
        active.pop()
        done.add(node)

    done: set[str] = set()
    for node in adjacency:
        visit(node, [], [], done)

    for e in exposures:
        p = e.payload
        c.cross_checks += 5
        if p["destination_instance"] not in minds:
            findings.append(Finding("unknown_exposure_instance", (e.event_id,), p["destination_instance"], "typed_cross"))
        if p["object_id"] not in evidence and p["operation"] != "restore":
            findings.append(Finding("unknown_exposure_object", (e.event_id,), p["object_id"], "typed_cross"))
        if p["operation"] == "state_replication":
            eligible = False
            for l in lineages:
                lp = l.payload
                if (
                    lp["source_instance"] == p["source_instance"]
                    and lp["destination_instance"] == p["destination_instance"]
                    and lp["kind"] in {"operational_replica", "checkpoint_branch"}
                    and lp["authorization"]
                    and minds.get(lp["source_instance"]) == minds.get(lp["destination_instance"])
                ):
                    eligible = True
            if not eligible or not p["authorization"]:
                findings.append(Finding("invalid_state_replication", (e.event_id,), "no eligible lineage/authorization", "typed_cross"))
            if p["attribution"] != "same_principal_state_replication":
                findings.append(Finding("state_replication_attribution_mismatch", (e.event_id,), p["attribution"], "typed_cross"))
        if p["operation"] == "evidence_copy" and p["attribution"] == "direct_observation":
            findings.append(Finding("copy_claims_direct_observation", (e.event_id,), "copy cannot be direct observation", "typed_cross"))
        if p["operation"] == "observe" and p["attribution"] != "direct_observation":
            findings.append(Finding("observation_attribution_mismatch", (e.event_id,), p["attribution"], "typed_cross"))
        if p["operation"] == "restore":
            snap = snapshots.get(p.get("snapshot_id"))
            if snap is None or p["object_id"] not in tuple(snap.payload["members"]):
                ids = (e.event_id,) + ((snap.event_id,) if snap else ())
                findings.append(Finding("restore_object_not_in_snapshot", ids, p["object_id"], "typed_cross"))

    for snap in snapshots.values():
        cutoff = snap.payload["cutoff_system"]
        for member in tuple(snap.payload["members"]):
            c.cross_checks += 1
            ev = evidence.get(member)
            if ev is None or ev.system_time > cutoff:
                ids = (snap.event_id,) + ((ev.event_id,) if ev else ())
                findings.append(Finding("snapshot_member_after_cutoff", ids, member, "typed_cross"))

    for a in attitudes:
        c.cross_checks += 1
        ap = a.payload
        prior = [
            e
            for e in exposures
            if e.payload["destination_instance"] == ap["instance"]
            and e.payload["object_id"] == ap["source_object"]
            and e.system_time <= a.system_time
            and e.payload["operation"] in ACQUIRE_OPS
        ]
        if not prior:
            findings.append(Finding("attitude_without_prior_exposure", (a.event_id,), f"{ap['instance']}:{ap['source_object']}", "typed_cross"))

    return typed, ValidationResult(_dedupe_findings(findings), c)
