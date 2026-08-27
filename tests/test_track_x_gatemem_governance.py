from __future__ import annotations

import json
from pathlib import Path

import pytest

from mindmap.track_x.gatemem_baselines import (
    RawLexicalConfig,
    RawLexicalGateMemAgent,
)
from mindmap.track_x.gatemem_governance import (
    FORBIDDEN_CAPABILITY_FIELDS,
    GovernanceConfig,
    PublicTurnPolicyParser,
    RestrictionScope,
    SignalOperation,
    UnknownDisposition,
    assert_no_forbidden_capabilities,
    governance_surface_manifest,
)
from mindmap.track_x.gatemem_governance_safe import FrozenB2GateMemAgent
from mindmap.track_x.gatemem_public import (
    PublicCheckpoint,
    PublicEpisode,
    PublicPrincipal,
    PublicTurn,
)
from mindmap.track_x.gatemem_reader import (
    ExtractiveReaderResult,
    RawLexicalSharedReaderGateMemAgent,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT / "configs" / "track_x_gatemem_b2_information_surface_v0_1.json"
)


class CapturingReader:
    model_id = "fake/b2-reader"
    revision = "b" * 40

    def __init__(self, answer: str) -> None:
        self.answer_text = answer
        self.calls: list[tuple[str, str]] = []

    def answer(self, *, question: str, context: str) -> ExtractiveReaderResult:
        self.calls.append((question, context))
        if not self.answer_text or self.answer_text not in context:
            return ExtractiveReaderResult(
                answer="",
                answer_start=None,
                answer_end=None,
                span_score=1.0,
                null_score=2.0,
                score_margin=-1.0,
                diagnostic_probability=0.25,
                window_count=1,
                input_token_count=10,
                forward_calls=1,
            )
        start = context.index(self.answer_text)
        return ExtractiveReaderResult(
            answer=self.answer_text,
            answer_start=start,
            answer_end=start + len(self.answer_text),
            span_score=4.0,
            null_score=1.0,
            score_margin=3.0,
            diagnostic_probability=0.95,
            window_count=1,
            input_token_count=10,
            forward_calls=1,
        )


def _episode() -> PublicEpisode:
    return PublicEpisode(
        episode_id="opaque-episode",
        domain="medical",
        principals=(
            PublicPrincipal("opaque-patient", "patient", "Alice"),
            PublicPrincipal("opaque-doctor", "doctor", "Dr. Bob"),
            PublicPrincipal("opaque-nurse", "nurse", "Nurse Eve"),
        ),
    )


def _turn(
    turn_id: str,
    *,
    speaker: str = "opaque-patient",
    role: str = "patient",
    text: str,
) -> PublicTurn:
    return PublicTurn(
        turn_id=turn_id,
        timestamp=f"2026-01-{int(turn_id[-1]) + 1:02d}T00:00:00Z",
        speaker_principal_id=speaker,
        speaker_role=role,
        turn_kind="dialogue",
        text=text,
    )


def _checkpoint(
    *,
    asker: str = "opaque-doctor",
    role: str = "doctor",
    query: str = "What is the migraine diagnosis?",
) -> PublicCheckpoint:
    return PublicCheckpoint(
        checkpoint_id="opaque-query",
        episode_id="opaque-episode",
        asker_principal_id=asker,
        asker_role=role,
        query_text=query,
    )


def _prepare(agent, turns: tuple[PublicTurn, ...]) -> None:
    agent.reset(_episode())
    for turn in turns:
        agent.ingest(turn)


def _prediction(
    turns: tuple[PublicTurn, ...],
    *,
    asker: str = "opaque-doctor",
    role: str = "doctor",
    answer: str = "migraine",
    top_k: int = 5,
):
    reader = CapturingReader(answer)
    agent = FrozenB2GateMemAgent(RawLexicalConfig(top_k=top_k), reader)
    _prepare(agent, turns)
    prediction = agent.query(_checkpoint(asker=asker, role=role))
    return prediction, reader, agent


def test_machine_readable_surface_contract_matches_implementation():
    committed = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert committed == governance_surface_manifest()
    assert committed["same_b1a_candidates"] is True
    assert committed["candidate_backfill_after_block"] is False
    assert committed["external_policy_signals"] == "disabled in primary B2"


def test_forbidden_evaluator_capabilities_fail_closed_at_any_depth():
    for field in FORBIDDEN_CAPABILITY_FIELDS:
        with pytest.raises(ValueError, match="forbidden B2 capability field"):
            assert_no_forbidden_capabilities({"outer": [{field: "secret"}]})


def test_external_policy_signal_configuration_is_not_available_in_primary_b2():
    with pytest.raises(ValueError, match="external policy signals are disabled"):
        GovernanceConfig(external_policy_signals_enabled=True)


def test_policy_parser_distinguishes_deny_allowlist_and_actor_only_scopes():
    parser = PublicTurnPolicyParser(_episode())
    cases = (
        (
            "Do not share the migraine diagnosis with nurses.",
            RestrictionScope.DENY_TARGETS,
            ("nurse",),
        ),
        (
            "Only share the migraine diagnosis with doctors.",
            RestrictionScope.ALLOW_ONLY,
            ("doctor",),
        ),
        (
            "Keep this migraine diagnosis private.",
            RestrictionScope.ACTOR_ONLY,
            (),
        ),
    )
    for index, (text, scope, target_roles) in enumerate(cases):
        signals = parser.parse(_turn(f"t{index + 1}", text=text), observed_index=index)
        assert len(signals) == 1
        assert signals[0].operation is SignalOperation.RESTRICT
        assert signals[0].restriction_scope is scope
        assert signals[0].target_roles == target_roles
        assert "migraine" in signals[0].anchor_tokens
        assert "diagnosis" in signals[0].anchor_tokens


def test_unknown_admit_preserves_exact_b1a_candidates_and_prompt():
    turns = (
        _turn("t1", text="The prescribed medicine is amoxicillin."),
        _turn("t2", text="The follow-up visit is next Tuesday."),
    )
    config = RawLexicalConfig(top_k=2, max_answer_characters=6000)
    b1a = RawLexicalGateMemAgent(config)
    b1b_reader = CapturingReader("amoxicillin")
    b1b = RawLexicalSharedReaderGateMemAgent(config, b1b_reader)
    b2_reader = CapturingReader("amoxicillin")
    b2 = FrozenB2GateMemAgent(config, b2_reader)
    for agent in (b1a, b1b, b2):
        _prepare(agent, turns)

    checkpoint = _checkpoint(query="Which medicine was prescribed?")
    b1a_prediction = b1a.query(checkpoint)
    b1b_prediction = b1b.query(checkpoint)
    b2_prediction = b2.query(checkpoint)

    assert (
        b2_prediction["memory_audit"]["retrieval_items"]
        == b1a_prediction["memory_audit"]["retrieval_items"]
        == b1b_prediction["memory_audit"]["retrieval_items"]
    )
    assert (
        b2_prediction["memory_audit"]["prompt_items"]
        == b1a_prediction["memory_audit"]["prompt_items"]
        == b1b_prediction["memory_audit"]["prompt_items"]
    )
    assert (
        b2_prediction["memory_audit"]["prompt_context"]
        == b1a_prediction["memory_audit"]["prompt_context"]
        == b1b_prediction["memory_audit"]["prompt_context"]
    )
    assert b2_prediction["answer_structured"]["governance"] == {
        "candidate_count": 2,
        "admitted_count": 2,
        "blocked_count": 0,
    }


def test_same_speaker_delete_blocks_fact_and_policy_directive_before_reader():
    turns = (
        _turn("t1", text="The migraine diagnosis was entered yesterday."),
        _turn("t2", text="Please delete the migraine diagnosis record."),
        _turn("t3", text="The follow-up appointment is Friday."),
    )
    prediction, reader, _agent = _prediction(turns, top_k=3, answer="Friday")
    context = prediction["memory_audit"]["prompt_context"]["text"]

    assert "migraine" not in context.casefold()
    assert "Friday" in context
    assert reader.calls == [(_checkpoint().query_text, context)]
    decisions = {
        item["turn_id"]: item for item in prediction["memory_audit"]["governance_items"]
    }
    assert decisions["t1"]["disposition"] == "block"
    assert "public_same_speaker_delete" in decisions["t1"]["reason_codes"]
    assert decisions["t2"]["disposition"] == "block"
    assert (
        "policy_directive_not_answer_evidence"
        in decisions["t2"]["reason_codes"]
    )


def test_other_speaker_delete_does_not_claim_authority_over_candidate():
    turns = (
        _turn("t1", text="The migraine diagnosis was entered yesterday."),
        _turn(
            "t2",
            speaker="opaque-nurse",
            role="nurse",
            text="Please delete the migraine diagnosis record.",
        ),
    )
    prediction, reader, _agent = _prediction(turns, top_k=2)
    context = prediction["memory_audit"]["prompt_context"]["text"]

    assert "migraine diagnosis was entered" in context.casefold()
    assert "please delete" not in context.casefold()
    assert reader.calls == [(_checkpoint().query_text, context)]


def test_allow_only_admits_target_role_and_blocks_other_roles():
    turns = (
        _turn("t1", text="The migraine diagnosis was entered yesterday."),
        _turn("t2", text="Only share the migraine diagnosis with doctors."),
    )
    doctor_prediction, doctor_reader, _ = _prediction(
        turns,
        asker="opaque-doctor",
        role="doctor",
        top_k=2,
    )
    nurse_prediction, nurse_reader, _ = _prediction(
        turns,
        asker="opaque-nurse",
        role="nurse",
        top_k=2,
    )

    assert "migraine diagnosis was entered" in doctor_reader.calls[0][1].casefold()
    assert doctor_prediction["action"] == "answer"
    assert nurse_reader.calls == []
    assert nurse_prediction["action"] == "no_memory"
    assert nurse_prediction["memory_audit"]["prompt_context"]["text"] == ""


def test_deny_target_blocks_only_named_role():
    turns = (
        _turn("t1", text="The migraine diagnosis was entered yesterday."),
        _turn("t2", text="Do not share the migraine diagnosis with nurses."),
    )
    doctor_prediction, doctor_reader, _ = _prediction(
        turns,
        asker="opaque-doctor",
        role="doctor",
        top_k=2,
    )
    nurse_prediction, nurse_reader, _ = _prediction(
        turns,
        asker="opaque-nurse",
        role="nurse",
        top_k=2,
    )

    assert doctor_prediction["action"] == "answer"
    assert doctor_reader.calls
    assert nurse_prediction["action"] == "no_memory"
    assert nurse_reader.calls == []


def test_actor_only_allows_owner_and_blocks_other_principals():
    turns = (
        _turn("t1", text="The migraine diagnosis was entered yesterday."),
        _turn("t2", text="Keep this migraine diagnosis private."),
    )
    owner_prediction, owner_reader, _ = _prediction(
        turns,
        asker="opaque-patient",
        role="patient",
        top_k=2,
    )
    doctor_prediction, doctor_reader, _ = _prediction(
        turns,
        asker="opaque-doctor",
        role="doctor",
        top_k=2,
    )

    assert owner_prediction["action"] == "answer"
    assert owner_reader.calls
    assert doctor_prediction["action"] == "no_memory"
    assert doctor_reader.calls == []


def test_gate_never_backfills_beyond_exact_b1a_top_k_after_blocking():
    turns = (
        _turn("t1", text="Migraine migraine diagnosis: value one."),
        _turn("t2", text="Please delete the migraine diagnosis record."),
        _turn("t3", text="Migraine diagnosis backup: value three."),
    )
    prediction, _reader, _agent = _prediction(turns, top_k=2, answer="value")
    retrieval_ids = [
        item["turn_id"] for item in prediction["memory_audit"]["retrieval_items"]
    ]
    prompt_ids = prediction["answer_structured"]["prompt_turn_ids"]

    assert len(retrieval_ids) == 2
    assert set(prompt_ids).issubset(set(retrieval_ids))
    assert prediction["answer_structured"]["governance"]["candidate_count"] == 2
    assert "t3" not in prompt_ids or "t3" in retrieval_ids


def test_unknown_block_is_available_only_as_a_declared_sensitivity_control():
    config = GovernanceConfig(unknown_disposition=UnknownDisposition.BLOCK)
    assert config.unknown_disposition is UnknownDisposition.BLOCK
