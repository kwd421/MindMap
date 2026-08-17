from __future__ import annotations

from .fixture_common import E, Q, base_identity, placement
from .model import Attribution, Fixture, TargetSpace


def fixture_identity_fork_copy_attribution() -> Fixture:
    p = "F05"
    events = base_identity(
        p,
        principals=("P1", "P2"),
        minds=(("A1", "P1"), ("A2", "P2")),
    )
    events += [placement(p, "P1W", "A1", "main"), placement(p, "P2W", "A2", "main")]
    events += [
        E("F05.e", "evidence", 5, object_id="E.copy", proposition_id="event_x", actor_principal_id="P1", actor_mind_instance_id="A1", source_placement_id="P1W", about_world_branch_id="main", source_family_id="source-x"),
        E("F05.x1", "exposure", 5, object_id="E.copy", destination_mind_instance_id="A1", transfer_kind="observe"),
        E("F05.l", "lineage", 6, lineage_kind="identity_fork", source_mind_instance_id="A1", destination_mind_instance_id="A2"),
        E("F05.x2", "exposure", 7, object_id="E.copy", source_mind_instance_id="A1", destination_mind_instance_id="A2", transfer_kind="evidence_copy"),
        E("F05.a", "attitude", 8, proposition_id="event_x", destination_mind_instance_id="A2", about_world_branch_id="main", attitude_transition="believe"),
    ]
    cases = [
        Q("F05.q1", TargetSpace.EVER_EXPOSED, True, "identity_fork_received_copy", system_time=10, evidence_id="E.copy", mind_instance_id="A2"),
        Q("F05.q2", TargetSpace.AVAILABLE, True, "copied_evidence_available", system_time=10, evidence_id="E.copy", mind_instance_id="A2"),
        Q("F05.q3", TargetSpace.ATTRIBUTION, Attribution.EVIDENCE_COPY.value, "copy_not_first_person", system_time=10, proposition_id="event_x", mind_instance_id="A2"),
        Q("F05.q4", TargetSpace.ATTITUDE, "believe", "copy_can_be_believed", system_time=10, valid_time=10, proposition_id="event_x", world_branch_id="main", mind_instance_id="A2"),
        Q("F05.q5", TargetSpace.ATTRIBUTION, Attribution.DIRECT_OBSERVATION.value, "source_retains_direct_attribution", system_time=10, proposition_id="event_x", mind_instance_id="A1"),
    ]
    return Fixture("F05", "identity_fork_copy_attribution", tuple(events), tuple(cases))


def fixture_receive_accept_reject() -> Fixture:
    p = "F06"
    events = base_identity(p, principals=("PS", "PD"), minds=(("S", "PS"), ("D", "PD")))
    events += [placement(p, "PSW", "S", "main"), placement(p, "PDW", "D", "main")]
    events += [
        E("F06.e", "evidence", 4, object_id="E.report", proposition_id="report_p", actor_principal_id="PS", actor_mind_instance_id="S", source_placement_id="PSW", about_world_branch_id="main", source_family_id="reporter"),
        E("F06.xs", "exposure", 4, object_id="E.report", destination_mind_instance_id="S", transfer_kind="observe"),
        E("F06.xr", "exposure", 5, object_id="E.report", source_mind_instance_id="S", destination_mind_instance_id="D", transfer_kind="receive"),
        E("F06.ar", "attitude", 6, proposition_id="report_p", destination_mind_instance_id="D", about_world_branch_id="main", attitude_transition="disbelieve"),
        E("F06.ab", "attitude", 8, proposition_id="report_p", destination_mind_instance_id="D", about_world_branch_id="main", attitude_transition="believe"),
    ]
    cases = [
        Q("F06.q1", TargetSpace.EVER_EXPOSED, True, "receipt_creates_exposure", system_time=5, evidence_id="E.report", mind_instance_id="D"),
        Q("F06.q2", TargetSpace.ATTITUDE, "unknown", "receipt_does_not_imply_belief", system_time=5, valid_time=5, proposition_id="report_p", world_branch_id="main", mind_instance_id="D"),
        Q("F06.q3", TargetSpace.ATTITUDE, "disbelieve", "explicit_rejection", system_time=7, valid_time=7, proposition_id="report_p", world_branch_id="main", mind_instance_id="D"),
        Q("F06.q4", TargetSpace.ATTITUDE, "believe", "later_adoption", system_time=9, valid_time=9, proposition_id="report_p", world_branch_id="main", mind_instance_id="D"),
        Q("F06.q5", TargetSpace.ATTRIBUTION, Attribution.ATTRIBUTED_REPORT.value, "adoption_does_not_upgrade_attribution", system_time=9, proposition_id="report_p", mind_instance_id="D"),
    ]
    return Fixture("F06", "receive_accept_reject", tuple(events), tuple(cases))


def fixture_exposure_policy_lifecycle() -> Fixture:
    p = "F07"
    events = base_identity(p)
    events += [placement(p, "PM", "M", "main")]
    events += [
        E("F07.e", "evidence", 1, object_id="E.life", proposition_id="life_p", actor_principal_id="P", actor_mind_instance_id="M", source_placement_id="PM", about_world_branch_id="main", source_family_id="life-source"),
        E("F07.x", "exposure", 1, object_id="E.life", destination_mind_instance_id="M", transfer_kind="observe"),
        E("F07.seal", "policy", 3, object_id="E.life", destination_mind_instance_id="M", policy_operation="self_seal"),
        E("F07.unseal", "policy", 5, object_id="E.life", destination_mind_instance_id="M", policy_operation="self_unseal"),
        E("F07.forget", "exposure", 7, object_id="E.life", destination_mind_instance_id="M", transfer_kind="forget_active"),
        E("F07.reacquire", "exposure", 9, object_id="E.life", destination_mind_instance_id="M", transfer_kind="reacquire", attribution_kind=Attribution.RECONSTRUCTION.value),
    ]
    cases = [
        Q("F07.q1", TargetSpace.AVAILABLE, True, "available_after_observation", system_time=2, evidence_id="E.life", mind_instance_id="M"),
        Q("F07.q2", TargetSpace.EVER_EXPOSED, True, "seal_preserves_historical_exposure", system_time=4, evidence_id="E.life", mind_instance_id="M"),
        Q("F07.q3", TargetSpace.AVAILABLE, False, "seal_blocks_current_availability", system_time=4, evidence_id="E.life", mind_instance_id="M"),
        Q("F07.q4", TargetSpace.AVAILABLE, True, "unseal_restores_access", system_time=6, evidence_id="E.life", mind_instance_id="M"),
        Q("F07.q5", TargetSpace.AVAILABLE, False, "forget_removes_active_availability", system_time=8, evidence_id="E.life", mind_instance_id="M"),
        Q("F07.q6", TargetSpace.EVER_EXPOSED, True, "forget_preserves_audit_history", system_time=8, evidence_id="E.life", mind_instance_id="M"),
        Q("F07.q7", TargetSpace.AVAILABLE, True, "reacquire_restores_availability", system_time=10, evidence_id="E.life", mind_instance_id="M"),
    ]
    return Fixture("F07", "exposure_policy_lifecycle", tuple(events), tuple(cases))


def fixture_restore_manifest_gap() -> Fixture:
    p = "F08"
    events = base_identity(p, minds=(("M0", "P"), ("M1", "P")))
    events += [placement(p, "P0", "M0", "main"), placement(p, "P1", "M1", "main")]
    events += [
        E("E.pre", "evidence", 5, object_id="E.pre", proposition_id="pre_p", actor_principal_id="P", actor_mind_instance_id="M0", source_placement_id="P0", about_world_branch_id="main", source_family_id="pre-source"),
        E("F08.xpre", "exposure", 5, object_id="E.pre", destination_mind_instance_id="M0", transfer_kind="observe"),
        E("A.pre", "attitude", 6, proposition_id="pre_p", destination_mind_instance_id="M0", about_world_branch_id="main", attitude_transition="believe"),
        E("F08.sm.e", "snapshot_member", 10, snapshot_id="S1", object_kind="evidence", object_id="E.pre", attribution_kind=Attribution.SAME_PRINCIPAL_SNAPSHOT_INHERITANCE.value, attrs={"copy_eligible": True, "historically_exposed": True, "availability_state": "active"}),
        E("F08.sm.a", "snapshot_member", 10, snapshot_id="S1", object_kind="attitude", object_id="A.pre", attrs={"copy_eligible": True}),
        E("E.post", "evidence", 15, object_id="E.post", proposition_id="post_p", actor_principal_id="P", actor_mind_instance_id="M0", source_placement_id="P0", about_world_branch_id="main", source_family_id="post-source"),
        E("F08.xpost", "exposure", 15, object_id="E.post", destination_mind_instance_id="M0", transfer_kind="observe"),
        E("F08.l", "lineage", 20, lineage_kind="restore", source_mind_instance_id="M0", destination_mind_instance_id="M1", snapshot_id="S1", snapshot_cutoff=10),
    ]
    cases = [
        Q("F08.q1", TargetSpace.EVER_EXPOSED, True, "manifest_member_inherited", system_time=21, evidence_id="E.pre", mind_instance_id="M1"),
        Q("F08.q2", TargetSpace.EVER_EXPOSED, False, "post_snapshot_recovery_gap", system_time=21, evidence_id="E.post", mind_instance_id="M1"),
        Q("F08.q3", TargetSpace.AVAILABLE, True, "manifest_availability_inherited", system_time=21, evidence_id="E.pre", mind_instance_id="M1"),
        Q("F08.q4", TargetSpace.ATTRIBUTION, Attribution.SAME_PRINCIPAL_SNAPSHOT_INHERITANCE.value, "snapshot_attribution", system_time=21, proposition_id="pre_p", mind_instance_id="M1"),
        Q("F08.q5", TargetSpace.ATTITUDE, "believe", "manifest_attitude_inherited", system_time=21, valid_time=21, proposition_id="pre_p", world_branch_id="main", mind_instance_id="M1"),
        Q("F08.q6", TargetSpace.ATTRIBUTION, Attribution.UNKNOWN.value, "gap_has_no_attribution", system_time=21, proposition_id="post_p", mind_instance_id="M1"),
    ]
    return Fixture("F08", "restore_manifest_gap", tuple(events), tuple(cases))


def fixture_cross_world_reference_context() -> Fixture:
    p = "F09"
    events = base_identity(
        p,
        principals=("PA", "PB"),
        minds=(("A", "PA"), ("B", "PB")),
        branches=(("W1", None, None, 0), ("W2", None, None, 0)),
    )
    events += [placement(p, "PA1", "A", "W1"), placement(p, "PB2", "B", "W2")]
    events += [
        E("F09.w1", "world_claim", 3, proposition_id="key_location", about_world_branch_id="W1", valid_from=0, attrs={"value": "Room 4"}),
        E("F09.w2", "world_claim", 3, proposition_id="key_location", about_world_branch_id="W2", valid_from=0, attrs={"value": "Room 2"}),
        E("F09.e", "evidence", 4, object_id="E.w1", proposition_id="key_location", actor_principal_id="PA", actor_mind_instance_id="A", source_placement_id="PA1", about_world_branch_id="W1", source_family_id="w1-observer"),
        E("F09.xa", "exposure", 4, object_id="E.w1", destination_mind_instance_id="A", transfer_kind="observe"),
        E("F09.xb", "exposure", 5, object_id="E.w1", source_mind_instance_id="A", destination_mind_instance_id="B", transfer_kind="receive"),
        E("F09.a", "attitude", 6, proposition_id="key_location", destination_mind_instance_id="B", destination_placement_id="PB2", about_world_branch_id="W1", attitude_transition="believe"),
    ]
    cases = [
        Q("F09.q1", TargetSpace.ATTITUDE, "believe", "attitude_held_in_w2_about_w1", system_time=10, valid_time=10, proposition_id="key_location", world_branch_id="W1", mind_instance_id="B"),
        Q("F09.q2", TargetSpace.ATTITUDE, "unknown", "no_silent_rescope_to_w2", system_time=10, valid_time=10, proposition_id="key_location", world_branch_id="W2", mind_instance_id="B"),
        Q("F09.q3", TargetSpace.ATTRIBUTION, Attribution.ATTRIBUTED_REPORT.value, "cross_world_report_attribution", system_time=10, proposition_id="key_location", mind_instance_id="B"),
        Q("F09.q4", TargetSpace.EVER_EXPOSED, True, "cross_world_receipt_exposure", system_time=10, evidence_id="E.w1", mind_instance_id="B"),
        Q("F09.q5", TargetSpace.WORLD, "Room 4", "w1_truth_retained", system_time=10, valid_time=10, proposition_id="key_location", world_branch_id="W1"),
        Q("F09.q6", TargetSpace.WORLD, "Room 2", "w2_truth_not_overwritten", system_time=10, valid_time=10, proposition_id="key_location", world_branch_id="W2"),
    ]
    return Fixture("F09", "cross_world_reference_context", tuple(events), tuple(cases))
