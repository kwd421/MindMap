from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import math
import re
from typing import Any

from .gatemem_public import PublicCheckpoint, PublicEpisode, PublicTurn

_TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)


def lexical_tokens(text: str) -> tuple[str, ...]:
    """Return a deterministic Unicode word-regex token view."""

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


@dataclass(frozen=True, slots=True)
class PromptExposure:
    text: str
    items: tuple[dict[str, Any], ...]


class RawLexicalGateMemAgent:
    """Policy-unaware BM25 context-echo endpoint over public raw turns.

    This control deliberately has no answer reader and must not be presented as
    a capacity-matched QA baseline. It exposes the high-coverage leakage endpoint
    of raw retrieval. Method-side opaque IDs are retained only in local audit
    fields and never inserted into the answer/context text.
    """

    name = "raw_context_echo_bm25"

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

        for index, (turn, document) in enumerate(
            zip(self._turns, documents, strict=True)
        ):
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
                lexical_score += (
                    query_frequency * inverse_document_frequency * saturation
                )

            recency_score = (index + 1) / n_documents
            final_score = lexical_score + self.config.recency_weight * recency_score
            scored.append((final_score, lexical_score, recency_score, index, turn))

        # Higher score first; on a true tie prefer the later public turn.
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
            for rank, (
                final_score,
                lexical_score,
                recency_score,
                _index,
                turn,
            ) in enumerate(selected, start=1)
        )

    def _prompt_exposure(self, hits: tuple[LexicalHit, ...]) -> PromptExposure:
        pieces: list[str] = []
        items: list[dict[str, Any]] = []
        used = 0
        budget = self.config.max_answer_characters

        for hit in hits:
            separator = "\n" if pieces else ""
            prefix = f"[{hit.turn.speaker_role}] "
            fixed = len(separator) + len(prefix)
            remaining = budget - used
            if remaining <= fixed:
                break
            source_count = min(len(hit.turn.text), remaining - fixed)
            if source_count <= 0:
                break
            exposed_text = hit.turn.text[:source_count]
            piece = separator + prefix + exposed_text
            prompt_text_start = used + len(separator) + len(prefix)
            pieces.append(piece)
            used += len(piece)
            items.append(
                {
                    "rank": hit.rank,
                    "turn_id": hit.turn.turn_id,
                    "speaker_role": hit.turn.speaker_role,
                    "source_char_start": 0,
                    "source_char_end": source_count,
                    "prompt_char_start": prompt_text_start,
                    "prompt_char_end": prompt_text_start + source_count,
                    "truncated": source_count < len(hit.turn.text),
                    "lexical_score": hit.lexical_score,
                    "recency_score": hit.recency_score,
                    "final_score": hit.final_score,
                }
            )
            if source_count < len(hit.turn.text):
                break

        return PromptExposure(text="".join(pieces), items=tuple(items))

    def query(self, checkpoint: PublicCheckpoint) -> dict[str, Any]:
        if self._episode is None:
            raise RuntimeError("agent must be reset before querying")
        hits = self._rank(checkpoint.query_text)
        if not hits:
            return {
                "action": "no_memory",
                "answer": "",
                "answer_structured": {
                    "retrieved_turn_ids": [],
                    "prompt_turn_ids": [],
                },
                "used_record_ids": [],
                "memory_audit": {
                    "schema_version": "track-x-gatemem-memory-audit-v0.2",
                    "method": self.name,
                    "retrieval_items": [],
                    "prompt_items": [],
                    "prompt_context": {
                        "text": "",
                        "character_count": 0,
                        "sha256": sha256(b"").hexdigest(),
                    },
                },
            }

        exposure = self._prompt_exposure(hits)
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
        return {
            "action": "answer",
            "answer": exposure.text,
            "answer_structured": {
                "retrieved_turn_ids": [hit.turn.turn_id for hit in hits],
                "prompt_turn_ids": prompt_turn_ids,
            },
            # Raw turn IDs are not GateMem gold record IDs.
            "used_record_ids": [],
            "memory_audit": {
                "schema_version": "track-x-gatemem-memory-audit-v0.2",
                "method": self.name,
                "retrieval_items": retrieval_items,
                "prompt_items": list(exposure.items),
                "prompt_context": {
                    "text": exposure.text,
                    "character_count": len(exposure.text),
                    "sha256": sha256(exposure.text.encode("utf-8")).hexdigest(),
                },
            },
        }


class AlwaysNoMemoryGateMemAgent:
    """Degenerate selective baseline establishing the zero-coverage edge."""

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
                "schema_version": "track-x-gatemem-memory-audit-v0.2",
                "method": self.name,
                "retrieval_items": [],
                "prompt_items": [],
                "prompt_context": {
                    "text": "",
                    "character_count": 0,
                    "sha256": sha256(b"").hexdigest(),
                },
            },
        }
