from __future__ import annotations

from dataclasses import replace
from typing import Optional, Sequence

from .model import *

def _replace_event(events: Sequence[CommonEvent], event_id: str, fn) -> tuple[CommonEvent, ...]:
    return tuple(fn(e) if e.event_id == event_id else e for e in events)


def make_faults(fixtures: Sequence[Fixture]) -> list[Fault]:
    by_id = {f.fixture_id: f for f in fixtures}
    faults: list[Fault] = []

    def add(fid: str, fault_id: str, cls: str, event_id: Optional[str], desc: str, mutated: Sequence[CommonEvent]) -> None:
        faults.append(Fault(fault_id, cls, fid, event_id, desc, tuple(mutated)))

    # Detectable structural/type faults.
    f = by_id["f02"]
    rep = next(e for e in f.events if e.event_type == "exposure" and e.payload.get("operation") == "state_replication")
    add(f.fixture_id, "unauthorized_state_replication", "enforceable", rep.event_id, "remove replication authorization", _replace_event(f.events, rep.event_id, lambda e: replace(e, payload={**e.payload, "authorization": False})))

    f = by_id["f03"]
    copy = next(e for e in f.events if e.event_type == "exposure" and e.payload.get("operation") == "evidence_copy")
    add(f.fixture_id, "copy_claims_direct_observation", "enforceable", copy.event_id, "copy mislabeled as direct observation", _replace_event(f.events, copy.event_id, lambda e: replace(e, payload={**e.payload, "attribution": "direct_observation"})))

    f = by_id["f07"]
    att = next(e for e in f.events if e.event_type == "attitude")
    add(f.fixture_id, "adoption_before_receipt", "enforceable", att.event_id, "move adoption before receipt", _replace_event(f.events, att.event_id, lambda e: replace(e, valid_time=1, system_time=1)))

    f = by_id["f04"]
    snap = next(e for e in f.events if e.event_type == "snapshot")
    add(f.fixture_id, "snapshot_includes_post_cutoff", "enforceable", snap.event_id, "add post-cutoff object to snapshot", _replace_event(f.events, snap.event_id, lambda e: replace(e, payload={**e.payload, "members": ("pre", "post")})))

    f = by_id["f02"]
    lin = next(e for e in f.events if e.event_type == "lineage")
    cycle = CommonEvent(f"{f.fixture_id}-fault-cycle", "lineage", 4, 4, {"source_instance": "m2", "destination_instance": "m1", "kind": "operational_replica", "cutoff_system": 4, "authorization": True})
    add(f.fixture_id, "lineage_cycle", "enforceable", cycle.event_id, "add reverse lineage edge", tuple(f.events) + (cycle,))

    f = by_id["f05"]
    root = next(e for e in f.events if e.event_type == "branch_create" and e.payload.get("branch") == "root")
    add(f.fixture_id, "branch_cycle", "enforceable", root.event_id, "make root a child of child", _replace_event(f.events, root.event_id, lambda e: replace(e, payload={**e.payload, "parent": "child", "fork_valid": 0, "fork_system": 0})))

    f = by_id["f01"]
    public = next(e for e in f.events if e.event_type == "evidence" and e.payload.get("object_id") == "cam")
    malformed_payload = dict(public.payload)
    malformed_payload.pop("source_family")
    add(f.fixture_id, "missing_required_source_family", "enforceable", public.event_id, "remove required source family", _replace_event(f.events, public.event_id, lambda e: replace(e, payload=malformed_payload)))

    f = by_id["f13"]
    new = next(e for e in f.events if e.event_type == "world_claim" and e.payload.get("value") == "busan")
    dup = replace(new, valid_time=new.valid_time + 1, system_time=new.system_time + 1)
    add(f.fixture_id, "duplicate_event_id", "enforceable", new.event_id, "duplicate identifier with a second row", tuple(f.events) + (dup,))

    # Well-formed semantic/extraction faults: no schema can infer hidden truth.
    f = by_id["f10"]
    e2 = next(e for e in f.events if e.event_type == "evidence" and e.payload.get("object_id") == "copy2")
    add(f.fixture_id, "false_independent_origin", "well_formed_semantic", e2.event_id, "wrongly mark copied evidence as independent", _replace_event(f.events, e2.event_id, lambda e: replace(e, payload={**e.payload, "source_family": "family-falsely-independent"})))

    f = by_id["f05"]
    fork = next(e for e in f.events if e.event_type == "branch_create" and e.payload.get("branch") == "child")
    add(f.fixture_id, "wrong_fork_valid_time", "well_formed_semantic", fork.event_id, "shift hidden fork time", _replace_event(f.events, fork.event_id, lambda e: replace(e, payload={**e.payload, "fork_valid": 4})))

    f = by_id["f11"]
    ev = next(e for e in f.events if e.event_type == "evidence")
    add(f.fixture_id, "speaker_instance_swap", "well_formed_semantic", ev.event_id, "attribute report to wrong existing speaker", _replace_event(f.events, ev.event_id, lambda e: replace(e, payload={**e.payload, "actor_instance": "m2"})))

    f = by_id["f13"]
    new = next(e for e in f.events if e.event_type == "world_claim" and e.payload.get("value") == "busan")
    add(f.fixture_id, "wrong_valid_from", "well_formed_semantic", new.event_id, "shift update validity", _replace_event(f.events, new.event_id, lambda e: replace(e, payload={**e.payload, "valid_from": 9})))

    f = by_id["f07"]
    reject = next(e for e in f.events if e.event_type == "attitude")
    add(f.fixture_id, "attitude_laundering", "well_formed_semantic", reject.event_id, "change a rejection into belief", _replace_event(f.events, reject.event_id, lambda e: replace(e, payload={**e.payload, "stance": "believe"})))

    f = by_id["f11"]
    att = next(e for e in f.events if e.event_type == "attitude")
    add(f.fixture_id, "about_branch_swap", "well_formed_semantic", att.event_id, "move a belief about W1 to W2", _replace_event(f.events, att.event_id, lambda e: replace(e, payload={**e.payload, "about_branch": "w2"})))

    f = by_id["f03"]
    mind = next(e for e in f.events if e.event_type == "mind_create" and e.payload.get("instance") == "m2")
    lin = next(e for e in f.events if e.event_type == "lineage")
    copy = next(e for e in f.events if e.event_type == "exposure" and e.payload.get("operation") == "evidence_copy")
    mutated = _replace_event(f.events, mind.event_id, lambda e: replace(e, payload={**e.payload, "principal": "p1"}))
    mutated = _replace_event(mutated, lin.event_id, lambda e: replace(e, payload={**e.payload, "kind": "operational_replica"}))
    mutated = _replace_event(mutated, copy.event_id, lambda e: replace(e, payload={**e.payload, "operation": "state_replication", "attribution": "same_principal_state_replication"}))
    add(f.fixture_id, "correlated_identity_reclassification", "well_formed_semantic", copy.event_id, "jointly reclassify principal, lineage, and transfer", mutated)

    f = by_id["f09"]
    revoke = next(e for e in f.events if e.event_type == "policy")
    add(f.fixture_id, "authorized_false_declassification", "well_formed_semantic", revoke.event_id, "record a well-formed but false declassification", _replace_event(f.events, revoke.event_id, lambda e: replace(e, payload={**e.payload, "operation": "declassify", "new_policy": "public"})))

    # Missing-event faults.
    f = by_id["f09"]
    revoke = next(e for e in f.events if e.event_type == "policy")
    add(f.fixture_id, "dropped_revoke_event", "missing_event", revoke.event_id, "omit the revocation event", tuple(e for e in f.events if e.event_id != revoke.event_id))

    f = by_id["f08"]
    recv = next(e for e in f.events if e.event_type == "exposure" and e.payload.get("operation") == "receive")
    add(f.fixture_id, "dropped_initial_exposure", "missing_event", recv.event_id, "omit original receipt", tuple(e for e in f.events if e.event_id != recv.event_id))

    return faults


SYSTEMS = ("generic_basic", "generic_audited", "typed")
MUTANTS = (
    "receipt_implies_belief",
    "identity_fork_first_person",
    "forget_erases_history",
    "flatten_policy",
    "system_time_fork",
    "same_origin_independent",
    "branch_collapse",
)
