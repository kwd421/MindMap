from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Iterable, Protocol, Type

from mindmap.canonical.generic import GenericLedger
from mindmap.canonical.model import Answer, CommonEvent, TargetQuery
from mindmap.canonical.typed import TypedLedger

from .commitment import journal_head, projection_hash


class Ledger(Protocol):
    def answer(self, query: TargetQuery) -> Answer: ...


@dataclass(frozen=True, slots=True)
class ProjectionState:
    journal_head_hash: str
    rows: tuple[tuple[str, str], ...]
    implementation: str
    rebuild_generation: int

    @property
    def content_hash(self) -> str:
        return projection_hash(self.rows)

    def answer(self, query: TargetQuery) -> Answer:
        serialized = dict(self.rows).get(query.query_id)
        if serialized is None:
            raise KeyError(f"query absent from projection: {query.query_id}")
        return json.loads(serialized)


@dataclass(slots=True)
class PhysicalMetrics:
    journal_appends: int = 0
    projection_rebuilds: int = 0
    events_reprocessed: int = 0
    query_recomputations: int = 0
    projection_rows_written: int = 0

    def snapshot(self) -> dict[str, int]:
        return {
            "journal_appends": self.journal_appends,
            "projection_rebuilds": self.projection_rebuilds,
            "events_reprocessed": self.events_reprocessed,
            "query_recomputations": self.query_recomputations,
            "projection_rows_written": self.projection_rows_written,
        }


class PhysicalStore:
    implementation_name = "base"
    ledger_type: Type[Ledger]

    def __init__(
        self,
        *,
        journal_events: Iterable[CommonEvent],
        projection_events: Iterable[CommonEvent],
        queries: Iterable[TargetQuery],
        projection_overrides: dict[str, Answer] | None = None,
    ) -> None:
        self.journal = list(journal_events)
        self.queries = tuple(queries)
        self.metrics = PhysicalMetrics(journal_appends=len(self.journal))
        self._generation = 0
        self.projection = self._build_projection(
            tuple(projection_events),
            projection_overrides=projection_overrides or {},
        )

    @staticmethod
    def _encode_answer(answer: Answer) -> str:
        return json.dumps(answer, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def _build_projection(
        self,
        events: tuple[CommonEvent, ...],
        *,
        projection_overrides: dict[str, Answer] | None = None,
    ) -> ProjectionState:
        ledger = self.ledger_type(events)
        overrides = projection_overrides or {}
        rows: list[tuple[str, str]] = []
        for query in self.queries:
            answer = overrides.get(query.query_id, ledger.answer(query))
            rows.append((query.query_id, self._encode_answer(answer)))
        self._generation += 1
        self.metrics.projection_rebuilds += 1
        self.metrics.events_reprocessed += len(events)
        self.metrics.query_recomputations += len(self.queries)
        self.metrics.projection_rows_written += len(rows)
        return ProjectionState(
            journal_head_hash=journal_head(events),
            rows=tuple(sorted(rows)),
            implementation=self.implementation_name,
            rebuild_generation=self._generation,
        )

    def append_without_projection(self, event: CommonEvent) -> None:
        self.journal.append(event)
        self.metrics.journal_appends += 1

    def append_transactional(self, event: CommonEvent) -> None:
        self.journal.append(event)
        self.metrics.journal_appends += 1
        self.projection = self._build_projection(tuple(self.journal))

    def replace_journal(self, events: Iterable[CommonEvent]) -> None:
        self.journal = list(events)
        self.metrics.journal_appends += len(self.journal)

    def current_journal_head(self) -> str:
        return journal_head(tuple(self.journal))

    def answer(self, query: TargetQuery) -> Answer:
        return self.projection.answer(query)

    def stale_against_journal(self) -> bool:
        return self.projection.journal_head_hash != self.current_journal_head()

    def content_matches(self, expected_hash: str) -> bool:
        return self.projection.content_hash == expected_hash

    def rebuild_from_journal(self) -> None:
        self.projection = self._build_projection(tuple(self.journal))

    def repair_from_authority(self, authoritative_events: Iterable[CommonEvent]) -> None:
        self.journal = list(authoritative_events)
        self.rebuild_from_journal()


class GenericPhysicalStore(PhysicalStore):
    implementation_name = "G_generic_physical_v0.3"
    ledger_type = GenericLedger


class TypedPhysicalStore(PhysicalStore):
    implementation_name = "T_typed_physical_v0.3"
    ledger_type = TypedLedger


@dataclass(frozen=True, slots=True)
class PhysicalFaultCase:
    case_id: str
    family: str
    clean_events: tuple[CommonEvent, ...]
    faulty_journal_events: tuple[CommonEvent, ...]
    faulty_projection_events: tuple[CommonEvent, ...]
    queries: tuple[TargetQuery, ...]
    expected_answers: tuple[tuple[str, Answer], ...]
    projection_overrides: tuple[tuple[str, Answer], ...] = ()
    clean_control: bool = False
    identifiable: bool = True
    repair_authority_available: bool = True
    notes: str = ""

    @property
    def expected_by_query(self) -> dict[str, Answer]:
        return dict(self.expected_answers)

    @property
    def overrides(self) -> dict[str, Answer]:
        return dict(self.projection_overrides)


@dataclass(frozen=True, slots=True)
class PhysicalResult:
    case_id: str
    family: str
    implementation: str
    clean_control: bool
    identifiable: bool
    stale_head_detected: bool
    content_mismatch_detected: bool
    detected: bool
    pre_repair_correct: bool
    silent_incorrect_use: bool
    repair_attempted: bool
    repair_success: bool
    residue_after_repair: int
    metrics_before_repair: tuple[tuple[str, int], ...]
    metrics_after_repair: tuple[tuple[str, int], ...]
    notes: str = ""


def expected_projection_rows(
    ledger_type: Type[Ledger],
    events: tuple[CommonEvent, ...],
    queries: tuple[TargetQuery, ...],
) -> tuple[tuple[str, str], ...]:
    ledger = ledger_type(events)
    return tuple(
        sorted(
            (
                query.query_id,
                PhysicalStore._encode_answer(ledger.answer(query)),
            )
            for query in queries
        )
    )


def run_physical_case(
    case: PhysicalFaultCase,
    store_type: type[PhysicalStore],
) -> PhysicalResult:
    expected_rows = expected_projection_rows(
        store_type.ledger_type,
        case.clean_events,
        case.queries,
    )
    expected_content_hash = projection_hash(expected_rows)

    store = store_type(
        journal_events=case.faulty_journal_events,
        projection_events=case.faulty_projection_events,
        queries=case.queries,
        projection_overrides=case.overrides,
    )
    stale_head = store.stale_against_journal()
    content_mismatch = not store.content_matches(expected_content_hash)
    detected = stale_head or content_mismatch

    expected = case.expected_by_query
    answers: dict[str, Answer | str] = {}
    for query in case.queries:
        try:
            answers[query.query_id] = store.answer(query)
        except Exception as exc:
            answers[query.query_id] = f"ERROR:{type(exc).__name__}:{exc}"
    pre_correct = all(answers.get(query_id) == value for query_id, value in expected.items())
    silent_wrong = not detected and not pre_correct
    before = tuple(sorted(store.metrics.snapshot().items()))

    repair_attempted = detected and case.repair_authority_available
    repair_success = False
    residue = sum(answers.get(query_id) != value for query_id, value in expected.items())
    if repair_attempted:
        store.repair_from_authority(case.clean_events)
        repaired_answers = {
            query.query_id: store.answer(query) for query in case.queries
        }
        residue = sum(
            repaired_answers.get(query_id) != value
            for query_id, value in expected.items()
        )
        repair_success = residue == 0 and not store.stale_against_journal()

    after = tuple(sorted(store.metrics.snapshot().items()))
    return PhysicalResult(
        case_id=case.case_id,
        family=case.family,
        implementation=store.implementation_name,
        clean_control=case.clean_control,
        identifiable=case.identifiable,
        stale_head_detected=stale_head,
        content_mismatch_detected=content_mismatch,
        detected=detected,
        pre_repair_correct=pre_correct,
        silent_incorrect_use=silent_wrong,
        repair_attempted=repair_attempted,
        repair_success=repair_success,
        residue_after_repair=residue,
        metrics_before_repair=before,
        metrics_after_repair=after,
        notes=case.notes,
    )
