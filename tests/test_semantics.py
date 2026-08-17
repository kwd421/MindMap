from mindmap.core import BranchScopedCharacterResolver, NCMResolver
from mindmap.scenarios import (
    build_backdated_correction,
    build_cross_world_report,
    build_mind_fork_isolation,
    build_private_derivation,
    build_restore_gap,
    build_sealed_memory,
    build_world_fork_isolation,
)


def test_mind_fork_isolation_requires_instance_lineage():
    scenario = build_mind_fork_isolation("t001", 1)
    scoped = BranchScopedCharacterResolver()
    ncm = NCMResolver()
    target = next(q for q in scenario.queries if q.kind == "access" and q.expected == "no")
    assert scoped.answer(scenario, target) == "yes"
    assert ncm.answer(scenario, target) == "no"


def test_world_branch_isolation_is_independent_of_mind_lineage():
    scenario = build_world_fork_isolation("t002", 2)
    ncm = NCMResolver()
    for query in scenario.queries:
        assert ncm.answer(scenario, query) == query.expected


def test_private_policy_propagates_through_derivation():
    scenario = build_private_derivation("t003", 3)
    scoped = BranchScopedCharacterResolver()
    ncm = NCMResolver()
    public_query = next(
        q for q in scenario.queries
        if q.kind == "disclose" and q.requester_id == "public_user" and q.transaction_time == 20
    )
    assert scoped.answer(scenario, public_query) == "yes"
    assert ncm.answer(scenario, public_query) == "no"


def test_restore_inherits_only_through_snapshot_cutoff():
    scenario = build_restore_gap("t004", 4)
    ncm = NCMResolver()
    for query in scenario.queries:
        assert ncm.answer(scenario, query) == query.expected


def test_transaction_time_changes_point_in_time_answer():
    scenario = build_backdated_correction("t005", 5)
    ncm = NCMResolver()
    before = next(q for q in scenario.queries if q.metadata.get("label") == "before_learning_correction")
    after = next(q for q in scenario.queries if q.metadata.get("label") == "after_learning_correction")
    assert before.valid_time == after.valid_time
    assert before.transaction_time < after.transaction_time
    assert ncm.answer(scenario, before) == before.expected
    assert ncm.answer(scenario, after) == after.expected
    assert before.expected != after.expected


def test_about_world_branch_is_distinct_from_holder_context():
    scenario = build_cross_world_report("t006", 6)
    ncm = NCMResolver()
    for query in scenario.queries:
        assert ncm.answer(scenario, query) == query.expected


def test_seal_changes_availability_but_not_historical_exposure():
    scenario = build_sealed_memory("t007", 7)
    ncm = NCMResolver()
    available = next(
        q for q in scenario.queries
        if q.kind == "access" and q.transaction_time == 35 and q.target_mind_instance_id == "A2"
    )
    historical = next(q for q in scenario.queries if q.kind == "ever_exposed")
    assert ncm.answer(scenario, available) == "no"
    assert ncm.answer(scenario, historical) == "yes"
