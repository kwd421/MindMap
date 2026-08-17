from mindmap.v02_fixtures import build_semantic_conformance_fixture
from mindmap.v02_generic import GenericEventLedger
from mindmap.v02_gold import DeclarativeGold
from mindmap.v02_model import Answer, QueryTarget
from mindmap.v02_typed import TypedV02Ledger


def _systems():
    fixture = build_semantic_conformance_fixture()
    return (
        fixture,
        DeclarativeGold(fixture.events),
        GenericEventLedger(fixture.events),
        TypedV02Ledger(fixture.events),
    )


def test_complete_generic_and_typed_match_independent_gold():
    fixture, gold, generic, typed = _systems()
    mismatches = []
    for query in fixture.queries:
        expected = gold.answer(query)
        generic_answer = generic.answer(query)
        typed_answer = typed.answer(query)
        if not (expected == generic_answer == typed_answer):
            mismatches.append((query.query_id, expected, generic_answer, typed_answer))
    assert not mismatches


def test_fixture_covers_every_canonical_target():
    fixture, *_ = _systems()
    assert {query.target for query in fixture.queries} == set(QueryTarget)


def test_decisive_semantic_outputs_are_explicit():
    fixture, gold, *_ = _systems()
    by_id = {query.query_id: gold.answer(query).value for query in fixture.queries}

    assert by_id["q-world-w1"] is True
    assert by_id["q-world-w2"] is False
    assert by_id["q-delayed-before"] is None
    assert by_id["q-delayed-after"] is True

    assert by_id["q-rep-root"] is True
    assert by_id["q-rep-late"] is False
    assert by_id["q-restore-root"] is True
    assert by_id["q-restore-late"] is False

    assert by_id["q-sealed-during"] is False
    assert by_id["q-sealed-ever"] is True
    assert by_id["q-sealed-after"] is True
    assert by_id["q-forget"] is False
    assert by_id["q-forget-ever"] is True
    assert by_id["q-reacquire"] is True

    assert by_id["q-att-before"] is None
    assert by_id["q-att-reject"] == "reject"
    assert by_id["q-att-believe"] == "believe"
    assert by_id["q-att-w2"] is None

    assert by_id["q-attr-fork"] == "evidence_copy"
    assert by_id["q-attr-restore"] == "same_principal_snapshot_inheritance"
    assert by_id["q-attr-report"] == "attributed_report"
    assert by_id["q-attr-bad-repl"] == "evidence_copy"
    assert by_id["q-attr-good-repl"] == "same_principal_state_replication"

    assert by_id["q-disc-public"] is True
    assert by_id["q-just-public"] == ("J_PUBLIC",)
    assert by_id["q-just-owner"] == ("J_PRIVATE", "J_PUBLIC")
    assert by_id["q-just-after-revoke"] == ("J_PUBLIC",)
    assert by_id["q-disc-after-delete"] is False


def test_receipt_as_belief_mutation_is_detected():
    fixture, gold, generic, _ = _systems()
    query = next(query for query in fixture.queries if query.query_id == "q-att-before")
    assert gold.answer(query) == Answer(QueryTarget.ATTITUDE, None)
    assert generic.answer(query) == Answer(QueryTarget.ATTITUDE, None)
    assert Answer(QueryTarget.ATTITUDE, "believe") != gold.answer(query)


def test_target_specific_answers_do_not_overload_fields():
    fixture, gold, *_ = _systems()
    boolean_targets = {
        QueryTarget.DISCLOSE,
        QueryTarget.EVER_EXPOSED,
        QueryTarget.AVAILABLE,
        QueryTarget.WORLD,
    }
    for query in fixture.queries:
        answer = gold.answer(query)
        assert answer.target is query.target
        if query.target in boolean_targets:
            assert answer.value is None or isinstance(answer.value, bool)
        elif query.target is QueryTarget.JUSTIFICATION:
            assert isinstance(answer.value, tuple)
        else:
            assert answer.value is None or isinstance(answer.value, str)
