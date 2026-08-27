from __future__ import annotations

from mindmap.track_x.gatemem_baselines import RawLexicalConfig
from mindmap.track_x.gatemem_governance import SignalOperation
from mindmap.track_x.gatemem_governance_safe import (
    FrozenB2GateMemAgent,
    FrozenPublicTurnPolicyParser,
    deletion_capability_manifest,
)
from mindmap.track_x.gatemem_public import (
    PublicCheckpoint,
    PublicEpisode,
    PublicPrincipal,
    PublicTurn,
)
from mindmap.track_x.gatemem_reader import ExtractiveReaderResult


class CapturingReader:
    model_id = "deterministic/speech-act-reader"
    revision = "c" * 40

    def __init__(self) -> None:
        self.contexts: list[str] = []

    def answer(self, *, question: str, context: str) -> ExtractiveReaderResult:
        self.contexts.append(context)
        return ExtractiveReaderResult(
            answer="stitches" if "stitches" in context.casefold() else "",
            answer_start=4 if "stitches" in context.casefold() else None,
            answer_end=12 if "stitches" in context.casefold() else None,
            span_score=2.0,
            null_score=0.0,
            score_margin=2.0,
            diagnostic_probability=0.9,
            window_count=1,
            input_token_count=len(context.split()),
            forward_calls=1,
        )


def _episode() -> PublicEpisode:
    return PublicEpisode(
        episode_id="opaque-episode",
        domain="medical",
        principals=(
            PublicPrincipal("opaque-patient", "patient", "Alice"),
            PublicPrincipal("opaque-doctor", "doctor", "Dr. Bob"),
        ),
    )


def _turn(turn_id: str, text: str) -> PublicTurn:
    return PublicTurn(
        turn_id=turn_id,
        timestamp=f"2026-01-0{int(turn_id[-1]) + 1}T00:00:00Z",
        speaker_principal_id="opaque-patient",
        speaker_role="patient",
        turn_kind="dialogue",
        text=text,
    )


def test_explicit_information_record_deletion_emits_delete_signal():
    parser = FrozenPublicTurnPolicyParser(_episode())
    signals = parser.parse(
        _turn("t1", "Please delete the migraine diagnosis record."),
        observed_index=0,
    )
    assert len(signals) == 1
    assert signals[0].operation is SignalOperation.DELETE
    assert {"migraine", "diagnosis"}.issubset(signals[0].anchor_tokens)


def test_remove_stitches_is_not_active_forgetting():
    parser = FrozenPublicTurnPolicyParser(_episode())
    assert (
        parser.parse(
            _turn("t1", "Please remove the stitches tomorrow."),
            observed_index=0,
        )
        == ()
    )


def test_wipe_table_is_not_active_forgetting():
    parser = FrozenPublicTurnPolicyParser(_episode())
    assert (
        parser.parse(
            _turn("t1", "Please wipe the table."),
            observed_index=0,
        )
        == ()
    )


def test_referentless_forget_fact_is_explicitly_outside_v09_capability():
    parser = FrozenPublicTurnPolicyParser(_episode())
    assert (
        parser.parse(
            _turn("t1", "Please forget the migraine diagnosis."),
            observed_index=0,
        )
        == ()
    )
    assert (
        parser.parse(
            _turn("t2", "Forget that Alice has migraines."),
            observed_index=1,
        )
        == ()
    )


def test_deletion_capability_route_is_machine_readable_and_incomplete():
    manifest = deletion_capability_manifest()
    assert manifest["route"] == "capability-boundary"
    assert "referent-less forget <fact> requests" in manifest["outside_capability"]
    assert "incomplete" in str(manifest["expected_consequence"])


def test_ordinary_remove_action_does_not_block_prior_fact():
    reader = CapturingReader()
    agent = FrozenB2GateMemAgent(RawLexicalConfig(top_k=2), reader)
    agent.reset(_episode())
    agent.ingest(_turn("t1", "The stitches are scheduled for removal tomorrow."))
    agent.ingest(_turn("t2", "Please remove the stitches tomorrow."))

    prediction = agent.query(
        PublicCheckpoint(
            checkpoint_id="opaque-query",
            episode_id="opaque-episode",
            asker_principal_id="opaque-doctor",
            asker_role="doctor",
            query_text="What is scheduled for removal tomorrow?",
        )
    )

    assert agent.governance_signals == ()
    assert reader.contexts
    assert "stitches are scheduled for removal" in reader.contexts[0].casefold()
    decisions = {
        item["turn_id"]: item
        for item in prediction["memory_audit"]["governance_items"]
    }
    assert decisions["t1"]["disposition"] == "admit"
    assert "public_same_speaker_delete" not in decisions["t1"]["reason_codes"]
