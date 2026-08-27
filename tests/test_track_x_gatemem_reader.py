from __future__ import annotations

import pytest

from mindmap.track_x.gatemem_baselines import (
    RawLexicalConfig,
    RawLexicalGateMemAgent,
)
from mindmap.track_x.gatemem_public import (
    PublicCheckpoint,
    PublicEpisode,
    PublicPrincipal,
    PublicTurn,
)
from mindmap.track_x.gatemem_reader import (
    ExtractiveReaderConfig,
    ExtractiveReaderResult,
    RawLexicalSharedReaderGateMemAgent,
)


class FakeReader:
    model_id = "fake/reader"
    revision = "f" * 40

    def __init__(self, answer: str) -> None:
        self.output = answer
        self.calls: list[tuple[str, str]] = []

    def answer(self, *, question: str, context: str) -> ExtractiveReaderResult:
        self.calls.append((question, context))
        if not self.output:
            return ExtractiveReaderResult(
                answer="",
                answer_start=None,
                answer_end=None,
                span_score=1.0,
                null_score=2.0,
                score_margin=-1.0,
                diagnostic_probability=0.25,
                window_count=1,
                input_token_count=12,
                forward_calls=1,
            )
        start = context.index(self.output)
        return ExtractiveReaderResult(
            answer=self.output,
            answer_start=start,
            answer_end=start + len(self.output),
            span_score=4.0,
            null_score=1.0,
            score_margin=3.0,
            diagnostic_probability=0.95,
            window_count=1,
            input_token_count=12,
            forward_calls=1,
        )


def _episode() -> PublicEpisode:
    return PublicEpisode(
        episode_id="opaque-episode",
        domain="medical",
        principals=(
            PublicPrincipal(
                principal_id="opaque-p1",
                role="doctor",
                display_name="Dr. A",
            ),
        ),
    )


def _turns() -> tuple[PublicTurn, ...]:
    return (
        PublicTurn(
            turn_id="opaque-t1",
            timestamp="2026-01-01T00:00:00Z",
            speaker_principal_id="opaque-p1",
            speaker_role="doctor",
            turn_kind="dialogue",
            text="The prescribed medicine is amoxicillin.",
        ),
        PublicTurn(
            turn_id="opaque-t2",
            timestamp="2026-01-02T00:00:00Z",
            speaker_principal_id="opaque-p1",
            speaker_role="doctor",
            turn_kind="dialogue",
            text="The follow-up visit is next Tuesday.",
        ),
    )


def _checkpoint() -> PublicCheckpoint:
    return PublicCheckpoint(
        checkpoint_id="opaque-q1",
        episode_id="opaque-episode",
        asker_principal_id="opaque-p1",
        asker_role="doctor",
        query_text="Which medicine was prescribed?",
    )


def _prepare(agent) -> None:
    agent.reset(_episode())
    for turn in _turns():
        agent.ingest(turn)


def test_b1b_preserves_exact_b1a_retrieval_and_prompt_context():
    config = RawLexicalConfig(top_k=2, max_answer_characters=6000)
    baseline = RawLexicalGateMemAgent(config)
    reader = FakeReader("amoxicillin")
    b1b = RawLexicalSharedReaderGateMemAgent(config, reader)
    _prepare(baseline)
    _prepare(b1b)

    baseline_prediction = baseline.query(_checkpoint())
    b1b_prediction = b1b.query(_checkpoint())

    assert (
        b1b_prediction["memory_audit"]["retrieval_items"]
        == baseline_prediction["memory_audit"]["retrieval_items"]
    )
    assert (
        b1b_prediction["memory_audit"]["prompt_items"]
        == baseline_prediction["memory_audit"]["prompt_items"]
    )
    assert (
        b1b_prediction["memory_audit"]["prompt_context"]
        == baseline_prediction["memory_audit"]["prompt_context"]
    )
    assert reader.calls == [
        (
            _checkpoint().query_text,
            baseline_prediction["memory_audit"]["prompt_context"]["text"],
        )
    ]


def test_b1b_emits_reader_span_and_no_gold_record_ids():
    reader = FakeReader("amoxicillin")
    agent = RawLexicalSharedReaderGateMemAgent(
        RawLexicalConfig(top_k=2), reader
    )
    _prepare(agent)
    prediction = agent.query(_checkpoint())

    assert prediction["action"] == "answer"
    assert prediction["answer"] == "amoxicillin"
    assert prediction["used_record_ids"] == []
    assert prediction["answer_structured"]["reader"]["forward_calls"] == 1
    assert (
        prediction["memory_audit"]["reader"]["threshold_is_calibrated"]
        is False
    )


def test_b1b_native_no_answer_abstains_without_hiding_prompt_exposure():
    reader = FakeReader("")
    agent = RawLexicalSharedReaderGateMemAgent(
        RawLexicalConfig(top_k=2), reader
    )
    _prepare(agent)
    prediction = agent.query(_checkpoint())

    assert prediction["action"] == "no_memory"
    assert prediction["answer"] == ""
    assert prediction["memory_audit"]["prompt_context"]["character_count"] > 0
    assert prediction["memory_audit"]["reader"]["score_margin"] == -1.0


def test_reader_config_rejects_unfrozen_or_invalid_budget_values():
    with pytest.raises(ValueError):
        ExtractiveReaderConfig(revision="")
    with pytest.raises(ValueError):
        ExtractiveReaderConfig(max_sequence_length=32)
    with pytest.raises(ValueError):
        ExtractiveReaderConfig(max_sequence_length=128, stride=128)
    with pytest.raises(ValueError):
        ExtractiveReaderConfig(max_answer_tokens=0)
