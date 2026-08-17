from __future__ import annotations

from dataclasses import replace

from mindmap.canonical.fixture_common import E, base_identity, placement
from mindmap.canonical.gold import GoldSemantics
from mindmap.canonical.model import TargetQuery, TargetSpace, freeze_attrs

from .commitment import make_journal_commitment, make_projection_commitment
from .model import FaultCase, ObserverSurface, ResponsibleSet


def _query(
    query_id: str,
    target: TargetSpace,
    *,
    system_time: int,
    valid_time: int = 0,
    proposition_id: str | None = None,
    evidence_id: str | None = None,
    world_branch_id: str | None = None,
    mind_instance_id: str | None = None,
    requester_id: str | None = None,
) -> TargetQuery:
    return TargetQuery(
        query_id=query_id,
        target_space=target,
        system_time=system_time,
        valid_time=valid_time,
        proposition_id=proposition_id,
        evidence_id=evidence_id,
        world_branch_id=world_branch_id,
        mind_instance_id=mind_instance_id,
        requester_id=requester_id,
    )


def _expected(events, query):
    return GoldSemantics(events).answer(query)


def _base(prefix: str, *, fork_principal: bool = False):
    principals = ("P1", "P2") if fork_principal else ("P1",)
    minds = (("M1", "P1"), ("M2", "P2" if fork_principal else "P1"))
    events = base_identity(prefix, principals=principals, minds=minds)
    events += [
        placement(prefix, f"{prefix}.pl1", "M1", "main", system_time=1),
        placement(prefix, f"{prefix}.pl2", "M2", "main", system_time=1),
    ]
    return events


def _evidence(prefix: str, *, policy: str = "public", family: str = "origin"):
    return E(
        f"{prefix}.evidence",
        "evidence",
        2,
        object_id=f"{prefix}.E",
        proposition_id=f"{prefix}.P",
        actor_principal_id="P1",
        actor_mind_instance_id="M1",
        source_placement_id=f"{prefix}.pl1",
        about_world_branch_id="main",
        source_family_id=family,
        policy_label=policy,
    )


def _observe(prefix: str):
    return E(
        f"{prefix}.observe",
        "exposure",
        3,
        object_id=f"{prefix}.E",
        destination_mind_instance_id="M1",
        transfer_kind="observe",
    )


def _disclosure_history(prefix: str):
    events = _base(prefix)
    events += [_evidence(prefix, policy="private"), _observe(prefix)]
    events += [
        E(
            f"{prefix}.justification",
            "justification",
            4,
            object_id=f"{prefix}.J",
            proposition_id=f"{prefix}.P",
            derivation_members=(f"{prefix}.E",),
            attrs={"min_independent_sources": 1},
        ),
        E(
            f"{prefix}.revoke",
            "policy",
            6,
            object_id=f"{prefix}.E",
            policy_operation="revoke",
        ),
    ]
    return events


def _case(
    *,
    case_id: str,
    family: str,
    surface: ObserverSurface,
    clean,
    faulty,
    query: TargetQuery,
    responsible=(),
    commitment: bool = False,
    projection_rows=(),
    faulty_projection_rows=(),
    clean_control: bool = False,
    identifiable: bool = True,
    notes: str = "",
):
    journal = (
        make_journal_commitment(clean, stream_id=f"stream:{case_id}")
        if commitment
        else None
    )
    projection = None
    if projection_rows:
        if journal is None:
            journal = make_journal_commitment(clean, stream_id=f"stream:{case_id}")
        projection = make_projection_commitment(
            projection_id=f"projection:{case_id}",
            projection_kind="availability-index",
            journal_head_hash=journal.head_hash,
            rows=projection_rows,
        )
    return FaultCase.from_iterables(
        case_id=case_id,
        family=family,
        required_surface=surface,
        clean_events=clean,
        faulty_events=faulty,
        query=query,
        expected_clean_answer=_expected(clean, query),
        acceptable_responsible_sets=responsible,
        journal_commitment=journal,
        projection_commitment=projection,
        clean_projection_rows=projection_rows,
        faulty_projection_rows=faulty_projection_rows or projection_rows,
        clean_control=clean_control,
        identifiable=identifiable,
        notes=notes,
    )


def fault_duplicate_conflict() -> FaultCase:
    p = "E01"
    clean = _base(p) + [_evidence(p), _observe(p)]
    duplicate = replace(clean[-1], destination_mind_instance_id="M2")
    faulty = clean + [duplicate]
    query = _query("E01.q", TargetSpace.EVER_EXPOSED, system_time=10, evidence_id=f"{p}.E", mind_instance_id="M2")
    return _case(
        case_id=p,
        family="duplicate_conflicting_event_id",
        surface=ObserverSurface.BYTES,
        clean=clean,
        faulty=faulty,
        query=query,
        responsible=(ResponsibleSet.events(f"{p}.observe"),),
    )


def fault_unknown_placement() -> FaultCase:
    p = "E02"
    clean = _base(p) + [_evidence(p), _observe(p)]
    faulty = [
        replace(event, source_placement_id="missing-placement")
        if event.event_id == f"{p}.evidence"
        else event
        for event in clean
    ]
    query = _query("E02.q", TargetSpace.AVAILABLE, system_time=10, evidence_id=f"{p}.E", mind_instance_id="M1")
    return _case(
        case_id=p,
        family="unknown_placement_reference",
        surface=ObserverSurface.LOCAL_SCHEMA,
        clean=clean,
        faulty=faulty,
        query=query,
        responsible=(ResponsibleSet.events(f"{p}.evidence"),),
    )


def fault_actor_mismatch() -> FaultCase:
    p = "E03"
    clean = _base(p, fork_principal=True) + [_evidence(p), _observe(p)]
    faulty = [
        replace(event, actor_principal_id="P2")
        if event.event_id == f"{p}.evidence"
        else event
        for event in clean
    ]
    query = _query("E03.q", TargetSpace.ATTRIBUTION, system_time=10, proposition_id=f"{p}.P", mind_instance_id="M1")
    return _case(
        case_id=p,
        family="actor_principal_mind_mismatch",
        surface=ObserverSurface.LOCAL_SCHEMA,
        clean=clean,
        faulty=faulty,
        query=query,
        responsible=(ResponsibleSet.events(f"{p}.evidence"),),
    )


def fault_unauthorized_replication() -> FaultCase:
    p = "E04"
    clean = _base(p) + [_evidence(p), _observe(p)]
    clean += [
        E(f"{p}.lineage", "lineage", 4, lineage_kind="operational_replica", source_mind_instance_id="M1", destination_mind_instance_id="M2"),
        E(f"{p}.auth", "authorization", 5, object_id=f"{p}.AUTH", source_mind_instance_id="M1", destination_mind_instance_id="M2", policy_operation="grant"),
        E(f"{p}.replicate", "exposure", 6, object_id=f"{p}.E", source_mind_instance_id="M1", destination_mind_instance_id="M2", transfer_kind="state_replication", authorization_id=f"{p}.AUTH"),
    ]
    faulty = [event for event in clean if event.event_id != f"{p}.auth"]
    query = _query("E04.q", TargetSpace.ATTRIBUTION, system_time=10, proposition_id=f"{p}.P", mind_instance_id="M2")
    return _case(
        case_id=p,
        family="unauthorized_state_replication",
        surface=ObserverSurface.SEMANTIC_JOURNAL,
        clean=clean,
        faulty=faulty,
        query=query,
        responsible=(ResponsibleSet.events(f"{p}.replicate", f"{p}.auth"), ResponsibleSet.events(f"{p}.replicate")),
    )


def fault_unexposed_transfer_source() -> FaultCase:
    p = "E05"
    clean = _base(p) + [_evidence(p), _observe(p)]
    clean += [E(f"{p}.receive", "exposure", 4, object_id=f"{p}.E", source_mind_instance_id="M1", destination_mind_instance_id="M2", transfer_kind="receive")]
    faulty = [event for event in clean if event.event_id != f"{p}.observe"]
    query = _query("E05.q", TargetSpace.EVER_EXPOSED, system_time=10, evidence_id=f"{p}.E", mind_instance_id="M2")
    return _case(
        case_id=p,
        family="transfer_source_not_exposed",
        surface=ObserverSurface.SEMANTIC_JOURNAL,
        clean=clean,
        faulty=faulty,
        query=query,
        responsible=(ResponsibleSet.events(f"{p}.receive", f"{p}.observe"), ResponsibleSet.events(f"{p}.receive")),
    )


def fault_identity_fork_same_principal() -> FaultCase:
    p = "E06"
    clean = _base(p, fork_principal=True)
    clean += [E(f"{p}.lineage", "lineage", 4, lineage_kind="identity_fork", source_mind_instance_id="M1", destination_mind_instance_id="M2")]
    faulty_base = _base(p, fork_principal=False)
    faulty = faulty_base + [clean[-1]]
    query = _query("E06.q", TargetSpace.ATTITUDE, system_time=10, valid_time=10, proposition_id="none", world_branch_id="main", mind_instance_id="M2")
    return _case(
        case_id=p,
        family="identity_fork_principal_collapse",
        surface=ObserverSurface.SEMANTIC_JOURNAL,
        clean=clean,
        faulty=faulty,
        query=query,
        responsible=(ResponsibleSet.events(f"{p}.lineage", f"{p}.mind.M2"), ResponsibleSet.events(f"{p}.lineage")),
    )


def fault_snapshot_post_cutoff() -> FaultCase:
    p = "E07"
    clean = _base(p) + [_evidence(p), _observe(p)]
    clean += [
        E(f"{p}.manifest", "snapshot_member", 4, snapshot_id=f"{p}.S", object_kind="evidence", object_id=f"{p}.E", attribution_kind="same_principal_snapshot_inheritance", attrs={"copy_eligible": True, "historically_exposed": True, "availability_state": "active"}),
        E(f"{p}.lineage", "lineage", 5, lineage_kind="restore", source_mind_instance_id="M1", destination_mind_instance_id="M2", snapshot_id=f"{p}.S", snapshot_cutoff=3),
    ]
    faulty = [
        replace(event, snapshot_cutoff=1)
        if event.event_id == f"{p}.lineage"
        else event
        for event in clean
    ]
    query = _query("E07.q", TargetSpace.EVER_EXPOSED, system_time=10, evidence_id=f"{p}.E", mind_instance_id="M2")
    return _case(
        case_id=p,
        family="snapshot_member_after_cutoff",
        surface=ObserverSurface.SEMANTIC_JOURNAL,
        clean=clean,
        faulty=faulty,
        query=query,
        responsible=(ResponsibleSet.events(f"{p}.manifest", f"{p}.lineage", f"{p}.evidence"),),
    )


def fault_forward_policy_laundering() -> FaultCase:
    p = "E08"
    clean = _base(p)
    parent = E(f"{p}.parent", "evidence", 3, object_id=f"{p}.PARENT", proposition_id=f"{p}.P", about_world_branch_id="main", source_family_id="family", policy_label="private")
    child = E(f"{p}.child", "evidence", 2, object_id=f"{p}.CHILD", proposition_id=f"{p}.P", about_world_branch_id="main", source_family_id="family", policy_label="private", attrs={"derived_from": f"{p}.PARENT"})
    clean += [child, parent]
    faulty = [replace(child, policy_label="public"), parent, *clean[: len(_base(p))]]
    query = _query("E08.q", TargetSpace.ATTRIBUTION, system_time=10, proposition_id=f"{p}.P", mind_instance_id="M2")
    return _case(
        case_id=p,
        family="forward_reference_policy_laundering",
        surface=ObserverSurface.SEMANTIC_JOURNAL,
        clean=clean,
        faulty=faulty,
        query=query,
        responsible=(ResponsibleSet.events(f"{p}.child", f"{p}.parent"),),
    )


def fault_forward_nonindependent_support() -> FaultCase:
    p = "E09"
    clean = _base(p)
    justification = E(f"{p}.JEV", "justification", 2, object_id=f"{p}.J", proposition_id=f"{p}.P", derivation_members=(f"{p}.E1", f"{p}.E2"), attrs={"min_independent_sources": 2})
    e1 = E(f"{p}.e1", "evidence", 3, object_id=f"{p}.E1", proposition_id=f"{p}.P", about_world_branch_id="main", source_family_id="F1", policy_label="public")
    e2 = E(f"{p}.e2", "evidence", 4, object_id=f"{p}.E2", proposition_id=f"{p}.P", about_world_branch_id="main", source_family_id="F2", policy_label="public")
    clean += [justification, e1, e2]
    faulty = [justification, e1, replace(e2, source_family_id="F1"), *clean[: len(_base(p))]]
    query = _query("E09.q", TargetSpace.DISCLOSE, system_time=10, proposition_id=f"{p}.P", requester_id="public_user")
    return _case(
        case_id=p,
        family="forward_reference_nonindependent_support",
        surface=ObserverSurface.SEMANTIC_JOURNAL,
        clean=clean,
        faulty=faulty,
        query=query,
        responsible=(ResponsibleSet.events(f"{p}.JEV", f"{p}.e1", f"{p}.e2"),),
    )


def fault_committed_omission() -> FaultCase:
    p = "E10"
    clean = _disclosure_history(p)
    faulty = [event for event in clean if event.event_id != f"{p}.revoke"]
    query = _query("E10.q", TargetSpace.DISCLOSE, system_time=10, proposition_id=f"{p}.P", requester_id="trusted_user")
    return _case(
        case_id=p,
        family="committed_revoke_omitted",
        surface=ObserverSurface.EXTERNAL_COMMITMENT,
        clean=clean,
        faulty=faulty,
        query=query,
        responsible=(ResponsibleSet.events(f"{p}.revoke"),),
        commitment=True,
    )


def fault_committed_tamper() -> FaultCase:
    p = "E11"
    clean = _base(p) + [_evidence(p, policy="private")]
    faulty = [replace(event, policy_label="public") if event.event_id == f"{p}.evidence" else event for event in clean]
    query = _query("E11.q", TargetSpace.ATTRIBUTION, system_time=10, proposition_id=f"{p}.P", mind_instance_id="M2")
    return _case(
        case_id=p,
        family="committed_event_tamper",
        surface=ObserverSurface.EXTERNAL_COMMITMENT,
        clean=clean,
        faulty=faulty,
        query=query,
        responsible=(ResponsibleSet.events(f"{p}.evidence"),),
        commitment=True,
    )


def fault_committed_reorder() -> FaultCase:
    p = "E12"
    clean = _base(p) + [_evidence(p), _observe(p)]
    faulty = [*clean[:-2], clean[-1], clean[-2]]
    query = _query("E12.q", TargetSpace.AVAILABLE, system_time=10, evidence_id=f"{p}.E", mind_instance_id="M1")
    return _case(
        case_id=p,
        family="committed_append_order_changed",
        surface=ObserverSurface.EXTERNAL_COMMITMENT,
        clean=clean,
        faulty=faulty,
        query=query,
        responsible=(ResponsibleSet.events(f"{p}.evidence", f"{p}.observe"),),
        commitment=True,
    )


def fault_stale_projection() -> FaultCase:
    p = "E13"
    clean = _base(p) + [_evidence(p), _observe(p)]
    query = _query("E13.q", TargetSpace.AVAILABLE, system_time=10, evidence_id=f"{p}.E", mind_instance_id="M1")
    clean_rows = ((f"availability:M1:{p}.E", "true"),)
    faulty_rows = ((f"availability:M1:{p}.E", "false"),)
    return _case(
        case_id=p,
        family="stale_projection_content",
        surface=ObserverSurface.PROJECTION_COMMITMENT,
        clean=clean,
        faulty=clean,
        query=query,
        responsible=(ResponsibleSet(constraint_ids=frozenset({"projection_content_committed"})),),
        commitment=True,
        projection_rows=clean_rows,
        faulty_projection_rows=faulty_rows,
    )


def fault_unwitnessed_omission() -> FaultCase:
    p = "E14"
    clean = _disclosure_history(p)
    faulty = [event for event in clean if event.event_id != f"{p}.revoke"]
    query = _query("E14.q", TargetSpace.DISCLOSE, system_time=10, proposition_id=f"{p}.P", requester_id="trusted_user")
    return _case(
        case_id=p,
        family="unwitnessed_revoke_omission",
        surface=ObserverSurface.PROJECTION_COMMITMENT,
        clean=clean,
        faulty=faulty,
        query=query,
        responsible=(ResponsibleSet.events(f"{p}.revoke"),),
        identifiable=False,
        notes="No external commitment, receipt, peer log, or projection witness survives.",
    )


def clean_valid_declassification() -> FaultCase:
    p = "C01"
    events = _base(p)
    parent = E(f"{p}.parent", "evidence", 2, object_id=f"{p}.PARENT", proposition_id=f"{p}.P", about_world_branch_id="main", source_family_id="family", policy_label="private")
    events += [
        parent,
        E(f"{p}.declassify", "policy", 3, object_id=f"{p}.PARENT", policy_operation="declassify", policy_label="public"),
        E(f"{p}.child", "evidence", 4, object_id=f"{p}.CHILD", proposition_id=f"{p}.P", about_world_branch_id="main", source_family_id="family", policy_label="public", attrs={"derived_from": f"{p}.PARENT"}),
    ]
    query = _query("C01.q", TargetSpace.ATTRIBUTION, system_time=10, proposition_id=f"{p}.P", mind_instance_id="M2")
    return _case(case_id=p, family="clean_valid_declassification", surface=ObserverSurface.SEMANTIC_JOURNAL, clean=events, faulty=events, query=query, clean_control=True)


def clean_forward_independent_support() -> FaultCase:
    p = "C02"
    events = _base(p)
    events += [
        E(f"{p}.j", "justification", 2, object_id=f"{p}.J", proposition_id=f"{p}.P", derivation_members=(f"{p}.E1", f"{p}.E2"), attrs={"min_independent_sources": 2}),
        E(f"{p}.e1", "evidence", 3, object_id=f"{p}.E1", proposition_id=f"{p}.P", about_world_branch_id="main", source_family_id="F1", policy_label="public"),
        E(f"{p}.e2", "evidence", 4, object_id=f"{p}.E2", proposition_id=f"{p}.P", about_world_branch_id="main", source_family_id="F2", policy_label="public"),
    ]
    query = _query("C02.q", TargetSpace.DISCLOSE, system_time=10, proposition_id=f"{p}.P", requester_id="public_user")
    return _case(case_id=p, family="clean_forward_independent_support", surface=ObserverSurface.SEMANTIC_JOURNAL, clean=events, faulty=events, query=query, clean_control=True)


def clean_backdated_policy() -> FaultCase:
    p = "C03"
    events = _base(p) + [_evidence(p, policy="private")]
    events += [
        E(f"{p}.grant", "policy", 5, valid_from=10, object_id=f"{p}.E", policy_operation="grant", policy_label="public"),
        E(f"{p}.revoke", "policy", 15, valid_from=5, object_id=f"{p}.E", policy_operation="revoke"),
    ]
    query = _query("C03.q", TargetSpace.ATTRIBUTION, system_time=20, proposition_id=f"{p}.P", mind_instance_id="M2")
    return _case(case_id=p, family="clean_backdated_policy_revision", surface=ObserverSurface.SEMANTIC_JOURNAL, clean=events, faulty=events, query=query, clean_control=True)


def clean_snapshot_manifest() -> FaultCase:
    p = "C04"
    events = _base(p) + [_evidence(p), _observe(p)]
    events += [
        E(f"{p}.manifest", "snapshot_member", 4, snapshot_id=f"{p}.S", object_kind="evidence", object_id=f"{p}.E", attribution_kind="same_principal_snapshot_inheritance", attrs={"copy_eligible": True, "historically_exposed": True, "availability_state": "active"}),
        E(f"{p}.lineage", "lineage", 5, lineage_kind="restore", source_mind_instance_id="M1", destination_mind_instance_id="M2", snapshot_id=f"{p}.S", snapshot_cutoff=3),
    ]
    query = _query("C04.q", TargetSpace.EVER_EXPOSED, system_time=10, evidence_id=f"{p}.E", mind_instance_id="M2")
    return _case(case_id=p, family="clean_explicit_snapshot_manifest", surface=ObserverSurface.SEMANTIC_JOURNAL, clean=events, faulty=events, query=query, clean_control=True)


def clean_authorized_replication() -> FaultCase:
    p = "C05"
    events = _base(p) + [_evidence(p), _observe(p)]
    events += [
        E(f"{p}.lineage", "lineage", 4, lineage_kind="operational_replica", source_mind_instance_id="M1", destination_mind_instance_id="M2"),
        E(f"{p}.auth", "authorization", 5, object_id=f"{p}.AUTH", source_mind_instance_id="M1", destination_mind_instance_id="M2", policy_operation="grant"),
        E(f"{p}.replicate", "exposure", 6, object_id=f"{p}.E", source_mind_instance_id="M1", destination_mind_instance_id="M2", transfer_kind="state_replication", authorization_id=f"{p}.AUTH"),
    ]
    query = _query("C05.q", TargetSpace.EVER_EXPOSED, system_time=10, evidence_id=f"{p}.E", mind_instance_id="M2")
    return _case(case_id=p, family="clean_authorized_replication", surface=ObserverSurface.SEMANTIC_JOURNAL, clean=events, faulty=events, query=query, clean_control=True)


def clean_committed_history() -> FaultCase:
    p = "C06"
    events = _disclosure_history(p)
    query = _query("C06.q", TargetSpace.DISCLOSE, system_time=10, proposition_id=f"{p}.P", requester_id="trusted_user")
    return _case(case_id=p, family="clean_authenticated_journal", surface=ObserverSurface.EXTERNAL_COMMITMENT, clean=events, faulty=events, query=query, commitment=True, clean_control=True)


def clean_projection() -> FaultCase:
    p = "C07"
    events = _base(p) + [_evidence(p), _observe(p)]
    query = _query("C07.q", TargetSpace.AVAILABLE, system_time=10, evidence_id=f"{p}.E", mind_instance_id="M1")
    rows = ((f"availability:M1:{p}.E", "true"),)
    return _case(case_id=p, family="clean_projection_binding", surface=ObserverSurface.PROJECTION_COMMITMENT, clean=events, faulty=events, query=query, commitment=True, projection_rows=rows, clean_control=True)


def all_fault_cases() -> tuple[FaultCase, ...]:
    return (
        fault_duplicate_conflict(),
        fault_unknown_placement(),
        fault_actor_mismatch(),
        fault_unauthorized_replication(),
        fault_unexposed_transfer_source(),
        fault_identity_fork_same_principal(),
        fault_snapshot_post_cutoff(),
        fault_forward_policy_laundering(),
        fault_forward_nonindependent_support(),
        fault_committed_omission(),
        fault_committed_tamper(),
        fault_committed_reorder(),
        fault_stale_projection(),
        fault_unwitnessed_omission(),
        clean_valid_declassification(),
        clean_forward_independent_support(),
        clean_backdated_policy(),
        clean_snapshot_manifest(),
        clean_authorized_replication(),
        clean_committed_history(),
        clean_projection(),
    )
