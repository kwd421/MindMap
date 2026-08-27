from __future__ import annotations

from mindmap.track_x.gatemem_baselines import RawLexicalConfig
from mindmap.track_x.gatemem_governance import PublicTurnPolicyParser, SignalOperation
from mindmap.track_x.gatemem_governance_safe import FrozenB2GateMemAgent
from mindmap.track_x.gatemem_public import (
    PublicCheckpoint,
    PublicEpisode,
    PublicPrincipal,
    PublicTurn,
)
from mindmap.track_x.gatemem_reader import ExtractiveReaderResult


class Reader:
    model_id = "review/fake-reader"
    revision = "c" * 40

    def __init__(self) -> None:
        self.calls: list[str] = []

    def answer(self, *, question: str, context: str) -> ExtractiveReaderResult:
        self.calls.append(context)
        return ExtractiveReaderResult(
            answer="stitches" if "stitches" in context.casefold() else "",
            answer_start=4 if "stitches" in context.casefold() else None,
            answer_end=12 if "stitches" in context.casefold() else None,
            span_score=1.0,
            null_score=0.0,
            score_margin=1.0,
            diagnostic_probability=0.9,
            window_count=1,
            input_token_count=len(context.split()),
            forward_calls=1,
        )


def episode() -> PublicEpisode:
    return PublicEpisode(
        episode_id="opaque-e",
        domain="medical",
        principals=(
            PublicPrincipal("opaque-patient", "patient", "Alice"),
            PublicPrincipal("opaque-doctor", "doctor", "Dr. Bob"),
        ),
    )


def turn(turn_id: str, text: str) -> PublicTurn:
    return PublicTurn(
        turn_id=turn_id,
        timestamp="2026-01-01T00:00:00Z",
        speaker_principal_id="opaque-patient",
        speaker_role="patient",
        turn_kind="dialogue",
        text=text,
    )


def test_explicit_record_deletion_still_emits_delete() -> None:
    signals = PublicTurnPolicyParser(episode()).parse(
        turn("t1", "Please delete the migraine diagnosis record."),
        observed_index=1,
    )
    assert len(signals) == 1
    assert signals[0].operation is SignalOperation.DELETE


def test_physical_remove_and_wipe_are_not_memory_deletion_signals() -> None:
    parser = PublicTurnPolicyParser(episode())
    assert parser.parse(
        turn("t1", "Please remove the stitches tomorrow."), observed_index=1
    ) == ()
    assert parser.parse(
        turn("t2", "Please wipe the table before dinner."), observed_index=2
    ) == ()


def test_physical_remove_does_not_block_prior_fact() -> None:
    reader = Reader()
    agent = FrozenB2GateMemAgent(RawLexicalConfig(top_k=5), reader)
    agent.reset(episode())
    agent.ingest(turn("t1", "The stitches are scheduled for removal tomorrow."))
    agent.ingest(turn("t2", "Please remove the stitches tomorrow."))
    prediction = agent.query(
        PublicCheckpoint(
            checkpoint_id="opaque-q",
            episode_id="opaque-e",
            asker_principal_id="opaque-doctor",
            asker_role="doctor",
            query_text="What is scheduled for removal tomorrow?",
        )
    )
    context = prediction["memory_audit"]["prompt_context"]["text"].casefold()
    assert "stitches are scheduled for removal" in context
    assert not agent.governance_signals
    assert reader.calls
