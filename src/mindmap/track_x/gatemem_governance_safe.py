from __future__ import annotations

from dataclasses import replace
import re

from . import gatemem_governance as _base_governance
from .gatemem_baselines import RawLexicalConfig
from .gatemem_governance import (
    CandidateDecision,
    GateDisposition,
    GovernanceConfig,
    GovernanceEvaluation,
    GovernanceSurface,
    PublicTextGovernanceGate,
    RawLexicalGovernedReaderGateMemAgent,
)
from .gatemem_reader import ExtractiveReader


# The base parser resolves these module-level patterns at call time. The frozen
# agent widens only phrase shape (not labels, thresholds, or target semantics)
# so ordinary public prose may place the protected topic between the policy
# verb and its target/scope.
_base_governance._ALLOW_ONLY_RE = re.compile(
    r"\bonly\s+share\b.{0,200}?\bwith\b",
    flags=re.IGNORECASE,
)
_base_governance._ACTOR_ONLY_RE = re.compile(
    r"(?:\bkeep\b.{0,200}?\b(?:private|confidential)\b|"
    r"\bthis\b.{0,200}?\bis\s+(?:private|confidential)\b)",
    flags=re.IGNORECASE,
)
_base_governance._GRANT_RE = re.compile(
    r"(?:\b(?:may|can)\s+share\b.{0,200}?\bwith\b|"
    r"\ballow\w*\s+.+?\s+to\s+(?:access|see|read)\b|"
    r"\bauthori[sz]e\w*\s+.+?\s+to\s+(?:access|see|read)\b)",
    flags=re.IGNORECASE,
)

# G3 review prototype: distinguish an information/memory erasure speech act
# from an ordinary domain action that happens to use verbs such as `remove` or
# `wipe`.  `forget` is intrinsically cognitive; the other destructive verbs
# require a nearby data/memory referent in either order.  This is deliberately
# conservative: unknown/ambiguous cases remain under the frozen unknown-admit
# policy rather than manufacturing a false deletion signal.
_MEMORY_REFERENT = (
    r"(?:mem(?:ory|ories)|record(?:s)?|data|information|details?|"
    r"conversation(?:s)?|message(?:s)?|note(?:s)?|history|"
    r"profile|entr(?:y|ies))"
)
_DESTRUCTIVE_VERB = r"(?:delete|erase|purge|wipe|remove)"
_base_governance._DELETE_RE = re.compile(
    rf"(?:\bforget\b|"
    rf"\b{_DESTRUCTIVE_VERB}\b.{{0,160}}?\b{_MEMORY_REFERENT}\b|"
    rf"\b{_MEMORY_REFERENT}\b.{{0,160}}?\b{_DESTRUCTIVE_VERB}\b)",
    flags=re.IGNORECASE,
)


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
