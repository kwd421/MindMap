from __future__ import annotations

from .v02_model import CommonEvent, EventType, Fixture, Query, QueryTarget


def build_semantic_conformance_fixture() -> Fixture:
    E = CommonEvent
    events: list[CommonEvent] = [
        E("m0", EventType.MIND_CREATED, 1, actor_principal_id="pA", destination_mind_instance_id="m0"),
        E("place-m0", EventType.PLACEMENT, 2, destination_mind_instance_id="m0", placement_id="pl-m0-w0", world_branch_id="W0"),
        E("m-rep", EventType.MIND_CREATED, 3, actor_principal_id="pA", destination_mind_instance_id="m_rep"),
        E("place-rep", EventType.PLACEMENT, 4, destination_mind_instance_id="m_rep", placement_id="pl-rep-w0", world_branch_id="W0"),
        E("m-fork", EventType.MIND_CREATED, 5, actor_principal_id="pA2", destination_mind_instance_id="m_fork"),
        E("place-fork", EventType.PLACEMENT, 6, destination_mind_instance_id="m_fork", placement_id="pl-fork-w0", world_branch_id="W0"),
        E("m-restore", EventType.MIND_CREATED, 7, actor_principal_id="pA", destination_mind_instance_id="m_restore"),
        E("place-restore", EventType.PLACEMENT, 8, destination_mind_instance_id="m_restore", placement_id="pl-restore-w0", world_branch_id="W0"),
        E("m-b", EventType.MIND_CREATED, 9, actor_principal_id="pB", destination_mind_instance_id="m_b"),
        E("place-b", EventType.PLACEMENT, 10, destination_mind_instance_id="m_b", placement_id="pl-b-w2", world_branch_id="W2"),

        E("wf-root", EventType.WORLD_FACT, 11, valid_from=1, proposition_id="root_seen", world_branch_id="W0", truth_value=True),
        E("ev-root", EventType.EVIDENCE, 12, object_id="e_root", proposition_id="root_seen", about_world_branch_id="W0", policy_label="private:pA", source_family_id="fam-root"),
        E("x-root", EventType.EXPOSURE, 13, destination_mind_instance_id="m0", object_id="e_root", operation="observe"),
        E("lin-fork", EventType.LINEAGE, 14, source_mind_instance_id="m0", destination_mind_instance_id="m_fork", lineage_kind="identity_fork", snapshot_cutoff=13),
        E("copy-fork", EventType.EXPOSURE, 15, source_mind_instance_id="m0", destination_mind_instance_id="m_fork", object_id="e_root", operation="evidence_copy"),
        E("believe-fork", EventType.ATTITUDE, 16, valid_from=1, destination_mind_instance_id="m_fork", proposition_id="root_seen", about_world_branch_id="W0", stance="believe"),
        E("snap-1", EventType.SNAPSHOT, 17, source_mind_instance_id="m0", snapshot_id="s1", snapshot_cutoff=13),
        E("restore-edge", EventType.LINEAGE, 18, source_mind_instance_id="m0", destination_mind_instance_id="m_restore", lineage_kind="restore", snapshot_id="s1", snapshot_cutoff=13),

        E("wf-late", EventType.WORLD_FACT, 19, valid_from=2, proposition_id="late_seen", world_branch_id="W0", truth_value=True),
        E("ev-late", EventType.EVIDENCE, 20, object_id="e_late", proposition_id="late_seen", about_world_branch_id="W0", policy_label="public", source_family_id="fam-late"),
        E("x-late", EventType.EXPOSURE, 21, destination_mind_instance_id="m0", object_id="e_late", operation="observe"),
        E("rep-edge", EventType.LINEAGE, 22, source_mind_instance_id="m0", destination_mind_instance_id="m_rep", lineage_kind="operational_replica", snapshot_cutoff=13, authorization_id="auth-rep", authorized=True),

        E("wf-key-w1", EventType.WORLD_FACT, 23, valid_from=5, proposition_id="key_room4", world_branch_id="W1", truth_value=True),
        E("wf-key-w2", EventType.WORLD_FACT, 24, valid_from=5, proposition_id="key_room4", world_branch_id="W2", truth_value=False),
        E("ev-key", EventType.EVIDENCE, 25, object_id="e_key_w1", proposition_id="key_room4", about_world_branch_id="W1", policy_label="public", source_family_id="fam-key"),
        E("x-key-m0", EventType.EXPOSURE, 26, destination_mind_instance_id="m0", object_id="e_key_w1", operation="observe"),
        E("x-key-b", EventType.EXPOSURE, 27, source_mind_instance_id="m0", destination_mind_instance_id="m_b", object_id="e_key_w1", operation="receive", attribution_kind="attributed_report"),
        E("att-key-reject", EventType.ATTITUDE, 28, valid_from=5, destination_mind_instance_id="m_b", proposition_id="key_room4", about_world_branch_id="W1", stance="reject"),
        E("att-key-believe", EventType.ATTITUDE, 29, valid_from=5, destination_mind_instance_id="m_b", proposition_id="key_room4", about_world_branch_id="W1", stance="believe"),

        E("ev-sealed", EventType.EVIDENCE, 30, object_id="e_sealed", proposition_id="sealed_fact", about_world_branch_id="W0", policy_label="public", source_family_id="fam-sealed"),
        E("x-sealed", EventType.EXPOSURE, 31, destination_mind_instance_id="m0", object_id="e_sealed", operation="observe"),
        E("seal", EventType.POLICY, 32, destination_mind_instance_id="m0", object_id="e_sealed", operation="self_seal"),
        E("unseal", EventType.POLICY, 33, destination_mind_instance_id="m0", object_id="e_sealed", operation="self_unseal"),

        E("ev-forget", EventType.EVIDENCE, 34, object_id="e_forget", proposition_id="forgotten_fact", about_world_branch_id="W0", policy_label="public", source_family_id="fam-forget"),
        E("x-forget", EventType.EXPOSURE, 35, destination_mind_instance_id="m0", object_id="e_forget", operation="observe"),
        E("forget", EventType.EXPOSURE, 36, destination_mind_instance_id="m0", object_id="e_forget", operation="forget_active"),
        E("reacquire", EventType.EXPOSURE, 37, destination_mind_instance_id="m0", object_id="e_forget", operation="reacquire", attribution_kind="reconstruction"),

        E("ev-auth-bad", EventType.EVIDENCE, 38, object_id="e_auth_bad", proposition_id="auth_bad", about_world_branch_id="W0", policy_label="public", source_family_id="fam-auth-bad"),
        E("x-auth-bad-src", EventType.EXPOSURE, 39, destination_mind_instance_id="m0", object_id="e_auth_bad", operation="observe"),
        E("x-auth-bad-dst", EventType.EXPOSURE, 40, source_mind_instance_id="m0", destination_mind_instance_id="m_rep", object_id="e_auth_bad", operation="state_replication", authorization_id="missing-approval", authorized=False),
        E("ev-auth-good", EventType.EVIDENCE, 41, object_id="e_auth_good", proposition_id="auth_good", about_world_branch_id="W0", policy_label="public", source_family_id="fam-auth-good"),
        E("x-auth-good-src", EventType.EXPOSURE, 42, destination_mind_instance_id="m0", object_id="e_auth_good", operation="observe"),
        E("x-auth-good-dst", EventType.EXPOSURE, 43, source_mind_instance_id="m0", destination_mind_instance_id="m_rep", object_id="e_auth_good", operation="state_replication", authorization_id="auth-good", authorized=True),

        E("wf-delayed", EventType.WORLD_FACT, 50, valid_from=5, proposition_id="delayed_fact", world_branch_id="W0", truth_value=True),

        E("ev-private", EventType.EVIDENCE, 60, object_id="e_private", proposition_id="diagnosis", about_world_branch_id="W0", policy_label="private:pA", source_family_id="fam-secret"),
        E("ev-public-1", EventType.EVIDENCE, 61, object_id="e_public_1", proposition_id="diagnosis", about_world_branch_id="W0", policy_label="public", source_family_id="fam-camera-1"),
        E("ev-public-2", EventType.EVIDENCE, 62, object_id="e_public_2", proposition_id="diagnosis", about_world_branch_id="W0", policy_label="public", source_family_id="fam-camera-2"),
        E("ev-public-dup", EventType.EVIDENCE, 63, object_id="e_public_dup", proposition_id="diagnosis", about_world_branch_id="W0", policy_label="public", source_family_id="fam-camera-1"),
        E("j-private", EventType.JUSTIFICATION, 64, valid_from=1, proposition_id="diagnosis", about_world_branch_id="W0", support_set_id="J_PRIVATE", support_member_ids=("e_private",), required_independent_sources=1),
        E("j-public", EventType.JUSTIFICATION, 65, valid_from=1, proposition_id="diagnosis", about_world_branch_id="W0", support_set_id="J_PUBLIC", support_member_ids=("e_public_1", "e_public_2"), required_independent_sources=2),
        E("j-duplicate", EventType.JUSTIFICATION, 66, valid_from=1, proposition_id="diagnosis", about_world_branch_id="W0", support_set_id="J_DUP", support_member_ids=("e_public_1", "e_public_dup"), required_independent_sources=2),
        E("revoke-private", EventType.POLICY, 67, object_id="e_private", operation="revoke"),
        E("delete-public-2", EventType.POLICY, 68, object_id="e_public_2", operation="evidence_delete"),
    ]

    Q = Query
    queries = [
        Q("q-world-w1", QueryTarget.WORLD, 24, valid_time=5, proposition_id="key_room4", world_branch_id="W1"),
        Q("q-world-w2", QueryTarget.WORLD, 24, valid_time=5, proposition_id="key_room4", world_branch_id="W2"),
        Q("q-delayed-before", QueryTarget.WORLD, 49, valid_time=10, proposition_id="delayed_fact", world_branch_id="W0"),
        Q("q-delayed-after", QueryTarget.WORLD, 50, valid_time=10, proposition_id="delayed_fact", world_branch_id="W0"),

        Q("q-rep-root", QueryTarget.EVER_EXPOSED, 22, mind_instance_id="m_rep", evidence_id="e_root"),
        Q("q-rep-late", QueryTarget.EVER_EXPOSED, 22, mind_instance_id="m_rep", evidence_id="e_late"),
        Q("q-restore-root", QueryTarget.EVER_EXPOSED, 21, mind_instance_id="m_restore", evidence_id="e_root"),
        Q("q-restore-late", QueryTarget.EVER_EXPOSED, 21, mind_instance_id="m_restore", evidence_id="e_late"),
        Q("q-receive-exposed", QueryTarget.EVER_EXPOSED, 27, mind_instance_id="m_b", evidence_id="e_key_w1"),

        Q("q-sealed-before", QueryTarget.AVAILABLE, 31, mind_instance_id="m0", evidence_id="e_sealed"),
        Q("q-sealed-during", QueryTarget.AVAILABLE, 32, mind_instance_id="m0", evidence_id="e_sealed"),
        Q("q-sealed-ever", QueryTarget.EVER_EXPOSED, 32, mind_instance_id="m0", evidence_id="e_sealed"),
        Q("q-sealed-after", QueryTarget.AVAILABLE, 33, mind_instance_id="m0", evidence_id="e_sealed"),
        Q("q-forget", QueryTarget.AVAILABLE, 36, mind_instance_id="m0", evidence_id="e_forget"),
        Q("q-forget-ever", QueryTarget.EVER_EXPOSED, 36, mind_instance_id="m0", evidence_id="e_forget"),
        Q("q-reacquire", QueryTarget.AVAILABLE, 37, mind_instance_id="m0", evidence_id="e_forget"),

        Q("q-att-before", QueryTarget.ATTITUDE, 27, valid_time=5, mind_instance_id="m_b", proposition_id="key_room4", world_branch_id="W1"),
        Q("q-att-reject", QueryTarget.ATTITUDE, 28, valid_time=5, mind_instance_id="m_b", proposition_id="key_room4", world_branch_id="W1"),
        Q("q-att-believe", QueryTarget.ATTITUDE, 29, valid_time=5, mind_instance_id="m_b", proposition_id="key_room4", world_branch_id="W1"),
        Q("q-att-w2", QueryTarget.ATTITUDE, 29, valid_time=5, mind_instance_id="m_b", proposition_id="key_room4", world_branch_id="W2"),

        Q("q-attr-fork", QueryTarget.ATTRIBUTION, 16, mind_instance_id="m_fork", proposition_id="root_seen", world_branch_id="W0"),
        Q("q-attr-restore", QueryTarget.ATTRIBUTION, 18, mind_instance_id="m_restore", proposition_id="root_seen", world_branch_id="W0"),
        Q("q-attr-report", QueryTarget.ATTRIBUTION, 29, mind_instance_id="m_b", proposition_id="key_room4", world_branch_id="W1"),
        Q("q-attr-bad-repl", QueryTarget.ATTRIBUTION, 40, mind_instance_id="m_rep", proposition_id="auth_bad", world_branch_id="W0"),
        Q("q-attr-good-repl", QueryTarget.ATTRIBUTION, 43, mind_instance_id="m_rep", proposition_id="auth_good", world_branch_id="W0"),

        Q("q-disc-public", QueryTarget.DISCLOSE, 66, valid_time=1, proposition_id="diagnosis", world_branch_id="W0", requester_id="public_user"),
        Q("q-just-public", QueryTarget.JUSTIFICATION, 66, valid_time=1, proposition_id="diagnosis", world_branch_id="W0", requester_id="public_user"),
        Q("q-just-owner", QueryTarget.JUSTIFICATION, 66, valid_time=1, proposition_id="diagnosis", world_branch_id="W0", requester_id="pA"),
        Q("q-just-after-revoke", QueryTarget.JUSTIFICATION, 67, valid_time=1, proposition_id="diagnosis", world_branch_id="W0", requester_id="pA"),
        Q("q-disc-after-delete", QueryTarget.DISCLOSE, 68, valid_time=1, proposition_id="diagnosis", world_branch_id="W0", requester_id="public_user"),
    ]
    return Fixture.from_iterables("semantic-conformance-v0.2", events, queries)
