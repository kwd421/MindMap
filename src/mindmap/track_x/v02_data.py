from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Mapping


class PassageCondition(StrEnum):
    CLEAN = "clean"
    FIELD_CORRUPTION = "field_corruption"
    CANDIDATE_OMITTED = "candidate_omitted"
    RAW_UNAVAILABLE = "raw_unavailable"
    AMBIGUOUS_RAW = "ambiguous_raw"
    MISLEADING_CONTEXT = "misleading_context"


FORBIDDEN_PASSAGE_KEYS = frozenset(
    {
        "gold_event",
        "expected_answer",
        "answer",
        "recoverable_from_raw",
        "corrected_event",
        "verification_status",
        "confidence",
        "unsafe_disclosure",
    }
)

DEVELOPMENT_TOPOLOGIES = frozenset(
    {
        "branch_visibility",
        "mind_copy_without_world_fork",
        "world_fork_without_mind_copy",
        "unsynchronized_same_principal_replicas",
        "identity_fork_copy_attribution",
        "receive_accept_reject",
        "exposure_policy_lifecycle",
    }
)

HELDOUT_TOPOLOGIES = frozenset(
    {
        "restore_manifest_gap",
        "cross_world_reference_context",
        "protected_only_revocation",
        "independent_public_survives",
        "same_origin_dedup",
        "authorized_replication",
        "temporal_negative_controls",
    }
)

MAX_RAW_CHARACTERS = 1200
MAX_CONTEXT_PASSAGES = 3
MAX_CONTEXT_CHARACTERS = 1800


@dataclass(frozen=True, slots=True)
class CandidateMutation:
    field_name: str
    replacement: object | None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> CandidateMutation | None:
        if value is None:
            return None
        if set(value) != {"field_name", "replacement"}:
            raise ValueError(
                "candidate_mutation must contain exactly field_name and replacement"
            )
        field_name = value["field_name"]
        if not isinstance(field_name, str) or not field_name:
            raise ValueError("candidate mutation field_name must be non-empty")
        return cls(field_name=field_name, replacement=value["replacement"])

    def to_mapping(self) -> dict[str, object | None]:
        return {
            "field_name": self.field_name,
            "replacement": self.replacement,
        }


@dataclass(frozen=True, slots=True)
class RawPassageRecord:
    passage_id: str
    fixture_id: str
    topology_family: str
    event_id: str
    query_id: str
    author_session: str
    raw_text: str | None
    context_passages: tuple[str, ...]
    candidate_condition: PassageCondition
    candidate_mutation: CandidateMutation | None
    raw_available: bool
    notes: str = ""

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> RawPassageRecord:
        forbidden = set(value) & FORBIDDEN_PASSAGE_KEYS
        if forbidden:
            raise ValueError(
                "passage record contains evaluator-only fields: "
                + ", ".join(sorted(forbidden))
            )
        required = {
            "passage_id",
            "fixture_id",
            "topology_family",
            "event_id",
            "query_id",
            "author_session",
            "raw_text",
            "context_passages",
            "candidate_condition",
            "candidate_mutation",
            "raw_available",
            "notes",
        }
        missing = required - set(value)
        extras = set(value) - required
        if missing:
            raise ValueError("missing passage keys: " + ", ".join(sorted(missing)))
        if extras:
            raise ValueError("unknown passage keys: " + ", ".join(sorted(extras)))
        context = value["context_passages"]
        if not isinstance(context, list) or not all(
            isinstance(item, str) for item in context
        ):
            raise ValueError("context_passages must be a JSON list of strings")
        raw_text = value["raw_text"]
        if raw_text is not None and not isinstance(raw_text, str):
            raise ValueError("raw_text must be a string or null")
        return cls(
            passage_id=str(value["passage_id"]),
            fixture_id=str(value["fixture_id"]),
            topology_family=str(value["topology_family"]),
            event_id=str(value["event_id"]),
            query_id=str(value["query_id"]),
            author_session=str(value["author_session"]),
            raw_text=raw_text,
            context_passages=tuple(context),
            candidate_condition=PassageCondition(value["candidate_condition"]),
            candidate_mutation=CandidateMutation.from_mapping(
                value["candidate_mutation"]
            ),
            raw_available=bool(value["raw_available"]),
            notes=str(value["notes"]),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "passage_id": self.passage_id,
            "fixture_id": self.fixture_id,
            "topology_family": self.topology_family,
            "event_id": self.event_id,
            "query_id": self.query_id,
            "author_session": self.author_session,
            "raw_text": self.raw_text,
            "context_passages": list(self.context_passages),
            "candidate_condition": self.candidate_condition.value,
            "candidate_mutation": (
                None
                if self.candidate_mutation is None
                else self.candidate_mutation.to_mapping()
            ),
            "raw_available": self.raw_available,
            "notes": self.notes,
        }


def _validate_record(record: RawPassageRecord, *, split: str) -> None:
    if not record.passage_id:
        raise ValueError("passage_id cannot be empty")
    if not record.fixture_id.startswith("F"):
        raise ValueError("fixture_id must reference a canonical F fixture")
    if not record.event_id or not record.query_id:
        raise ValueError("event_id and query_id are required")
    if split == "development":
        if record.author_session != "B":
            raise ValueError("development passages must be authored by Session B")
        if record.topology_family not in DEVELOPMENT_TOPOLOGIES:
            raise ValueError("development passage uses a held-out topology")
    elif split == "heldout":
        if record.author_session != "A":
            raise ValueError("held-out passages must be authored by Session A")
        if record.topology_family not in HELDOUT_TOPOLOGIES:
            raise ValueError("held-out passage uses a development topology")
    else:
        raise ValueError(f"unsupported split: {split}")

    if record.raw_available != (record.raw_text is not None):
        raise ValueError("raw_available must match raw_text presence")
    if record.raw_text is not None:
        text = record.raw_text.strip()
        if not text:
            raise ValueError("available raw_text cannot be blank")
        if len(text) > MAX_RAW_CHARACTERS:
            raise ValueError("raw_text exceeds the frozen character budget")
        forbidden_snippets = (
            "about_world_branch_id=",
            "policy_operation=",
            "candidate_mutation",
            "expected_answer",
            "gold_event",
        )
        if any(snippet in text for snippet in forbidden_snippets):
            raise ValueError("raw_text exposes field or evaluator labels")

    if len(record.context_passages) > MAX_CONTEXT_PASSAGES:
        raise ValueError("too many context passages")
    if sum(len(item) for item in record.context_passages) > MAX_CONTEXT_CHARACTERS:
        raise ValueError("context passage budget exceeded")

    if record.candidate_condition is PassageCondition.CLEAN:
        if record.candidate_mutation is not None:
            raise ValueError("clean passage cannot declare a candidate mutation")
    elif record.candidate_condition is PassageCondition.CANDIDATE_OMITTED:
        if record.candidate_mutation is not None:
            raise ValueError("candidate_omitted does not use a field mutation")
    else:
        if record.candidate_mutation is None:
            raise ValueError(
                f"{record.candidate_condition.value} requires a candidate mutation"
            )

    if record.candidate_condition is PassageCondition.RAW_UNAVAILABLE:
        if record.raw_available:
            raise ValueError("raw_unavailable condition must withhold raw text")
    elif not record.raw_available:
        raise ValueError(
            f"{record.candidate_condition.value} requires available raw text"
        )

    if record.candidate_condition is PassageCondition.MISLEADING_CONTEXT:
        if not record.context_passages:
            raise ValueError("misleading_context requires at least one distractor")


def validate_records(
    records: Iterable[RawPassageRecord], *, split: str
) -> tuple[RawPassageRecord, ...]:
    materialized = tuple(records)
    if not materialized:
        raise ValueError(f"{split} passage set cannot be empty")
    seen: set[str] = set()
    coverage: dict[tuple[str, PassageCondition], int] = {}
    for record in materialized:
        _validate_record(record, split=split)
        if record.passage_id in seen:
            raise ValueError(f"duplicate passage_id: {record.passage_id}")
        seen.add(record.passage_id)
        key = (record.topology_family, record.candidate_condition)
        coverage[key] = coverage.get(key, 0) + 1

    expected_topologies = (
        DEVELOPMENT_TOPOLOGIES if split == "development" else HELDOUT_TOPOLOGIES
    )
    expected_conditions = set(PassageCondition)
    for topology in expected_topologies:
        missing = [
            condition.value
            for condition in expected_conditions
            if coverage.get((topology, condition), 0) == 0
        ]
        if missing:
            raise ValueError(
                f"{topology} lacks frozen conditions: " + ", ".join(sorted(missing))
            )
    return materialized


def load_jsonl(path: Path, *, split: str) -> tuple[RawPassageRecord, ...]:
    records: list[RawPassageRecord] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}: {exc}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL row {line_number} must be an object")
            try:
                records.append(RawPassageRecord.from_mapping(payload))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid passage at {path}:{line_number}: {exc}") from exc
    return validate_records(records, split=split)


def write_jsonl(path: Path, records: Iterable[RawPassageRecord]) -> None:
    materialized = tuple(records)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in materialized:
            handle.write(
                json.dumps(
                    record.to_mapping(),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )
