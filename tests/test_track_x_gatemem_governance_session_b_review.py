from __future__ import annotations

from mindmap.track_x.gatemem_baselines import RawLexicalConfig
from mindmap.track_x.gatemem_governance_safe import FrozenB2GateMemAgent
from mindmap.track_x.gatemem_public import (
    PublicCheckpoint,
    PublicEpisode,
    PublicPrincipal,
    PublicTurn,
)
from mindmap.track_x.gatemem_reader import ExtractiveReaderResult


class ReviewReader:
    model_id = "review/fake-reader"
    revision = "b" * 40

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def answer(self, *, question: str, context: str) -> ExtractiveReaderResult:
        self.calls.append((question, context))
        answer = "migraine" if "migraine" in context.casefold() else "stitches" if "stitches" in context.casefold() else ""
        start = context.casefold().find(answer) if answer else -1
        return ExtractiveReaderResult(
            answer=answer,
            answer_start=start if answer else None,
            answer_end=start + len(answer) if answer else None,
            span_score=2.0 if answer else None,
            null_score=0.0 if answer else None,
            score_margin=2.0 if answer else None,
            diagnostic_probability=0.9 if answer else None,
            window_count=1 if context else 0,
            input_token_count=len(context.split()),
            forward_calls=1 if context else 0,
        )


def episode() -> PublicEpisode:
    return PublicEpisode(
        episode_id="opaque-episode",
        domain="medical",
        principals=(
            PublicPrincipal("opaque-patient", "patient", "Alice"),
            PublicPrincipal("opaque-doctor", "doctor", "Dr. Bob"),
            PublicPrincipal("opaque-nurse", "nurse", "Nurse Eve"),
        ),
    )


def turn(turn_id: str, text: str) -> PublicTurn:
    return PublicTurn(
        turn_id=turn_id,
        timestamp=f"2026-01-0{int(turn_id[-1]) + 1}T00:00:00Z",
        speaker_principal_id="opaque-patient",
        speaker_role="patient",
        turn_kind="dialogue",
        text=text,
    )


def checkpoint(*, asker: str = "opaque-doctor", role: str = "doctor", query: str) -> PublicCheckpoint:
    return PublicCheckpoint(
        checkpoint_id="opaque-query",
        episode_id="opaque-episode",
        asker_principal_id=asker,
        asker_role=role,
        query_text=query,
    )


def run(turns: tuple[PublicTurn, ...], *, asker: str = "opaque-doctor", role: str = "doctor", query: str):
    reader = ReviewReader()
    agent = FrozenB2GateMemAgent(RawLexicalConfig(top_k=5), reader)
    agent.reset(episode())
    for item in turns:
        agent.ingest(item)
    prediction = agent.query(checkpoint(asker=asker, role=role, query=query))
    return prediction, reader, agent


def test_deictic_unscoped_deny_is_not_silently_bound_to_every_prior_memory() -> None:
    prediction, _reader, agent = run(
        (
            turn("t1", "The migraine diagnosis was entered yesterday."),
            turn("t2", "Do not share this."),
        ),
        query="What is the migraine diagnosis?",
    )
    prompt = prediction["memory_audit"]["prompt_context"]["text"].casefold()

    # A deictic directive with no target/topic grounding is non-identifiable in
    # the frozen raw surface. It must not be silently treated as a global revoke.
    assert "migraine diagnosis was entered" in prompt
    assert "do not share this" not in prompt
    assert agent.governance_signals


def test_primary_contract_is_explicitly_retrospective_not_prospective() -> None:
    prediction, _reader, _agent = run(
        (
            turn("t1", "Only share the migraine diagnosis with doctors."),
            turn("t2", "The migraine diagnosis was entered yesterday."),
        ),
        asker="opaque-nurse",
        role="nurse",
        query="What is the migraine diagnosis?",
    )
    prompt = prediction["memory_audit"]["prompt_context"]["text"].casefold()

    # Current B2-v0.1 semantics are retrospective-only: a policy uttered before
    # a later fact does not claim authority over that later fact. This test is a
    # boundary test, not an endorsement of general policy semantics.
    assert "migraine diagnosis was entered" in prompt
    assert "only share" not in prompt


def test_physical_remove_is_not_misclassified_as_memory_deletion() -> None:
    prediction, _reader, agent = run(
        (
            turn("t1", "The stitches are scheduled for removal tomorrow."),
            turn("t2", "Please remove the stitches tomorrow."),
        ),
        query="What is scheduled for removal tomorrow?",
    )
    prompt = prediction["memory_audit"]["prompt_context"]["text"].casefold()

    # A physical/domain action must not become Active Forgetting merely because
    # it contains a lexical deletion verb. A valid memory-erasure signal needs
    # an explicit memory/data/information referent in the frozen B2 contract.
    assert "stitches are scheduled for removal" in prompt
    assert not agent.governance_signals
