from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Iterable

from mindmap.canonical.model import Answer, CommonEvent, TargetQuery


class ObserverSurface(IntEnum):
    BYTES = 0
    LOCAL_SCHEMA = 1
    SEMANTIC_JOURNAL = 2
    EXTERNAL_COMMITMENT = 3
    PROJECTION_COMMITMENT = 4


@dataclass(frozen=True, slots=True)
class Alert:
    rule: str
    candidate_event_ids: frozenset[str] = frozenset()
    constraint_ids: frozenset[str] = frozenset()
    surface: ObserverSurface = ObserverSurface.SEMANTIC_JOURNAL
    detail: str = ""


@dataclass(frozen=True, slots=True)
class ResponsibleSet:
    event_ids: frozenset[str] = frozenset()
    constraint_ids: frozenset[str] = frozenset()

    @classmethod
    def events(cls, *event_ids: str) -> "ResponsibleSet":
        return cls(event_ids=frozenset(event_ids))


@dataclass(frozen=True, slots=True)
class JournalCommitment:
    stream_id: str
    sequence_start: int
    sequence_end: int
    ordered_event_ids: tuple[str, ...]
    event_hashes: tuple[tuple[str, str], ...]
    head_hash: str
    previous_head_hash: str | None
    issuer: str
    canonicalization_version: str = "common-event-json-v1"


@dataclass(frozen=True, slots=True)
class ProjectionCommitment:
    projection_id: str
    projection_kind: str
    journal_head_hash: str
    projection_hash: str
    schema_version: str
    configuration_hash: str


@dataclass(frozen=True, slots=True)
class FaultCase:
    case_id: str
    family: str
    required_surface: ObserverSurface
    clean_events: tuple[CommonEvent, ...]
    faulty_events: tuple[CommonEvent, ...]
    query: TargetQuery
    expected_clean_answer: Answer
    acceptable_responsible_sets: tuple[ResponsibleSet, ...]
    journal_commitment: JournalCommitment | None = None
    projection_commitment: ProjectionCommitment | None = None
    clean_control: bool = False
    notes: str = ""
    tags: tuple[str, ...] = ()

    @classmethod
    def from_iterables(
        cls,
        *,
        case_id: str,
        family: str,
        required_surface: ObserverSurface,
        clean_events: Iterable[CommonEvent],
        faulty_events: Iterable[CommonEvent],
        query: TargetQuery,
        expected_clean_answer: Answer,
        acceptable_responsible_sets: Iterable[ResponsibleSet] = (),
        journal_commitment: JournalCommitment | None = None,
        projection_commitment: ProjectionCommitment | None = None,
        clean_control: bool = False,
        notes: str = "",
        tags: Iterable[str] = (),
    ) -> "FaultCase":
        return cls(
            case_id=case_id,
            family=family,
            required_surface=required_surface,
            clean_events=tuple(clean_events),
            faulty_events=tuple(faulty_events),
            query=query,
            expected_clean_answer=expected_clean_answer,
            acceptable_responsible_sets=tuple(acceptable_responsible_sets),
            journal_commitment=journal_commitment,
            projection_commitment=projection_commitment,
            clean_control=clean_control,
            notes=notes,
            tags=tuple(tags),
        )


@dataclass(frozen=True, slots=True)
class ObserverResult:
    observer: str
    case_id: str
    alerts: tuple[Alert, ...]
    answer: Answer | str
    detected: bool
    contained: bool
    answer_correct: bool
    silent_incorrect_use: bool
    candidate_event_ids: frozenset[str] = field(default_factory=frozenset)
    candidate_constraint_ids: frozenset[str] = field(default_factory=frozenset)


def localization_scores(
    candidate_event_ids: frozenset[str],
    candidate_constraint_ids: frozenset[str],
    acceptable: tuple[ResponsibleSet, ...],
) -> dict[str, float | int | bool]:
    if not acceptable:
        return {
            "mutated_event_hit": False,
            "responsible_recall": 0.0,
            "localization_precision": 0.0,
            "exact_responsible_set": False,
            "candidate_set_size": len(candidate_event_ids) + len(candidate_constraint_ids),
        }

    candidates = set(candidate_event_ids) | {
        f"constraint:{value}" for value in candidate_constraint_ids
    }
    best = {
        "mutated_event_hit": False,
        "responsible_recall": 0.0,
        "localization_precision": 0.0,
        "exact_responsible_set": False,
        "candidate_set_size": len(candidates),
    }
    for responsible in acceptable:
        expected = set(responsible.event_ids) | {
            f"constraint:{value}" for value in responsible.constraint_ids
        }
        intersection = candidates & expected
        recall = len(intersection) / len(expected) if expected else 0.0
        precision = len(intersection) / len(candidates) if candidates else 0.0
        exact = candidates == expected
        score = (int(exact), recall, precision)
        current = (
            int(bool(best["exact_responsible_set"])),
            float(best["responsible_recall"]),
            float(best["localization_precision"]),
        )
        if score > current:
            best = {
                "mutated_event_hit": bool(candidate_event_ids & responsible.event_ids),
                "responsible_recall": recall,
                "localization_precision": precision,
                "exact_responsible_set": exact,
                "candidate_set_size": len(candidates),
            }
    return best
