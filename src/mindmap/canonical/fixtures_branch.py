from __future__ import annotations

from .fixture_common import E, Q, base_identity, placement
from .model import Attribution, Fixture, TargetSpace


def fixture_branch_visibility() -> Fixture:
    p = "F01"
    events = base_identity(
        p,
        branches=(("main", None, None, 0), ("child", "main", 10, 10)),
    )
    events += [
        placement(p, "PM", "M", "main"),
        E("F01.c0", "world_claim", 5, proposition_id="key.location", about_world_branch_id="main", valid_from=0, attrs={"value": "Room 1"}),
        # Parent-world update begins after the child fork and must not leak.
        E("F01.c1", "world_claim", 12, proposition_id="key.location", about_world_branch_id="main", valid_from=12, attrs={"value": "Room 2"}),
        # Imported later in database time, but asserted to hold before the fork.
        E("F01.c2", "world_claim", 20, proposition_id="key.location", about_world_branch_id="main", valid_from=0, valid_to=12, attrs={"value": "Room 0"}),
        E("F01.c3", "world_claim", 22, proposition_id="key.location", about_world_branch_id="child", valid_from=15, attrs={"value": "Room 3"}),
    ]
    cases = [
        Q("F01.q1", TargetSpace.WORLD, "Room 2", "parent_postfork_state", system_time=15, valid_time=20, proposition_id="key.location", world_branch_id="main"),
        Q("F01.q2", TargetSpace.WORLD, "Room 1", "postfork_parent_update_not_inherited", system_time=15, valid_time=20, proposition_id="key.location", world_branch_id="child"),
        Q("F01.q3", TargetSpace.WORLD, "Room 0", "late_import_of_prefork_fact_visible", system_time=21, valid_time=20, proposition_id="key.location", world_branch_id="child"),
        Q("F01.q4", TargetSpace.WORLD, "Room 3", "branch_local_override", system_time=25, valid_time=20, proposition_id="key.location", world_branch_id="child"),
        Q("F01.q5", TargetSpace.WORLD, "Room 1", "point_in_system_time_before_late_import", system_time=19, valid_time=8, proposition_id="key.location", world_branch_id="child"),
    ]
    return Fixture("F01", "branch_visibility", tuple(events), tuple(cases), tags=("world_branch", "bitemporal"))

def fixture_mind_copy_without_world_fork() -> Fixture:
    p = "F02"
    events = base_identity(p, minds=(("A0", "P"), ("A1", "P"), ("A2", "P")))
    events += [placement(p, "P0", "A0", "main"), placement(p, "P1", "A1", "main"), placement(p, "P2", "A2", "main")]
    events += [
        E("F02.l1", "lineage", 5, lineage_kind="operational_replica", source_mind_instance_id="A0", destination_mind_instance_id="A1"),
        E("F02.l2", "lineage", 5, lineage_kind="operational_replica", source_mind_instance_id="A0", destination_mind_instance_id="A2"),
        E("F02.e1", "evidence", 10, object_id="E.key", proposition_id="key_in_r4", actor_principal_id="P", actor_mind_instance_id="A1", source_placement_id="P1", about_world_branch_id="main", source_family_id="camera-A1"),
        E("F02.x1", "exposure", 10, object_id="E.key", destination_mind_instance_id="A1", transfer_kind="observe", attribution_kind=Attribution.DIRECT_OBSERVATION.value),
        E("F02.a1", "attitude", 11, proposition_id="key_in_r4", destination_mind_instance_id="A1", about_world_branch_id="main", attitude_transition="believe"),
    ]
    cases = [
        Q("F02.q1", TargetSpace.EVER_EXPOSED, True, "copy_does_not_share_postfork_exposure", system_time=20, evidence_id="E.key", mind_instance_id="A1"),
        Q("F02.q2", TargetSpace.EVER_EXPOSED, False, "sibling_copy_isolated", system_time=20, evidence_id="E.key", mind_instance_id="A2"),
        Q("F02.q3", TargetSpace.AVAILABLE, True, "observer_current_availability", system_time=20, evidence_id="E.key", mind_instance_id="A1"),
        Q("F02.q4", TargetSpace.AVAILABLE, False, "unexposed_copy_unavailable", system_time=20, evidence_id="E.key", mind_instance_id="A2"),
        Q("F02.q5", TargetSpace.ATTITUDE, "believe", "instance_specific_attitude", system_time=20, valid_time=20, proposition_id="key_in_r4", world_branch_id="main", mind_instance_id="A1"),
        Q("F02.q6", TargetSpace.ATTITUDE, "unknown", "same_principal_not_same_belief", system_time=20, valid_time=20, proposition_id="key_in_r4", world_branch_id="main", mind_instance_id="A2"),
        Q("F02.q7", TargetSpace.ATTRIBUTION, Attribution.DIRECT_OBSERVATION.value, "direct_observation_attribution", system_time=20, proposition_id="key_in_r4", mind_instance_id="A1"),
        Q("F02.q8", TargetSpace.ATTRIBUTION, Attribution.UNKNOWN.value, "no_attribution_without_exposure", system_time=20, proposition_id="key_in_r4", mind_instance_id="A2"),
    ]
    return Fixture("F02", "mind_copy_without_world_fork", tuple(events), tuple(cases), tags=("mind_lineage", "same_principal"))

def fixture_world_fork_without_mind_copy() -> Fixture:
    p = "F03"
    events = base_identity(p, branches=(("main", None, None, 0), ("alt", "main", 10, 10)))
    events += [placement(p, "PM", "M", "main")]
    events += [
        E("F03.c0", "world_claim", 5, proposition_id="door.color", about_world_branch_id="main", valid_from=0, attrs={"value": "gray"}),
        E("F03.c1", "world_claim", 12, proposition_id="door.color", about_world_branch_id="main", valid_from=12, attrs={"value": "blue"}),
        E("F03.c2", "world_claim", 12, proposition_id="door.color", about_world_branch_id="alt", valid_from=12, attrs={"value": "red"}),
    ]
    cases = [
        Q("F03.q1", TargetSpace.WORLD, "blue", "main_world_continues", system_time=20, valid_time=20, proposition_id="door.color", world_branch_id="main"),
        Q("F03.q2", TargetSpace.WORLD, "red", "child_world_local_state", system_time=20, valid_time=20, proposition_id="door.color", world_branch_id="alt"),
        Q("F03.q3", TargetSpace.WORLD, "gray", "prefork_state_shared", system_time=9, valid_time=9, proposition_id="door.color", world_branch_id="main"),
    ]
    return Fixture("F03", "world_fork_without_mind_copy", tuple(events), tuple(cases), tags=("world_branch",))

def fixture_unsynchronized_replicas() -> Fixture:
    p = "F04"
    events = base_identity(p, minds=(("R1", "P"), ("R2", "P")))
    events += [placement(p, "P1", "R1", "main"), placement(p, "P2", "R2", "main")]
    events += [
        E("F04.l", "lineage", 1, lineage_kind="operational_replica", source_mind_instance_id="R1", destination_mind_instance_id="R2"),
        E("F04.e1", "evidence", 5, object_id="E.r1", proposition_id="alarm_on", actor_principal_id="P", actor_mind_instance_id="R1", source_placement_id="P1", about_world_branch_id="main", source_family_id="sensor-r1"),
        E("F04.x1", "exposure", 5, object_id="E.r1", destination_mind_instance_id="R1", transfer_kind="observe"),
        E("F04.a1", "attitude", 6, proposition_id="alarm_on", destination_mind_instance_id="R1", about_world_branch_id="main", attitude_transition="believe"),
        E("F04.e2", "evidence", 7, object_id="E.r2", proposition_id="alarm_off", actor_principal_id="P", actor_mind_instance_id="R2", source_placement_id="P2", about_world_branch_id="main", source_family_id="sensor-r2"),
        E("F04.x2", "exposure", 7, object_id="E.r2", destination_mind_instance_id="R2", transfer_kind="observe"),
        E("F04.a2", "attitude", 8, proposition_id="alarm_on", destination_mind_instance_id="R2", about_world_branch_id="main", attitude_transition="disbelieve"),
    ]
    cases = [
        Q("F04.q1", TargetSpace.ATTITUDE, "believe", "replica_one_belief", system_time=20, valid_time=20, proposition_id="alarm_on", world_branch_id="main", mind_instance_id="R1"),
        Q("F04.q2", TargetSpace.ATTITUDE, "disbelieve", "replica_two_belief", system_time=20, valid_time=20, proposition_id="alarm_on", world_branch_id="main", mind_instance_id="R2"),
        Q("F04.q3", TargetSpace.EVER_EXPOSED, False, "no_implicit_same_principal_sync", system_time=20, evidence_id="E.r1", mind_instance_id="R2"),
        Q("F04.q4", TargetSpace.EVER_EXPOSED, False, "reverse_no_implicit_sync", system_time=20, evidence_id="E.r2", mind_instance_id="R1"),
    ]
    return Fixture("F04", "unsynchronized_same_principal_replicas", tuple(events), tuple(cases), tags=("same_principal", "replica"))
