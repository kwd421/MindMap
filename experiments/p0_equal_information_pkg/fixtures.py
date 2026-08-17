from __future__ import annotations

from .model import *

def add_base(b: Builder, *, second_principal: bool = False) -> None:
    b.e("branch_create", 0, 0, branch="root", parent=None, fork_valid=None, fork_system=None)
    b.e("principal_create", 0, 0, principal="p1")
    b.e("mind_create", 0, 0, instance="m1", principal="p1")
    b.e("placement", 0, 0, instance="m1", branch="root", operation="instantiate")
    if second_principal:
        b.e("principal_create", 0, 0, principal="p2")
        b.e("mind_create", 0, 0, instance="m2", principal="p2")
        b.e("placement", 0, 0, instance="m2", branch="root", operation="instantiate")


def fixture_identity_fork_public_backup() -> Fixture:
    b = Builder("f01", "identity_fork_copy_public_backup")
    add_base(b, second_principal=True)
    lin = b.e(
        "lineage",
        1,
        1,
        source_instance="m1",
        destination_instance="m2",
        kind="identity_fork",
        cutoff_system=0,
        authorization=True,
    )
    private = b.e(
        "evidence",
        2,
        2,
        object_id="priv",
        actor_instance="m1",
        branch="root",
        source_family="family-private",
        policy="private",
    )
    obs = b.e(
        "exposure",
        2,
        2,
        destination_instance="m1",
        source_instance=None,
        object_id="priv",
        operation="observe",
        attribution="direct_observation",
        authorization=True,
        branch="root",
    )
    copy = b.e(
        "exposure",
        3,
        3,
        destination_instance="m2",
        source_instance="m1",
        object_id="priv",
        operation="evidence_copy",
        attribution="evidence_copy",
        authorization=True,
        branch="root",
    )
    adopt = b.e(
        "attitude",
        4,
        4,
        instance="m2",
        proposition="x",
        about_branch="root",
        stance="believe",
        value="true",
        source_object="priv",
    )
    public = b.e(
        "evidence",
        5,
        5,
        object_id="cam",
        actor_instance="m1",
        branch="root",
        source_family="family-camera",
        policy="public",
    )
    j1 = b.e(
        "justification",
        5,
        5,
        claim_id="claim-x",
        proposition="x",
        members=("priv",),
        min_independent=1,
    )
    j2 = b.e(
        "justification",
        5,
        5,
        claim_id="claim-x",
        proposition="x",
        members=("cam",),
        min_independent=1,
    )
    revoke = b.e(
        "policy",
        6,
        6,
        object_id="priv",
        operation="revoke",
        new_policy="deleted",
        authorization=True,
    )
    b.q("attitude", "believe:true", 7, 7, instance="m2", proposition="x", depends_on=(copy, adopt))
    b.q("attribution", "evidence_copy", 7, 7, instance="m2", proposition="x", object_id="priv", depends_on=(lin, copy))
    b.q("disclose", "yes", 7, 7, claim_id="claim-x", depends_on=(public, j2, revoke))
    b.q("justification", "family-camera", 7, 7, claim_id="claim-x", depends_on=(public, j2, revoke))
    b.q("ever_exposed", "yes", 7, 7, instance="m2", object_id="priv", depends_on=(copy,))
    return b.build()


def fixture_operational_replica() -> Fixture:
    b = Builder("f02", "authorized_operational_replica")
    add_base(b)
    m2 = b.e("mind_create", 1, 1, instance="m2", principal="p1")
    b.e("placement", 1, 1, instance="m2", branch="root", operation="instantiate")
    lin = b.e(
        "lineage",
        1,
        1,
        source_instance="m1",
        destination_instance="m2",
        kind="operational_replica",
        cutoff_system=2,
        authorization=True,
    )
    ev = b.e(
        "evidence",
        2,
        2,
        object_id="obs",
        actor_instance="m1",
        branch="root",
        source_family="family-obs",
        policy="private",
    )
    b.e(
        "exposure",
        2,
        2,
        destination_instance="m1",
        source_instance=None,
        object_id="obs",
        operation="observe",
        attribution="direct_observation",
        authorization=True,
        branch="root",
    )
    rep = b.e(
        "exposure",
        3,
        3,
        destination_instance="m2",
        source_instance="m1",
        object_id="obs",
        operation="state_replication",
        attribution="same_principal_state_replication",
        authorization=True,
        branch="root",
    )
    att = b.e(
        "attitude",
        3,
        3,
        instance="m2",
        proposition="door-open",
        about_branch="root",
        stance="believe",
        value="true",
        source_object="obs",
    )
    b.q("attribution", "same_principal_state_replication", 4, 4, instance="m2", proposition="door-open", object_id="obs", depends_on=(m2, lin, rep))
    b.q("merge_eligible", "yes", 4, 4, source_instance="m1", destination_instance="m2", depends_on=(lin,))
    b.q("attitude", "believe:true", 4, 4, instance="m2", proposition="door-open", depends_on=(rep, att))
    b.q("available", "yes", 4, 4, instance="m2", object_id="obs", depends_on=(rep,))
    return b.build()


def fixture_identity_fork_no_first_person() -> Fixture:
    b = Builder("f03", "identity_fork_no_first_person")
    add_base(b, second_principal=True)
    lin = b.e("lineage", 1, 1, source_instance="m1", destination_instance="m2", kind="identity_fork", cutoff_system=1, authorization=True)
    ev = b.e("evidence", 2, 2, object_id="diary", actor_instance="m1", branch="root", source_family="family-diary", policy="private")
    b.e("exposure", 2, 2, destination_instance="m1", source_instance=None, object_id="diary", operation="observe", attribution="direct_observation", authorization=True, branch="root")
    copy = b.e("exposure", 3, 3, destination_instance="m2", source_instance="m1", object_id="diary", operation="evidence_copy", attribution="evidence_copy", authorization=True, branch="root")
    att = b.e("attitude", 4, 4, instance="m2", proposition="met-alice", about_branch="root", stance="believe", value="true", source_object="diary")
    b.q("attribution", "evidence_copy", 5, 5, instance="m2", proposition="met-alice", object_id="diary", depends_on=(lin, copy))
    b.q("merge_eligible", "no", 5, 5, source_instance="m1", destination_instance="m2", depends_on=(lin,))
    b.q("attitude", "believe:true", 5, 5, instance="m2", proposition="met-alice", depends_on=(copy, att))
    return b.build()


def fixture_restore_gap() -> Fixture:
    b = Builder("f04", "restore_with_recovery_gap")
    add_base(b)
    e0 = b.e("evidence", 2, 2, object_id="pre", actor_instance="m1", branch="root", source_family="family-pre", policy="private")
    b.e("exposure", 2, 2, destination_instance="m1", source_instance=None, object_id="pre", operation="observe", attribution="direct_observation", authorization=True, branch="root")
    e1 = b.e("evidence", 8, 8, object_id="post", actor_instance="m1", branch="root", source_family="family-post", policy="private")
    b.e("exposure", 8, 8, destination_instance="m1", source_instance=None, object_id="post", operation="observe", attribution="direct_observation", authorization=True, branch="root")
    snap = b.e("snapshot", 10, 10, snapshot_id="snap-5", source_instance="m1", cutoff_system=5, members=("pre",))
    b.e("mind_create", 10, 10, instance="mr", principal="p1")
    b.e("placement", 10, 10, instance="mr", branch="root", operation="restore_into")
    lin = b.e("lineage", 10, 10, source_instance="m1", destination_instance="mr", kind="restore", cutoff_system=5, authorization=True, snapshot_id="snap-5")
    restore = b.e("exposure", 10, 10, destination_instance="mr", source_instance="m1", object_id="pre", operation="restore", attribution="same_principal_snapshot_inheritance", authorization=True, branch="root", snapshot_id="snap-5")
    b.q("available", "yes", 11, 11, instance="mr", object_id="pre", depends_on=(snap, lin, restore))
    b.q("available", "no", 11, 11, instance="mr", object_id="post", depends_on=(e1, snap, lin))
    b.q("ever_exposed", "no", 11, 11, instance="mr", object_id="post", depends_on=(e1, snap, lin))
    b.q("attribution", "same_principal_snapshot_inheritance", 11, 11, instance="mr", proposition="pre-event", object_id="pre", depends_on=(snap, lin, restore))
    return b.build()


def fixture_world_fork_delayed_import() -> Fixture:
    b = Builder("f05", "world_fork_delayed_pre_fork_import")
    b.e("branch_create", 0, 0, branch="root", parent=None, fork_valid=None, fork_system=None)
    fork = b.e("branch_create", 10, 10, branch="child", parent="root", fork_valid=10, fork_system=10)
    pre = b.e("world_claim", 5, 20, proposition="flag", value="old", about_branch="root", valid_from=5, valid_to=None, status="active", source_object=None)
    post = b.e("world_claim", 15, 9, proposition="flag", value="parent-new", about_branch="root", valid_from=15, valid_to=None, status="active", source_object=None)
    child = b.e("world_claim", 16, 16, proposition="flag", value="child-new", about_branch="child", valid_from=16, valid_to=None, status="active", source_object=None)
    b.q("world", "old", 6, 25, branch="child", proposition="flag", depends_on=(fork, pre))
    b.q("world", "child-new", 20, 25, branch="child", proposition="flag", depends_on=(fork, post, child))
    b.q("world", "parent-new", 20, 25, branch="root", proposition="flag", depends_on=(post,))
    return b.build()


def fixture_receive_no_adoption() -> Fixture:
    b = Builder("f06", "receipt_without_belief")
    add_base(b, second_principal=True)
    ev = b.e("evidence", 1, 1, object_id="report", actor_instance="m1", branch="root", source_family="family-report", policy="public")
    recv = b.e("exposure", 2, 2, destination_instance="m2", source_instance="m1", object_id="report", operation="receive", attribution="attributed_report", authorization=True, branch="root")
    b.q("ever_exposed", "yes", 3, 3, instance="m2", object_id="report", depends_on=(recv,))
    b.q("available", "yes", 3, 3, instance="m2", object_id="report", depends_on=(recv,))
    b.q("attitude", UNKNOWN, 3, 3, instance="m2", proposition="rain", depends_on=(ev, recv))
    b.q("attribution", "attributed_report", 3, 3, instance="m2", proposition="rain", object_id="report", depends_on=(recv,))
    return b.build()


def fixture_receive_reject() -> Fixture:
    b = Builder("f07", "receipt_and_rejection")
    add_base(b, second_principal=True)
    ev = b.e("evidence", 1, 1, object_id="rumor", actor_instance="m1", branch="root", source_family="family-rumor", policy="public")
    recv = b.e("exposure", 2, 2, destination_instance="m2", source_instance="m1", object_id="rumor", operation="receive", attribution="attributed_report", authorization=True, branch="root")
    reject = b.e("attitude", 3, 3, instance="m2", proposition="rain", about_branch="root", stance="disbelieve", value="true", source_object="rumor")
    b.q("attitude", "disbelieve:true", 4, 4, instance="m2", proposition="rain", depends_on=(ev, recv, reject))
    b.q("attribution", "attributed_report", 4, 4, instance="m2", proposition="rain", object_id="rumor", depends_on=(recv,))
    return b.build()


def fixture_forget_reacquire() -> Fixture:
    b = Builder("f08", "forget_and_reacquire")
    add_base(b, second_principal=True)
    ev = b.e("evidence", 1, 1, object_id="memo", actor_instance="m1", branch="root", source_family="family-memo", policy="public")
    recv = b.e("exposure", 2, 2, destination_instance="m2", source_instance="m1", object_id="memo", operation="receive", attribution="attributed_report", authorization=True, branch="root")
    forget = b.e("exposure", 4, 4, destination_instance="m2", source_instance="m2", object_id="memo", operation="forget_active", attribution="attributed_report", authorization=True, branch="root")
    reacquire = b.e("exposure", 6, 6, destination_instance="m2", source_instance="m1", object_id="memo", operation="reacquire", attribution="attributed_report", authorization=True, branch="root")
    b.q("ever_exposed", "yes", 5, 5, instance="m2", object_id="memo", depends_on=(recv, forget))
    b.q("available", "no", 5, 5, instance="m2", object_id="memo", depends_on=(recv, forget))
    b.q("ever_exposed", "yes", 7, 7, instance="m2", object_id="memo", depends_on=(recv, forget, reacquire))
    b.q("available", "yes", 7, 7, instance="m2", object_id="memo", depends_on=(recv, forget, reacquire))
    return b.build()


def fixture_protected_only_revoke() -> Fixture:
    b = Builder("f09", "shared_support_revoked")
    add_base(b)
    ev = b.e("evidence", 1, 1, object_id="secret", actor_instance="m1", branch="root", source_family="family-secret", policy="public")
    just = b.e("justification", 2, 2, claim_id="c", proposition="x", members=("secret",), min_independent=1)
    revoke = b.e("policy", 3, 3, object_id="secret", operation="revoke", new_policy="deleted", authorization=True)
    b.q("disclose", "no", 4, 4, claim_id="c", depends_on=(ev, just, revoke))
    b.q("justification", "withhold", 4, 4, claim_id="c", depends_on=(ev, just, revoke))
    return b.build()


def fixture_same_origin_not_independent() -> Fixture:
    b = Builder("f10", "same_origin_not_independent")
    add_base(b)
    e1 = b.e("evidence", 1, 1, object_id="copy1", actor_instance="m1", branch="root", source_family="family-one", policy="public")
    e2 = b.e("evidence", 2, 2, object_id="copy2", actor_instance="m1", branch="root", source_family="family-one", policy="public")
    just = b.e("justification", 3, 3, claim_id="c", proposition="x", members=("copy1", "copy2"), min_independent=2)
    b.q("disclose", "no", 4, 4, claim_id="c", depends_on=(e1, e2, just))
    b.q("justification", "withhold", 4, 4, claim_id="c", depends_on=(e1, e2, just))
    return b.build()


def fixture_cross_world_report() -> Fixture:
    b = Builder("f11", "cross_world_report")
    b.e("branch_create", 0, 0, branch="w1", parent=None, fork_valid=None, fork_system=None)
    b.e("branch_create", 0, 0, branch="w2", parent=None, fork_valid=None, fork_system=None)
    b.e("principal_create", 0, 0, principal="p1")
    b.e("principal_create", 0, 0, principal="p2")
    b.e("mind_create", 0, 0, instance="m1", principal="p1")
    b.e("mind_create", 0, 0, instance="m2", principal="p2")
    b.e("placement", 0, 0, instance="m1", branch="w1", operation="instantiate")
    b.e("placement", 0, 0, instance="m2", branch="w2", operation="instantiate")
    ev = b.e("evidence", 1, 1, object_id="w1-report", actor_instance="m1", branch="w1", source_family="family-w1", policy="public")
    world = b.e("world_claim", 1, 1, proposition="bridge-open", value="true", about_branch="w1", valid_from=1, valid_to=None, status="active", source_object="w1-report")
    recv = b.e("exposure", 2, 2, destination_instance="m2", source_instance="m1", object_id="w1-report", operation="receive", attribution="attributed_report", authorization=True, branch="w2")
    att = b.e("attitude", 3, 3, instance="m2", proposition="bridge-open", about_branch="w1", stance="believe", value="true", source_object="w1-report")
    b.q("attitude", "believe:true", 4, 4, branch="w2", instance="m2", proposition="bridge-open@w1", depends_on=(recv, att))
    b.q("attitude", UNKNOWN, 4, 4, branch="w2", instance="m2", proposition="bridge-open@w2", depends_on=(recv, att))
    b.q("world", "true", 4, 4, branch="w1", proposition="bridge-open", depends_on=(ev, world))
    b.q("world", UNKNOWN, 4, 4, branch="w2", proposition="bridge-open", depends_on=(world,))
    b.q("source_actor", "m1", 4, 4, branch="w2", object_id="w1-report", depends_on=(ev,))
    return b.build()


def fixture_fragment_reconstruct() -> Fixture:
    b = Builder("f12", "multi_source_fragment_reconstruction")
    add_base(b, second_principal=True)
    b.e("principal_create", 0, 0, principal="p3")
    b.e("mind_create", 0, 0, instance="m3", principal="p3")
    b.e("placement", 0, 0, instance="m3", branch="root", operation="instantiate")
    l1 = b.e("lineage", 1, 1, source_instance="m1", destination_instance="m3", kind="fragment_reconstruct", cutoff_system=1, authorization=True)
    l2 = b.e("lineage", 1, 1, source_instance="m2", destination_instance="m3", kind="fragment_reconstruct", cutoff_system=1, authorization=True)
    ev = b.e("evidence", 2, 2, object_id="fragment", actor_instance="m1", branch="root", source_family="family-fragment", policy="private")
    rec = b.e("exposure", 3, 3, destination_instance="m3", source_instance="m1", object_id="fragment", operation="evidence_copy", attribution="reconstruction", authorization=True, branch="root")
    att = b.e("attitude", 4, 4, instance="m3", proposition="identity-clue", about_branch="root", stance="suspect", value="true", source_object="fragment")
    b.q("attribution", "reconstruction", 5, 5, instance="m3", proposition="identity-clue", object_id="fragment", depends_on=(l1, l2, rec))
    b.q("merge_eligible", "no", 5, 5, source_instance="m1", destination_instance="m3", depends_on=(l1,))
    b.q("attitude", "suspect:true", 5, 5, instance="m3", proposition="identity-clue", depends_on=(rec, att))
    return b.build()


def fixture_ordinary_temporal_update() -> Fixture:
    b = Builder("f13", "ordinary_temporal_update_control")
    b.e("branch_create", 0, 0, branch="root", parent=None, fork_valid=None, fork_system=None)
    old = b.e("world_claim", 1, 1, proposition="location", value="seoul", about_branch="root", valid_from=1, valid_to=5, status="active", source_object=None)
    new = b.e("world_claim", 5, 5, proposition="location", value="busan", about_branch="root", valid_from=5, valid_to=None, status="active", source_object=None)
    b.q("world", "seoul", 3, 6, proposition="location", depends_on=(old,))
    b.q("world", "busan", 7, 7, proposition="location", depends_on=(new,))
    return b.build()


def fixture_same_principal_unsynchronized() -> Fixture:
    b = Builder("f14", "same_principal_unsynchronized_replicas")
    add_base(b)
    b.e("mind_create", 1, 1, instance="m2", principal="p1")
    b.e("placement", 1, 1, instance="m2", branch="root", operation="instantiate")
    lin = b.e("lineage", 1, 1, source_instance="m1", destination_instance="m2", kind="operational_replica", cutoff_system=1, authorization=True)
    ev = b.e("evidence", 2, 2, object_id="later", actor_instance="m1", branch="root", source_family="family-later", policy="private")
    obs = b.e("exposure", 2, 2, destination_instance="m1", source_instance=None, object_id="later", operation="observe", attribution="direct_observation", authorization=True, branch="root")
    b.q("available", "yes", 3, 3, instance="m1", object_id="later", depends_on=(obs,))
    b.q("available", "no", 3, 3, instance="m2", object_id="later", depends_on=(lin, ev, obs))
    b.q("ever_exposed", "no", 3, 3, instance="m2", object_id="later", depends_on=(lin, ev, obs))
    return b.build()


def all_fixtures() -> list[Fixture]:
    return [
        fixture_identity_fork_public_backup(),
        fixture_operational_replica(),
        fixture_identity_fork_no_first_person(),
        fixture_restore_gap(),
        fixture_world_fork_delayed_import(),
        fixture_receive_no_adoption(),
        fixture_receive_reject(),
        fixture_forget_reacquire(),
        fixture_protected_only_revoke(),
        fixture_same_origin_not_independent(),
        fixture_cross_world_report(),
        fixture_fragment_reconstruct(),
        fixture_ordinary_temporal_update(),
        fixture_same_principal_unsynchronized(),
    ]


# ---------------------------------------------------------------------------
# Generic and typed representations
# ---------------------------------------------------------------------------

