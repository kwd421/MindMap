from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from enum import StrEnum
from hashlib import sha256
import json
import re
from typing import Any

from .gatemem_baselines import LexicalHit, RawLexicalConfig
from .gatemem_public import PublicCheckpoint, PublicEpisode, PublicPrincipal, PublicTurn
from .gatemem_reader import (
    ExtractiveReader,
    ExtractiveReaderResult,
    RawLexicalSharedReaderGateMemAgent,
)


B2_SURFACE_SCHEMA_VERSION = "track-x-gatemem-b2-information-surface-v0.1"
B2_METHOD_NAME = "raw_bm25_public_text_governance_shared_reader"

# Exact evaluator-only capabilities that must never cross the B2 method boundary.
FORBIDDEN_CAPABILITY_FIELDS = frozenset(
    {
        "query_type",
        "expected_action",
        "judge_spec",
        "leak_targets",
        "relationships",
        "records",
        "record_refs",
        "memory_ops",
        "gold_records",
        "gold_record_ids",
        "source_checkpoint_id",
        "source_episode_id",
        "source_turn_id",
        "as_of_turn_id",
        "future_turns",
        "label",
        "labels",
    }
)

_TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)
_DELETE_RE = re.compile(
    r"\b(?:delete|forget|erase|remove|purge|wipe)\b", flags=re.IGNORECASE
)
_RESTRICT_RE = re.compile(
    r"\b(?:do\s+not\s+share|don't\s+share|must\s+not\s+share|"
    r"do\s+not\s+disclose|don't\s+disclose|keep\s+(?:this|that|it)?\s*private|"
    r"keep\s+(?:this|that|it)?\s*confidential|only\s+share\s+with)\b",
    flags=re.IGNORECASE,
)
_GRANT_RE = re.compile(
    r"\b(?:may\s+share\s+with|can\s+share\s+with|"
    r"allow\w*\s+.+?\s+to\s+(?:access|see|read)|"
    r"authori[sz]e\w*\s+.+?\s+to\s+(?:access|see|read))\b",
    flags=re.IGNORECASE,
)
_ONLY_SHARE_RE = re.compile(r"\bonly\s+share\s+with\b", flags=re.IGNORECASE)
_PRIVATE_RE = re.compile(r"\b(?:private|confidential)\b", flags=re.IGNORECASE)

_POLICY_WORDS = frozenset(
    {
        "delete",
        "deleted",
        "deleting",
        "forget",
        "forgotten",
        "erase",
        "remove",
        "purge",
        "wipe",
        "share",
        "shared",
        "disclose",
        "private",
        "confidential",
        "only",
        "allow",
        "allowed",
        "authorize",
        "authorized",
        "access",
        "read",
        "see",
        "must",
        "not",
        "dont",
        "do",
        "please",
        "this",
        "that",
        "it",
        "with",
        "from",
        "about",
        "memory",
        "record",
        "information",
        "details",
    }
)
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "if",
        "then",
        "to",
        "of",
        "for",
        "in",
        "on",
        "at",
        "by",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "i",
        "we",
        "you",
        "he",
        "she",
        "they",
        "them",
        "my",
        "our",
        "your",
        "his",
        "her",
        "their",
        "me",
        "us",
    }
)


class SignalOperation(StrEnum):
    DELETE = "delete"
    RESTRICT = "restrict"
    GRANT = "grant"


class GateDisposition(StrEnum):
    ADMIT = "admit"
    BLOCK = "block"


class UnknownDisposition(StrEnum):
    ADMIT = "admit"
    BLOCK = "block"


@dataclass(frozen=True, slots=True)
class GovernanceConfig:
    """Pre-outcome B2 policy fixed before any public benchmark result.

    The primary condition admits candidates when no public policy assertion can
    be linked to them. This avoids turning B2 into an always-refuse baseline.
    External policy signals are deliberately disabled because the pinned raw
    GateMem condition exposes no evaluator-independent authenticated policy API.
    """

    unknown_disposition: UnknownDisposition = UnknownDisposition.ADMIT
    minimum_anchor_overlap: int = 1
    same_speaker_authority_only: bool = True
    deletion_is_terminal: bool = True
    external_policy_signals_enabled: bool = False

    def __post_init__(self) -> None:
        if self.minimum_anchor_overlap < 0:
            raise ValueError("minimum_anchor_overlap must be non-negative")
        if self.external_policy_signals_enabled:
            raise ValueError(
                "external policy signals are disabled in the frozen B2 primary condition"
            )


@dataclass(frozen=True, slots=True)
class GovernanceQuery:
    asker_principal_id: str
    asker_role: str
    query_text: str


@dataclass(frozen=True, slots=True)
class GovernanceCandidate:
    turn_id: str
    speaker_principal_id: str
    speaker_role: str
    timestamp: str | None
    turn_kind: str
    text: str
    ingest_index: int
    rank: int
    lexical_score: float
    recency_score: float
    final_score: float


@dataclass(frozen=True, slots=True)
class GovernanceSignal:
    signal_id: str
    operation: SignalOperation
    actor_principal_id: str
    actor_role: str
    observed_index: int
    source_public_turn_id: str
    target_principal_ids: tuple[str, ...]
    target_roles: tuple[str, ...]
    deny_all_others: bool
    anchor_tokens: tuple[str, ...]
    source_text_sha256: str
    source_kind: str = "public_turn_assertion"


@dataclass(frozen=True, slots=True)
class CandidateDecision:
    turn_id: str
    rank: int
    disposition: GateDisposition
    reason_codes: tuple[str, ...]
    matched_signal_ids: tuple[str, ...]
    anchor_overlap: int


@dataclass(frozen=True, slots=True)
class GovernanceSurface:
    principals: tuple[PublicPrincipal, ...]
    query: GovernanceQuery
    candidates: tuple[GovernanceCandidate, ...]
    signals: tuple[GovernanceSignal, ...]
    observed_turn_count: int


@dataclass(frozen=True, slots=True)
class GovernanceEvaluation:
    decisions: tuple[CandidateDecision, ...]

    @property
    def admitted_turn_ids(self) -> tuple[str, ...]:
        return tuple(
            decision.turn_id
            for decision in self.decisions
            if decision.disposition is GateDisposition.ADMIT
        )

    @property
    def blocked_turn_ids(self) -> tuple[str, ...]:
        return tuple(
            decision.turn_id
            for decision in self.decisions
            if decision.disposition is GateDisposition.BLOCK
        )


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(token.casefold() for token in _TOKEN_RE.findall(text))


def _strict_json(value: Any) -> Any:
    try:
        return json.loads(
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("B2 governance surface must be strict JSON") from exc


def assert_no_forbidden_capabilities(value: Any) -> None:
    """Fail closed if evaluator-only names enter the deployable B2 surface."""

    if is_dataclass(value):
        assert_no_forbidden_capabilities(asdict(value))
        return
    if isinstance(value, Mapping):
        for raw_key, item in value.items():
            key = str(raw_key)
            if key in FORBIDDEN_CAPABILITY_FIELDS:
                raise ValueError(f"forbidden B2 capability field: {key}")
            assert_no_forbidden_capabilities(item)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            assert_no_forbidden_capabilities(item)
        return
    _strict_json(value)


def governance_surface_manifest() -> dict[str, Any]:
    """Machine-readable manifest checked against the committed JSON contract."""

    def names(cls: type[Any]) -> list[str]:
        return [field.name for field in fields(cls)]

    manifest = {
        "schema_version": B2_SURFACE_SCHEMA_VERSION,
        "primary_condition": "public-turn-text-derived-governance",
        "allowed_inputs": {
            "PublicPrincipal": names(PublicPrincipal),
            "GovernanceQuery": names(GovernanceQuery),
            "GovernanceCandidate": names(GovernanceCandidate),
            "GovernanceSignal": names(GovernanceSignal),
            "GovernanceSurface": names(GovernanceSurface),
        },
        "forbidden_fields": sorted(FORBIDDEN_CAPABILITY_FIELDS),
        "chronology": "incremental ingest order only; no future turns or source as-of ID",
        "external_policy_signals": "disabled in primary B2",
        "default_unknown_disposition": UnknownDisposition.ADMIT.value,
        "same_b1a_candidates": True,
        "candidate_backfill_after_block": False,
        "reader": "same frozen B1b reader and token/call budget",
    }
    assert_no_forbidden_capabilities(manifest["allowed_inputs"])
    return manifest


class PublicTurnPolicyParser:
    """Extract auditable policy assertions from observed public dialogue only."""

    def __init__(self, episode: PublicEpisode) -> None:
        self.episode = episode
        self._principal_aliases: dict[str, set[str]] = {}
        self._role_aliases: dict[str, set[str]] = {}
        for principal in episode.principals:
            aliases = {principal.role.casefold()}
            if principal.display_name:
                aliases.add(principal.display_name.casefold())
            self._principal_aliases[principal.principal_id] = aliases
            self._role_aliases.setdefault(principal.role.casefold(), set()).add(
                principal.principal_id
            )

    def _targets(self, text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
        lowered = text.casefold()
        principal_ids = {
            principal_id
            for principal_id, aliases in self._principal_aliases.items()
            if any(alias and re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", lowered) for alias in aliases)
        }
        roles = {
            role
            for role in self._role_aliases
            if role and re.search(rf"(?<!\w){re.escape(role)}s?(?!\w)", lowered)
        }
        return tuple(sorted(principal_ids)), tuple(sorted(roles))

    def _anchor_tokens(self, text: str) -> tuple[str, ...]:
        aliases = {
            token
            for alias_set in self._principal_aliases.values()
            for alias in alias_set
            for token in _tokens(alias)
        }
        output = {
            token
            for token in _tokens(text)
            if len(token) >= 3
            and token not in _POLICY_WORDS
            and token not in _STOPWORDS
            and token not in aliases
        }
        return tuple(sorted(output))

    @staticmethod
    def _signal_id(turn: PublicTurn, operation: SignalOperation, ordinal: int) -> str:
        payload = (
            f"{turn.turn_id}\0{operation.value}\0{ordinal}\0{turn.text}"
        ).encode("utf-8")
        return "sig_" + sha256(payload).hexdigest()[:24]

    def parse(self, turn: PublicTurn, *, observed_index: int) -> tuple[GovernanceSignal, ...]:
        text = turn.text
        operations: list[tuple[SignalOperation, bool]] = []
        if _DELETE_RE.search(text):
            operations.append((SignalOperation.DELETE, False))
        if _RESTRICT_RE.search(text) or _PRIVATE_RE.search(text):
            operations.append(
                (
                    SignalOperation.RESTRICT,
                    bool(_ONLY_SHARE_RE.search(text) or _PRIVATE_RE.search(text)),
                )
            )
        if _GRANT_RE.search(text):
            operations.append((SignalOperation.GRANT, False))
        if not operations:
            return ()

        target_principal_ids, target_roles = self._targets(text)
        anchors = self._anchor_tokens(text)
        digest = sha256(text.encode("utf-8")).hexdigest()
        signals = []
        for ordinal, (operation, deny_all_others) in enumerate(operations):
            signals.append(
                GovernanceSignal(
                    signal_id=self._signal_id(turn, operation, ordinal),
                    operation=operation,
                    actor_principal_id=turn.speaker_principal_id,
                    actor_role=turn.speaker_role,
                    observed_index=observed_index,
                    source_public_turn_id=turn.turn_id,
                    target_principal_ids=target_principal_ids,
                    target_roles=target_roles,
                    deny_all_others=deny_all_others,
                    anchor_tokens=anchors,
                    source_text_sha256=digest,
                )
            )
        return tuple(signals)


class PublicTextGovernanceGate:
    """Conservative pre-reader gate using only the frozen public B2 surface."""

    def __init__(self, config: GovernanceConfig | None = None) -> None:
        self.config = config or GovernanceConfig()

    def _topic_overlap(
        self,
        candidate: GovernanceCandidate,
        signal: GovernanceSignal,
    ) -> int:
        if not signal.anchor_tokens:
            return 0
        return len(set(_tokens(candidate.text)) & set(signal.anchor_tokens))

    @staticmethod
    def _targets_asker(signal: GovernanceSignal, query: GovernanceQuery) -> bool:
        if query.asker_principal_id in signal.target_principal_ids:
            return True
        return query.asker_role.casefold() in signal.target_roles

    def _relevant(
        self,
        candidate: GovernanceCandidate,
        signal: GovernanceSignal,
    ) -> tuple[bool, int]:
        if signal.observed_index <= candidate.ingest_index:
            return False, 0
        if (
            self.config.same_speaker_authority_only
            and signal.actor_principal_id != candidate.speaker_principal_id
        ):
            return False, 0
        overlap = self._topic_overlap(candidate, signal)
        if signal.anchor_tokens and overlap < self.config.minimum_anchor_overlap:
            return False, overlap
        return True, overlap

    def evaluate(self, surface: GovernanceSurface) -> GovernanceEvaluation:
        assert_no_forbidden_capabilities(surface)
        decisions: list[CandidateDecision] = []

        for candidate in surface.candidates:
            relevant: list[tuple[GovernanceSignal, int]] = []
            for signal in surface.signals:
                applies, overlap = self._relevant(candidate, signal)
                if applies:
                    relevant.append((signal, overlap))
            relevant.sort(key=lambda row: (row[0].observed_index, row[0].signal_id))

            matched: list[str] = []
            reasons: list[str] = []
            disposition = (
                GateDisposition.ADMIT
                if self.config.unknown_disposition is UnknownDisposition.ADMIT
                else GateDisposition.BLOCK
            )
            maximum_overlap = 0
            deleted = False

            for signal, overlap in relevant:
                matched.append(signal.signal_id)
                maximum_overlap = max(maximum_overlap, overlap)
                if signal.operation is SignalOperation.DELETE:
                    disposition = GateDisposition.BLOCK
                    deleted = True
                    reasons.append("public_same_speaker_delete")
                    if self.config.deletion_is_terminal:
                        continue
                elif deleted and self.config.deletion_is_terminal:
                    continue
                elif signal.operation is SignalOperation.RESTRICT:
                    targets_asker = self._targets_asker(signal, surface.query)
                    actor_is_asker = (
                        signal.actor_principal_id == surface.query.asker_principal_id
                    )
                    if targets_asker or (signal.deny_all_others and not actor_is_asker):
                        disposition = GateDisposition.BLOCK
                        reasons.append("public_same_speaker_restriction")
                elif signal.operation is SignalOperation.GRANT:
                    if self._targets_asker(signal, surface.query):
                        disposition = GateDisposition.ADMIT
                        reasons.append("public_same_speaker_grant")

            if not matched:
                reasons.append(
                    "no_applicable_public_policy_signal_"
                    + self.config.unknown_disposition.value
                )
            decisions.append(
                CandidateDecision(
                    turn_id=candidate.turn_id,
                    rank=candidate.rank,
                    disposition=disposition,
                    reason_codes=tuple(dict.fromkeys(reasons)),
                    matched_signal_ids=tuple(dict.fromkeys(matched)),
                    anchor_overlap=maximum_overlap,
                )
            )

        return GovernanceEvaluation(decisions=tuple(decisions))


def _candidate(hit: LexicalHit, *, ingest_index: int) -> GovernanceCandidate:
    return GovernanceCandidate(
        turn_id=hit.turn.turn_id,
        speaker_principal_id=hit.turn.speaker_principal_id,
        speaker_role=hit.turn.speaker_role,
        timestamp=hit.turn.timestamp,
        turn_kind=hit.turn.turn_kind,
        text=hit.turn.text,
        ingest_index=ingest_index,
        rank=hit.rank,
        lexical_score=hit.lexical_score,
        recency_score=hit.recency_score,
        final_score=hit.final_score,
    )


class RawLexicalGovernedReaderGateMemAgent(RawLexicalSharedReaderGateMemAgent):
    """B2 pre-reader public-text governance over the exact B1a top-k candidates."""

    name = B2_METHOD_NAME

    def __init__(
        self,
        lexical_config: RawLexicalConfig | None,
        reader: ExtractiveReader,
        governance_config: GovernanceConfig | None = None,
    ) -> None:
        super().__init__(lexical_config, reader)
        self.governance_config = governance_config or GovernanceConfig()
        self._policy_parser: PublicTurnPolicyParser | None = None
        self._governance_gate = PublicTextGovernanceGate(self.governance_config)
        self._signals: list[GovernanceSignal] = []
        self._ingest_indices: dict[str, int] = {}

    @property
    def governance_signals(self) -> tuple[GovernanceSignal, ...]:
        return tuple(self._signals)

    def reset(self, episode: PublicEpisode) -> None:
        super().reset(episode)
        self._policy_parser = PublicTurnPolicyParser(episode)
        self._signals.clear()
        self._ingest_indices.clear()

    def ingest(self, turn: PublicTurn) -> None:
        super().ingest(turn)
        if self._policy_parser is None:
            raise RuntimeError("agent must be reset before ingestion")
        observed_index = len(self._turns) - 1
        self._ingest_indices[turn.turn_id] = observed_index
        self._signals.extend(
            self._policy_parser.parse(turn, observed_index=observed_index)
        )

    @staticmethod
    def _empty_reader_result() -> ExtractiveReaderResult:
        return ExtractiveReaderResult(
            answer="",
            answer_start=None,
            answer_end=None,
            span_score=None,
            null_score=None,
            score_margin=None,
            diagnostic_probability=None,
            window_count=0,
            input_token_count=0,
            forward_calls=0,
        )

    def query(self, checkpoint: PublicCheckpoint) -> dict[str, Any]:
        if self._episode is None:
            raise RuntimeError("agent must be reset before querying")

        hits = self._rank(checkpoint.query_text)
        candidates = tuple(
            _candidate(
                hit,
                ingest_index=self._ingest_indices[hit.turn.turn_id],
            )
            for hit in hits
        )
        surface = GovernanceSurface(
            principals=self._episode.principals,
            query=GovernanceQuery(
                asker_principal_id=checkpoint.asker_principal_id,
                asker_role=checkpoint.asker_role,
                query_text=checkpoint.query_text,
            ),
            candidates=candidates,
            signals=tuple(self._signals),
            observed_turn_count=len(self._turns),
        )
        evaluation = self._governance_gate.evaluate(surface)
        admitted = set(evaluation.admitted_turn_ids)
        admitted_hits = tuple(hit for hit in hits if hit.turn.turn_id in admitted)
        exposure = self._prompt_exposure(admitted_hits)

        if exposure.text:
            result = self.reader.answer(
                question=checkpoint.query_text,
                context=exposure.text,
            )
        else:
            result = self._empty_reader_result()

        retrieval_items = [
            {
                "rank": hit.rank,
                "turn_id": hit.turn.turn_id,
                "speaker_role": hit.turn.speaker_role,
                "lexical_score": hit.lexical_score,
                "recency_score": hit.recency_score,
                "final_score": hit.final_score,
            }
            for hit in hits
        ]
        prompt_turn_ids = [str(item["turn_id"]) for item in exposure.items]
        reader_audit = {
            "model_id": self.reader.model_id,
            "revision": self.reader.revision,
            "answer_start": result.answer_start,
            "answer_end": result.answer_end,
            "span_score": result.span_score,
            "null_score": result.null_score,
            "score_margin": result.score_margin,
            "diagnostic_probability": result.diagnostic_probability,
            "window_count": result.window_count,
            "input_token_count": result.input_token_count,
            "forward_calls": result.forward_calls,
            "threshold_is_calibrated": False,
        }
        governance_items = [
            {
                "turn_id": decision.turn_id,
                "rank": decision.rank,
                "disposition": decision.disposition.value,
                "reason_codes": list(decision.reason_codes),
                "matched_signal_ids": list(decision.matched_signal_ids),
                "anchor_overlap": decision.anchor_overlap,
            }
            for decision in evaluation.decisions
        ]
        action = "answer" if result.answered else "no_memory"
        return {
            "action": action,
            "answer": result.answer,
            "answer_structured": {
                "retrieved_turn_ids": [hit.turn.turn_id for hit in hits],
                "prompt_turn_ids": prompt_turn_ids,
                "governance": {
                    "candidate_count": len(hits),
                    "admitted_count": len(admitted_hits),
                    "blocked_count": len(hits) - len(admitted_hits),
                },
                "reader": reader_audit,
            },
            "used_record_ids": [],
            "memory_audit": {
                "schema_version": "track-x-gatemem-memory-audit-v0.4",
                "method": self.name,
                "surface_schema_version": B2_SURFACE_SCHEMA_VERSION,
                "retrieval_items": retrieval_items,
                "governance_items": governance_items,
                "prompt_items": list(exposure.items),
                "prompt_context": {
                    "text": exposure.text,
                    "character_count": len(exposure.text),
                    "sha256": sha256(exposure.text.encode("utf-8")).hexdigest(),
                },
                "reader": reader_audit,
            },
        }
