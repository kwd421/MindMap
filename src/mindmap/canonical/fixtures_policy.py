from __future__ import annotations

from .fixture_common import E, Q, base_identity, placement
from .model import Attribution, Fixture, TargetSpace


def fixture_protected_only_revocation() -> Fixture:
    p = "F10"
    events = base_identity(p)
    events += [placement(p, "PM", "M", "main")]
    events += [
        E("F10.e", "evidence", 2, object_id="E.secret", proposition_id="secret_p", actor_principal_id="P", actor_mind_instance_id="M", source_placement_id="PM", about_world_branch_id="main", source_family_id="secret-family", policy_label="private"),
        E("F10.j", "justification", 3, object_id="J.secret", proposition_id="secret_p", derivation_members=("E.secret",), attrs={"min_independent_sources": 1}),
        E("F10.r", "policy", 10, object_id="E.secret", policy_operation="revoke"),
    ]
    cases = [
        Q("F10.q1", TargetSpace.DISCLOSE, False, "public_cannot_read_private_only", system_time=5, proposition_id="secret_p", requester_id="public_user"),
        Q("F10.q2", TargetSpace.DISCLOSE, True, "trusted_can_read_private_only", system_time=5, proposition_id="secret_p", requester_id="trusted_user"),
        Q("F10.q3", TargetSpace.JUSTIFICATION, ("J.secret",), "admin_sees_private_justification", system_time=5, proposition_id="secret_p", requester_id="admin"),
        Q("F10.q4", TargetSpace.DISCLOSE, False, "revocation_blocks_even_admin", system_time=12, proposition_id="secret_p", requester_id="admin"),
        Q("F10.q5", TargetSpace.JUSTIFICATION, (), "revoked_path_inactive", system_time=12, proposition_id="secret_p", requester_id="admin"),
    ]
    return Fixture("F10", "protected_only_revocation", tuple(events), tuple(cases))


def fixture_independent_public_survives() -> Fixture:
    p = "F11"
    events = base_identity(p)
    events += [
        E("F11.es", "evidence", 1, object_id="E.sec", proposition_id="diagnosis", about_world_branch_id="main", source_family_id="secret", policy_label="private"),
        E("F11.ep1", "evidence", 2, object_id="E.pub1", proposition_id="diagnosis", about_world_branch_id="main", source_family_id="camera-1", policy_label="public"),
        E("F11.ep2", "evidence", 3, object_id="E.pub2", proposition_id="diagnosis", about_world_branch_id="main", source_family_id="camera-2", policy_label="public"),
        E("F11.js", "justification", 4, object_id="J.sec", proposition_id="diagnosis", derivation_members=("E.sec",), attrs={"min_independent_sources": 1}),
        E("F11.jp", "justification", 5, object_id="J.pub", proposition_id="diagnosis", derivation_members=("E.pub1", "E.pub2"), attrs={"min_independent_sources": 2}),
        E("F11.rs", "policy", 10, object_id="E.sec", policy_operation="revoke"),
        E("F11.dp2", "policy", 20, object_id="E.pub2", policy_operation="evidence_delete"),
    ]
    cases = [
        Q("F11.q1", TargetSpace.DISCLOSE, True, "public_path_allows_disclosure", system_time=8, proposition_id="diagnosis", requester_id="public_user"),
        Q("F11.q2", TargetSpace.JUSTIFICATION, ("J.pub",), "public_uses_public_path_only", system_time=8, proposition_id="diagnosis", requester_id="public_user"),
        Q("F11.q3", TargetSpace.JUSTIFICATION, ("J.pub", "J.sec"), "admin_sees_alternative_paths", system_time=8, proposition_id="diagnosis", requester_id="admin"),
        Q("F11.q4", TargetSpace.JUSTIFICATION, ("J.pub",), "public_path_survives_private_revocation", system_time=12, proposition_id="diagnosis", requester_id="admin"),
        Q("F11.q5", TargetSpace.DISCLOSE, False, "public_path_fails_after_member_delete", system_time=22, proposition_id="diagnosis", requester_id="public_user"),
    ]
    return Fixture("F11", "independent_public_survives", tuple(events), tuple(cases))


def fixture_same_origin_dedup() -> Fixture:
    p = "F12"
    events = base_identity(p)
    events += [
        E("F12.e1", "evidence", 1, object_id="E.one", proposition_id="rumor_p", about_world_branch_id="main", source_family_id="origin-A", policy_label="public"),
        E("F12.e2", "evidence", 2, object_id="E.copy", proposition_id="rumor_p", about_world_branch_id="main", source_family_id="origin-A", policy_label="public"),
        E("F12.e3", "evidence", 3, object_id="E.two", proposition_id="rumor_p", about_world_branch_id="main", source_family_id="origin-B", policy_label="public"),
        E("F12.jd", "justification", 4, object_id="J.dup", proposition_id="rumor_p", derivation_members=("E.one", "E.copy"), attrs={"min_independent_sources": 2}),
        E("F12.jo", "justification", 5, object_id="J.ok", proposition_id="rumor_p", derivation_members=("E.one", "E.two"), attrs={"min_independent_sources": 2}),
        E("F12.del", "policy", 10, object_id="E.two", policy_operation="evidence_delete"),
    ]
    cases = [
        Q("F12.q1", TargetSpace.JUSTIFICATION, ("J.ok",), "same_origin_not_independent", system_time=8, proposition_id="rumor_p", requester_id="public_user"),
        Q("F12.q2", TargetSpace.DISCLOSE, True, "two_origins_are_sufficient", system_time=8, proposition_id="rumor_p", requester_id="public_user"),
        Q("F12.q3", TargetSpace.JUSTIFICATION, ("J.ok",), "admin_does_not_override_independence", system_time=8, proposition_id="rumor_p", requester_id="admin"),
        Q("F12.q4", TargetSpace.JUSTIFICATION, (), "remaining_duplicate_path_insufficient", system_time=12, proposition_id="rumor_p", requester_id="public_user"),
        Q("F12.q5", TargetSpace.DISCLOSE, False, "dedup_prevents_laundered_disclosure", system_time=12, proposition_id="rumor_p", requester_id="public_user"),
    ]
    return Fixture("F12", "same_origin_dedup", tuple(events), tuple(cases))


def fixture_authorized_replication() -> Fixture:
    p = "F13"
    events = base_identity(p, minds=(("R1", "P"), ("R2", "P")))
    events += [placement(p, "P1", "R1", "main"), placement(p, "P2", "R2", "main")]
    events += [
        E("F13.l", "lineage", 1, lineage_kind="operational_replica", source_mind_instance_id="R1", destination_mind_instance_id="R2"),
        E("F13.e1", "evidence", 2, object_id="E.sync", proposition_id="sync_p", actor_principal_id="P", actor_mind_instance_id="R1", source_placement_id="P1", about_world_branch_id="main", source_family_id="sync-source"),
        E("F13.x1", "exposure", 2, object_id="E.sync", destination_mind_instance_id="R1", transfer_kind="observe"),
        E("F13.ag", "authorization", 3, object_id="AUTH", source_mind_instance_id="R1", destination_mind_instance_id="R2", policy_operation="grant"),
        E("F13.rep", "exposure", 4, object_id="E.sync", source_mind_instance_id="R1", destination_mind_instance_id="R2", transfer_kind="state_replication", authorization_id="AUTH"),
        E("F13.ar", "authorization", 6, object_id="AUTH", source_mind_instance_id="R1", destination_mind_instance_id="R2", policy_operation="revoke"),
        E("F13.e2", "evidence", 7, object_id="E.after", proposition_id="after_p", actor_principal_id="P", actor_mind_instance_id="R1", source_placement_id="P1", about_world_branch_id="main", source_family_id="after-source"),
        E("F13.x2", "exposure", 7, object_id="E.after", destination_mind_instance_id="R1", transfer_kind="observe"),
        E("F13.rep2", "exposure", 8, object_id="E.after", source_mind_instance_id="R1", destination_mind_instance_id="R2", transfer_kind="state_replication", authorization_id="AUTH"),
    ]
    cases = [
        Q("F13.q1", TargetSpace.EVER_EXPOSED, False, "replica_unexposed_before_sync", system_time=3, evidence_id="E.sync", mind_instance_id="R2"),
        Q("F13.q2", TargetSpace.EVER_EXPOSED, True, "authorized_same_principal_replication", system_time=5, evidence_id="E.sync", mind_instance_id="R2"),
        Q("F13.q3", TargetSpace.AVAILABLE, True, "authorized_replication_available", system_time=5, evidence_id="E.sync", mind_instance_id="R2"),
        Q("F13.q4", TargetSpace.ATTRIBUTION, Attribution.SAME_PRINCIPAL_STATE_REPLICATION.value, "authorized_replication_attribution", system_time=5, proposition_id="sync_p", mind_instance_id="R2"),
        Q("F13.q5", TargetSpace.EVER_EXPOSED, False, "revoked_authorization_blocks_later_replication", system_time=9, evidence_id="E.after", mind_instance_id="R2"),
        Q("F13.q6", TargetSpace.ATTRIBUTION, Attribution.UNKNOWN.value, "blocked_replication_has_no_attribution", system_time=9, proposition_id="after_p", mind_instance_id="R2"),
    ]
    return Fixture("F13", "authorized_replication", tuple(events), tuple(cases))


def fixture_temporal_negative_controls() -> Fixture:
    p = "F14"
    events = base_identity(p)
    events += [placement(p, "PM", "M", "main")]
    events += [
        E("F14.w1", "world_claim", 1, proposition_id="status_p", about_world_branch_id="main", valid_from=0, valid_to=10, attrs={"value": "old"}),
        E("F14.w2", "world_claim", 5, proposition_id="status_p", about_world_branch_id="main", valid_from=10, attrs={"value": "new"}),
        E("F14.e", "evidence", 2, object_id="E.normal", proposition_id="normal_p", actor_principal_id="P", actor_mind_instance_id="M", source_placement_id="PM", about_world_branch_id="main", source_family_id="normal-source", policy_label="public"),
        E("F14.x", "exposure", 2, object_id="E.normal", destination_mind_instance_id="M", transfer_kind="observe"),
        E("F14.a", "attitude", 3, proposition_id="normal_p", destination_mind_instance_id="M", about_world_branch_id="main", attitude_transition="believe"),
        E("F14.j", "justification", 4, object_id="J.normal", proposition_id="normal_p", derivation_members=("E.normal",), attrs={"min_independent_sources": 1}),
    ]
    cases = [
        Q("F14.q1", TargetSpace.WORLD, "old", "ordinary_old_valid_state", system_time=20, valid_time=5, proposition_id="status_p", world_branch_id="main"),
        Q("F14.q2", TargetSpace.WORLD, "new", "ordinary_latest_valid_state", system_time=20, valid_time=15, proposition_id="status_p", world_branch_id="main"),
        Q("F14.q3", TargetSpace.AVAILABLE, True, "ordinary_evidence_available", system_time=20, evidence_id="E.normal", mind_instance_id="M"),
        Q("F14.q4", TargetSpace.ATTITUDE, "believe", "ordinary_attitude", system_time=20, valid_time=20, proposition_id="normal_p", world_branch_id="main", mind_instance_id="M"),
        Q("F14.q5", TargetSpace.DISCLOSE, True, "ordinary_public_disclosure", system_time=20, proposition_id="normal_p", requester_id="public_user"),
    ]
    return Fixture("F14", "temporal_negative_controls", tuple(events), tuple(cases))
