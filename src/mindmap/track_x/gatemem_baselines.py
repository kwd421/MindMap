from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
import re
from typing import Any

from .gatemem_public import PublicCheckpoint, PublicEpisode, PublicTurn

_TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)


def lexical_tokens(text: str) -> tuple[str, ...]:
    """Return a deterministic, language-agnostic Unicode word-token view."""

    return tuple(token.casefold() for token in _TOKEN_RE.findall(text))


@dataclass(frozen=True, slots=True)
class RawLexicalConfig:
    top_k: int = 5
    k1: float = 1.2
    b: float = 0.75
    recency_weight: float = 0.0
    max_answer_characters: int = 6_000

    def __post_init__(self) -> None:
        if self.top_k <= 0:
            raise ValueError("top_k must be positive")
        if self.k1 <= 0:
            raise ValueError("k1 must be positive")
        if not 0.0 <= self.b <= 1.0:
            raise ValueError("b must lie in [0, 1]")
        if self.recency_weight < 0:
            raise ValueError("recency_weight must be non-negative")
        if self.max_answer_characters <= 0:
            raise ValueError("max_answer_characters must be positive")


@dataclass(frozen=True, slots=True)
class LexicalHit:
    turn: PublicTurn
    rank: int
    lexical_score: float
    recency_score: float
    final_score: float


class RawLexicalGateMemAgent:
    """Policy-unaware BM25 retrieval baseline over public raw turns.

    The baseline deliberately does not infer GateMem's hidden query category or
    expected action. It always answers with retrieved raw excerpts when any turn
    is available. Its purpose is to expose the utility/leakage trade-off of raw
    retrieval and to provide an auditable prompt-context trace.
    """

    name = "raw_lexical_bm25"

    def __init__(self, config: RawLexicalConfig | None = None) -> None:
        self.config = config or RawLexicalConfig()
        self._episode: PublicEpisode | None = None
        self._turns: list[PublicTurn] = []

    @property
    def turns(self) -> tuple[PublicTurn, ...]:
        return tuple(self._turns)

    def reset(self, episode: PublicEpisode) -> None:
        self._episode = episode
        self._turns.clear()

    def ingest(self, turn: PublicTurn) -> None:
        if self._episode is None:
            raise RuntimeError("agent must be reset before ingestion")
        self._turns.append(turn)

    def _rank(self, query: str) -> tuple[LexicalHit, ...]:
        if not self._turns:
            return ()

        documents = [lexical_tokens(turn.text) for turn in self._turns]
        query_counts = Counter(lexical_tokens(query))
        document_frequencies: Counter[str] = Counter()
        for document in documents:
            document_frequencies.update(set(document))

        n_documents = len(documents)
        average_length = sum(len(document) for document in documents) / n_documents
        average_length = average_length or 1.0
        scored: list[tuple[float, float, float, int, PublicTurn]] = []

        for index, (turn, document) in enumerate(zip(self._turns, documents, strict=True)):
            term_frequencies = Counter(document)
            length_normalizer = 1.0 - self.config.b + self.config.b * (
                len(document) / average_length
            )
            lexical_score = 0.0
            for term, query_frequency in query_counts.items():
                frequency = term_frequencies.get(term, 0)
                if frequency == 0:
                    continue
                document_frequency = document_frequencies[term]
                inverse_document_frequency = math.log(
                    1.0
                    + (n_documents - document_frequency + 0.5)
                    / (document_frequency + 0.5)
                )
                saturation = frequency * (self.config.k1 + 1.0) / (
                    frequency + self.config.k1 * length_normalizer
                )
                lexical_score += query_frequency * inverse_document_frequency * saturation

            recency_score = (index + 1) / n_documents
            final_score = lexical_score + self.config.recency_weight * recency_score
            scored.append((final_score, lexical_score, recency_score, index, turn))

        # Higher score first; on a true tie prefer the later public turn. This is
        # deterministic and avoids dependence on Python object identity.
        scored.sort(key=lambda row: (row[0], row[3]), reverse=True)
        selected = scored[: self.config.top_k]
        return tuple(
            LexicalHit(
                turn=turn,
                rank=rank,
                lexical_score=lexical_score,
                recency_score=recency_score,
                final_score=final_score,
            )
            for rank, (final_score, lexical_score, recency_score, _index, turn) in enumerate(
                selected, start=1
            )
        )

    def query(self, checkpoint: PublicCheckpoint) -> dict[str, Any]:
        if self._episode is None:
            raise RuntimeError("agent must be reset before querying")
        hits = self._rank(checkpoint.query_text)
        if not hits:
            return {
                "action": "no_memory",
                "answer": "",
                "answer_structured": {"retrieved_turn_ids": []},
                "used_record_ids": [],
                "memory_audit": {
                    "schema_version": "track-x-gatemem-memory-audit-v0.1",
                    "method": self.name,
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "items": [],
                    "prompt_context": {"text": "", "character_count": 0},
                },
            }

        chunks = [
            f"[{hit.turn.turn_id} | {hit.turn.speaker_role} | "
            f"{hit.turn.speaker_principal_id}] {hit.turn.text}"
            for hit in hits
        ]
        answer = "\n".join(chunks)[: self.config.max_answer_characters]
        items = [
            {
                "rank": hit.rank,
                "turn_id": hit.turn.turn_id,
                "speaker_principal_id": hit.turn.speaker_principal_id,
                "speaker_role": hit.turn.speaker_role,
                "text": hit.turn.text,
                "lexical_score": hit.lexical_score,
                "recency_score": hit.recency_score,
                "final_score": hit.final_score,
            }
            for hit in hits
        ]
        return {
            "action": "answer",
            "answer": answer,
            "answer_structured": {
                "retrieved_turn_ids": [hit.turn.turn_id for hit in hits]
            },
            # These are raw turns, not GateMem gold record IDs. Returning the
            # hidden record identifiers would violate the raw-language condition.
            "used_record_ids": [],
            "memory_audit": {
                "schema_version": "track-x-gatemem-memory-audit-v0.1",
                "method": self.name,
                "checkpoint_id": checkpoint.checkpoint_id,
                "items": items,
                "prompt_context": {
                    "text": answer,
                    "character_count": len(answer),
                },
            },
        }


class AlwaysNoMemoryGateMemAgent:
    """Degenerate selective baseline establishing the zero-coverage safety edge."""

    name = "always_no_memory"

    def reset(self, episode: PublicEpisode) -> None:
        return None

    def ingest(self, turn: PublicTurn) -> None:
        return None

    def query(self, checkpoint: PublicCheckpoint) -> dict[str, Any]:
        return {
            "action": "no_memory",
            "answer": "",
            "answer_structured": {},
            "used_record_ids": [],
            "memory_audit": {
                "schema_version": "track-x-gatemem-memory-audit-v0.1",
                "method": self.name,
                "checkpoint_id": checkpoint.checkpoint_id,
                "items": [],
                "prompt_context": {"text": "", "character_count": 0},
            },
        }
