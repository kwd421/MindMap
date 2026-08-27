from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import re

from .gatemem_baselines import RawLexicalConfig
from .gatemem_governance import (
    CandidateDecision,
    GateDisposition,
    GovernanceConfig,
    GovernanceEvaluation,
    GovernanceSignal,
    GovernanceSurface,
    PublicTextGovernanceGate,
    PublicTurnPolicyParser,
    RawLexicalGovernedReaderGateMemAgent,
    RestrictionScope,
    SignalOperation,
)
from .gatemem_public import PublicEpisode, PublicTurn
from .gatemem_reader import ExtractiveReader


FROZEN_B2_DELETION_CAPABILITY_SCHEMA = (
    "track-x-gatemem-b2-deletion-capability-v0.1"
)

# Capability-boundary route chosen before any public B2 result:
# Active Forgetting requires an explicit information/memory referent. Natural
# referent-less requests such as "forget the diagnosis" are outside v0.9
# capability and must be reported as incomplete deletion-language recall.
_INFORMATION_REFERENT = (
    r"(?:memory|memories|record|records|data|information|details|"
    r"conversation|conversations|message|messages|note|notes|history)"
)
_FROZEN_DELETE_RE = re.compile(
    rf"(?:\b(?:delete|forget|erase|remove|purge|wipe)\b.{{0,200}}?"
    rf"\b{_INFORMATION_REFERENT}\b|"
    rf"\b{_INFORMATION_REFERENT}\b.{{0,200}}?"
    rf"\b(?:delete|forget|erase|remove|purge|wipe)\b)",
    flags=re.IGNORECASE,
)
_FROZEN_DENY_TARGET_RE = re.compile(
    r"\b(?:do\s+not\s+share|don't\s+share|must\s+not\s+share|"
    r"do\s+not\s+disclose|don't\s+disclose)\b",
    flags=re.IGNORECASE,
)
_FROZEN_ALLOW_ONLY_RE = re.compile(
    r"\bonly\s+share\b.{0,200}?\bwith\b",
    flags=re.IGNORECASE,
)
_FROZEN_ACTOR_ONLY_RE = re.compile(
    r"(?:\bkeep\b.{0,200}?\b(?:private|confidential)\b|"
    r"\bthis\b.{0,200}?\bis\s+(?:private|confidential)\b)",
    flags=re.IGNORECASE,
)
_FROZEN_GRANT_RE = re.compile(
    r"(?:\b(?:may|can)\s+share\b.{0,200}?\bwith\b|"
    r"\ballow\w*\s+.+?\s+to\s+(?:access|see|read)\b|"
    r"\bauthori[sz]e\w*\s+.+?\s+to\s+(?:access|see|read)\b)",
    flags=re.IGNORECASE,
)


def deletion_capability_manifest() -> dict[str, object]:
    return {
        "schema_version": FROZEN_B2_DELETION_CAPABILITY_SCHEMA,
        "route": "capability-boundary",
        "recognized": (
            "deletion verb and explicit information/memory referent in the same "
            "observed public turn"
        ),
        "information_referents": [
            "memory",
            "memories",
            "record",
            "records",
            "data",
            "information",
            "details",
            "conversation",
            "conversations",
            "message",
            "messages",
            "note",
            "notes",
            "history",
        ],
        "outside_capability": [
            "referent-less forget <fact> requests",
            "implicit or deictic deletion without an information referent",
            "ordinary physical/domain remove or wipe actions",
        ],
        "expected_consequence": (
            "Active-Forgetting recall is incomplete; public B2 must retain and "
            "report this limitation without post-outcome grammar tuning"
        ),
    }


class FrozenPublicTurnPolicyParser(PublicTurnPolicyParser):
    """Instance-owned v0.9 grammar, independent of import order."""

    def parse(
        self,
        turn: PublicTurn,
        *,
        observed_index: int,
    ) -> tuple[GovernanceSignal, ...]:
        text = turn.text
        operations: list[tuple[SignalOperation, RestrictionScope]] = []
        if _FROZEN_DELETE_RE.search(text):
            operations.append((SignalOperation.DELETE, RestrictionScope.NONE))

        if _FROZEN_ALLOW_ONLY_RE.search(text):
            operations.append(
                (SignalOperation.RESTRICT, RestrictionScope.ALLOW_ONLY)
            )
        elif _FROZEN_DENY_TARGET_RE.search(text):
            operations.append(
                (SignalOperation.RESTRICT, RestrictionScope.DENY_TARGETS)
            )
        elif _FROZEN_ACTOR_ONLY_RE.search(text):
            operations.append(
                (SignalOperation.RESTRICT, RestrictionScope.ACTOR_ONLY)
            )

        # "only share with" is an allow-list restriction, not an independent grant.
        if _FROZEN_GRANT_RE.search(text) and not _FROZEN_ALLOW_ONLY_RE.search(text):
            operations.append((SignalOperation.GRANT, RestrictionScope.NONE))
        if not operations:
            return ()

        target_principal_ids, target_roles = self._targets(text)
        anchors = self._anchor_tokens(text)
        digest = sha256(text.encode("utf-8")).hexdigest()
        signals: list[GovernanceSignal] = []
        for ordinal, (operation, scope) in enumerate(operations):
            signals.append(
                GovernanceSignal(
                    signal_id=self._signal_id(
                        turn,
                        operation,
                        scope,
                        ordinal,
                    ),
                    operation=operation,
                    restriction_scope=scope,
                    actor_principal_id=turn.speaker_principal_id,
                    actor_role=turn.speaker_role,
                    observed_index=observed_index,
                    source_public_turn_id=turn.turn_id,
                    target_principal_ids=target_principal_ids,
                    target_roles=target_roles,
                    anchor_tokens=anchors,
                    source_text_sha256=digest,
                )
            )
        return tuple(signals)


class PolicySourceBlockingGovernanceGate(PublicTextGovernanceGate):
    """Whole-turn B2 gate that never sends policy directives to the reader.

    Public policy turns can repeat the protected or deleted fact. The v0.9
    mechanism has no span-level redaction, so admitting those turns would let a
    deletion/restriction instruction become answer evidence. Blocking the full
    directive is conservative and is reported as a potential utility cost.
    """

    def evaluate(self, surface: GovernanceSurface) -> GovernanceEvaluation:
        base = super().evaluate(surface)
        signals_by_source: dict[str, list[str]] = {}
        for signal in surface.signals:
            signals_by_source.setdefault(signal.source_public_turn_id, []).append(
                signal.signal_id
            )

        decisions: list[CandidateDecision] = []
        for decision in base.decisions:
            source_signals = signals_by_source.get(decision.turn_id)
            if not source_signals:
                decisions.append(decision)
                continue
            decisions.append(
                replace(
                    decision,
                    disposition=GateDisposition.BLOCK,
                    reason_codes=tuple(
                        dict.fromkeys(
                            (
                                "policy_directive_not_answer_evidence",
                                *decision.reason_codes,
                            )
                        )
                    ),
                    matched_signal_ids=tuple(
                        dict.fromkeys(
                            (*decision.matched_signal_ids, *source_signals)
                        )
                    ),
                )
            )
        return GovernanceEvaluation(decisions=tuple(decisions))


class FrozenB2GateMemAgent(RawLexicalGovernedReaderGateMemAgent):
    """The only agent admitted by the frozen v0.9 B2 primary contract."""

    def __init__(
        self,
        lexical_config: RawLexicalConfig | None,
        reader: ExtractiveReader,
        governance_config: GovernanceConfig | None = None,
    ) -> None:
        super().__init__(lexical_config, reader, governance_config)
        self._governance_gate = PolicySourceBlockingGovernanceGate(
            self.governance_config
        )

    def reset(self, episode: PublicEpisode) -> None:
        super().reset(episode)
        self._policy_parser = FrozenPublicTurnPolicyParser(episode)
