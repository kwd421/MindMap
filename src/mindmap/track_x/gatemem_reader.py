from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
import time
from typing import Any, Protocol

from .gatemem_baselines import RawLexicalConfig, RawLexicalGateMemAgent
from .gatemem_public import PublicCheckpoint

DEFAULT_READER_MODEL_ID = "deepset/minilm-uncased-squad2"
DEFAULT_READER_MODEL_REVISION = "934656cdda79824eabf503ed56e15c01ddbdbe3f"


class ReaderDependencyError(RuntimeError):
    """Raised when the optional frozen reader runtime is unavailable."""


@dataclass(frozen=True, slots=True)
class ExtractiveReaderConfig:
    model_id: str = DEFAULT_READER_MODEL_ID
    revision: str = DEFAULT_READER_MODEL_REVISION
    max_sequence_length: int = 384
    stride: int = 128
    max_answer_tokens: int = 30
    null_margin: float = 0.0

    def __post_init__(self) -> None:
        if not self.model_id.strip():
            raise ValueError("model_id must be non-empty")
        if not self.revision.strip():
            raise ValueError("revision must be non-empty")
        if self.max_sequence_length < 64:
            raise ValueError("max_sequence_length must be at least 64")
        if self.stride < 0 or self.stride >= self.max_sequence_length:
            raise ValueError("stride must lie in [0, max_sequence_length)")
        if self.max_answer_tokens <= 0:
            raise ValueError("max_answer_tokens must be positive")
        if not math.isfinite(self.null_margin):
            raise ValueError("null_margin must be finite")


@dataclass(frozen=True, slots=True)
class ExtractiveReaderResult:
    answer: str
    answer_start: int | None
    answer_end: int | None
    span_score: float | None
    null_score: float | None
    score_margin: float | None
    diagnostic_probability: float | None
    window_count: int
    input_token_count: int
    forward_calls: int

    @property
    def answered(self) -> bool:
        return bool(self.answer)


@dataclass(frozen=True, slots=True)
class ReaderRuntimeStats:
    calls: int
    forward_calls: int
    windows: int
    input_tokens: int
    elapsed_seconds: float

    def to_json(self) -> dict[str, int | float]:
        return {
            "calls": self.calls,
            "forward_calls": self.forward_calls,
            "windows": self.windows,
            "input_tokens": self.input_tokens,
            "elapsed_seconds": self.elapsed_seconds,
        }


class ExtractiveReader(Protocol):
    model_id: str
    revision: str

    def answer(self, *, question: str, context: str) -> ExtractiveReaderResult:
        ...


class TransformersExtractiveReader:
    """Frozen CPU extractive reader over an already selected prompt context.

    The model is loaded lazily at an immutable Hugging Face revision. The
    reader receives no GateMem labels, relationships, source IDs, future turns,
    or gold records. It is intentionally policy-unaware: B1b changes only the
    use of the exact B1a BM25 context and cannot remove text already exposed to
    the reader.
    """

    def __init__(self, config: ExtractiveReaderConfig | None = None) -> None:
        self.config = config or ExtractiveReaderConfig()
        self.model_id = self.config.model_id
        self.revision = self.config.revision
        self._tokenizer: Any | None = None
        self._model: Any | None = None
        self._torch: Any | None = None
        self._calls = 0
        self._forward_calls = 0
        self._windows = 0
        self._input_tokens = 0
        self._elapsed_seconds = 0.0

    def _ensure_loaded(self) -> tuple[Any, Any, Any]:
        if (
            self._tokenizer is not None
            and self._model is not None
            and self._torch is not None
        ):
            return self._tokenizer, self._model, self._torch
        try:
            import torch
            from transformers import AutoModelForQuestionAnswering, AutoTokenizer
        except ImportError as exc:  # pragma: no cover - optional runtime
            raise ReaderDependencyError(
                "install the 'reader' extra to use the frozen GateMem B1b reader"
            ) from exc

        tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_id,
            revision=self.config.revision,
            use_fast=True,
        )
        if not getattr(tokenizer, "is_fast", False):
            raise ReaderDependencyError(
                "the frozen extractive reader requires a fast tokenizer"
            )
        model = AutoModelForQuestionAnswering.from_pretrained(
            self.config.model_id,
            revision=self.config.revision,
            use_safetensors=True,
        )
        model.eval()
        self._tokenizer = tokenizer
        self._model = model
        self._torch = torch
        return tokenizer, model, torch

    def stats(self) -> ReaderRuntimeStats:
        return ReaderRuntimeStats(
            calls=self._calls,
            forward_calls=self._forward_calls,
            windows=self._windows,
            input_tokens=self._input_tokens,
            elapsed_seconds=self._elapsed_seconds,
        )

    @staticmethod
    def _diagnostic_probability(margin: float) -> float:
        bounded = max(-60.0, min(60.0, margin))
        return 1.0 / (1.0 + math.exp(-bounded))

    def answer(self, *, question: str, context: str) -> ExtractiveReaderResult:
        question = question.strip()
        context = context.strip()
        self._calls += 1
        if not question or not context:
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

        tokenizer, model, torch = self._ensure_loaded()
        started = time.perf_counter()
        encoded = tokenizer(
            question,
            context,
            truncation="only_second",
            max_length=self.config.max_sequence_length,
            stride=self.config.stride,
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
            return_tensors="pt",
            padding=True,
        )
        sequence_ids = [
            tuple(encoded.sequence_ids(index))
            for index in range(len(encoded["input_ids"]))
        ]
        offsets = encoded.pop("offset_mapping")
        encoded.pop("overflow_to_sample_mapping", None)
        input_token_count = int(encoded["attention_mask"].sum().item())
        window_count = int(encoded["input_ids"].shape[0])

        with torch.inference_mode():
            output = model(**encoded)
        self._forward_calls += 1
        self._windows += window_count
        self._input_tokens += input_token_count
        self._elapsed_seconds += time.perf_counter() - started

        start_logits = output.start_logits.detach().cpu()
        end_logits = output.end_logits.detach().cpu()
        input_ids = encoded["input_ids"].detach().cpu()
        offsets = offsets.detach().cpu()
        cls_token_id = tokenizer.cls_token_id

        best_span: tuple[float, int, int] | None = None
        minimum_null_score = math.inf

        for feature_index, feature_sequence_ids in enumerate(sequence_ids):
            ids = input_ids[feature_index].tolist()
            if cls_token_id is not None and cls_token_id in ids:
                cls_index = ids.index(cls_token_id)
            else:
                cls_index = 0
            null_score = float(
                start_logits[feature_index, cls_index]
                + end_logits[feature_index, cls_index]
            )
            minimum_null_score = min(minimum_null_score, null_score)

            context_positions = [
                index
                for index, sequence_id in enumerate(feature_sequence_ids)
                if sequence_id == 1
                and int(offsets[feature_index, index, 1])
                > int(offsets[feature_index, index, 0])
            ]
            start_candidates = sorted(
                context_positions,
                key=lambda index: float(start_logits[feature_index, index]),
                reverse=True,
            )[:20]
            end_candidates = sorted(
                context_positions,
                key=lambda index: float(end_logits[feature_index, index]),
                reverse=True,
            )[:20]

            for start_index in start_candidates:
                for end_index in end_candidates:
                    if end_index < start_index:
                        continue
                    if end_index - start_index + 1 > self.config.max_answer_tokens:
                        continue
                    char_start = int(offsets[feature_index, start_index, 0])
                    char_end = int(offsets[feature_index, end_index, 1])
                    if char_end <= char_start:
                        continue
                    score = float(
                        start_logits[feature_index, start_index]
                        + end_logits[feature_index, end_index]
                    )
                    if best_span is None or score > best_span[0]:
                        best_span = (score, char_start, char_end)

        if best_span is None or not math.isfinite(minimum_null_score):
            return ExtractiveReaderResult(
                answer="",
                answer_start=None,
                answer_end=None,
                span_score=None,
                null_score=(
                    None
                    if not math.isfinite(minimum_null_score)
                    else minimum_null_score
                ),
                score_margin=None,
                diagnostic_probability=None,
                window_count=window_count,
                input_token_count=input_token_count,
                forward_calls=1,
            )

        span_score, answer_start, answer_end = best_span
        margin = span_score - minimum_null_score
        answer = context[answer_start:answer_end].strip()
        if margin <= self.config.null_margin or not answer:
            answer = ""
            answer_start = None
            answer_end = None

        return ExtractiveReaderResult(
            answer=answer,
            answer_start=answer_start,
            answer_end=answer_end,
            span_score=span_score,
            null_score=minimum_null_score,
            score_margin=margin,
            diagnostic_probability=self._diagnostic_probability(margin),
            window_count=window_count,
            input_token_count=input_token_count,
            forward_calls=1,
        )


class RawLexicalSharedReaderGateMemAgent(RawLexicalGateMemAgent):
    """B1b: exact B1a BM25 prompt context followed by one frozen reader."""

    name = "raw_bm25_shared_extractive_reader"

    def __init__(
        self,
        lexical_config: RawLexicalConfig | None,
        reader: ExtractiveReader,
    ) -> None:
        super().__init__(lexical_config)
        self.reader = reader

    def query(self, checkpoint: PublicCheckpoint) -> dict[str, Any]:
        if self._episode is None:
            raise RuntimeError("agent must be reset before querying")
        hits = self._rank(checkpoint.query_text)
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

        if not exposure.text:
            result = ExtractiveReaderResult(
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
        else:
            result = self.reader.answer(
                question=checkpoint.query_text,
                context=exposure.text,
            )

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
        action = "answer" if result.answered else "no_memory"
        return {
            "action": action,
            "answer": result.answer,
            "answer_structured": {
                "retrieved_turn_ids": [hit.turn.turn_id for hit in hits],
                "prompt_turn_ids": prompt_turn_ids,
                "reader": reader_audit,
            },
            "used_record_ids": [],
            "memory_audit": {
                "schema_version": "track-x-gatemem-memory-audit-v0.3",
                "method": self.name,
                "retrieval_items": retrieval_items,
                "prompt_items": list(exposure.items),
                "prompt_context": {
                    "text": exposure.text,
                    "character_count": len(exposure.text),
                    "sha256": sha256(exposure.text.encode("utf-8")).hexdigest(),
                },
                "reader": reader_audit,
            },
        }
