from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .v02_data import (
    CandidateMutation,
    DEVELOPMENT_TOPOLOGIES,
    HELDOUT_TOPOLOGIES,
    PassageCondition,
    RawPassageRecord,
    validate_records,
)


@dataclass(frozen=True, slots=True)
class RawPassageBundle:
    """One independently authored passage expanded into controlled conditions."""

    bundle_id: str
    fixture_id: str
    topology_family: str
    event_id: str
    query_id: str
    author_session: str
    complete_text: str
    ambiguous_text: str
    distractor_passages: tuple[str, ...]
    candidate_mutation: CandidateMutation
    notes: str = ""

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> RawPassageBundle:
        required = {
            "bundle_id",
            "fixture_id",
            "topology_family",
            "event_id",
            "query_id",
            "author_session",
            "complete_text",
            "ambiguous_text",
            "distractor_passages",
            "candidate_mutation",
            "notes",
        }
        missing = required - set(value)
        extras = set(value) - required
        if missing:
            raise ValueError("missing bundle keys: " + ", ".join(sorted(missing)))
        if extras:
            raise ValueError("unknown bundle keys: " + ", ".join(sorted(extras)))
        distractors = value["distractor_passages"]
        if not isinstance(distractors, list) or not all(
            isinstance(item, str) for item in distractors
        ):
            raise ValueError("distractor_passages must be a JSON list of strings")
        mutation = CandidateMutation.from_mapping(value["candidate_mutation"])
        if mutation is None:
            raise ValueError("bundle requires one frozen candidate mutation")
        return cls(
            bundle_id=str(value["bundle_id"]),
            fixture_id=str(value["fixture_id"]),
            topology_family=str(value["topology_family"]),
            event_id=str(value["event_id"]),
            query_id=str(value["query_id"]),
            author_session=str(value["author_session"]),
            complete_text=str(value["complete_text"]),
            ambiguous_text=str(value["ambiguous_text"]),
            distractor_passages=tuple(distractors),
            candidate_mutation=mutation,
            notes=str(value["notes"]),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "bundle_id": self.bundle_id,
            "fixture_id": self.fixture_id,
            "topology_family": self.topology_family,
            "event_id": self.event_id,
            "query_id": self.query_id,
            "author_session": self.author_session,
            "complete_text": self.complete_text,
            "ambiguous_text": self.ambiguous_text,
            "distractor_passages": list(self.distractor_passages),
            "candidate_mutation": self.candidate_mutation.to_mapping(),
            "notes": self.notes,
        }

    def expand(self) -> tuple[RawPassageRecord, ...]:
        common = {
            "fixture_id": self.fixture_id,
            "topology_family": self.topology_family,
            "event_id": self.event_id,
            "query_id": self.query_id,
            "author_session": self.author_session,
        }
        prefix = self.bundle_id
        mutation = self.candidate_mutation
        return (
            RawPassageRecord(
                passage_id=f"{prefix}-clean",
                raw_text=self.complete_text,
                context_passages=(),
                candidate_condition=PassageCondition.CLEAN,
                candidate_mutation=None,
                raw_available=True,
                notes="Clean independently authored passage.",
                **common,
            ),
            RawPassageRecord(
                passage_id=f"{prefix}-field",
                raw_text=self.complete_text,
                context_passages=(),
                candidate_condition=PassageCondition.FIELD_CORRUPTION,
                candidate_mutation=mutation,
                raw_available=True,
                notes="Complete passage paired with one controlled candidate error.",
                **common,
            ),
            RawPassageRecord(
                passage_id=f"{prefix}-omitted",
                raw_text=self.complete_text,
                context_passages=(),
                candidate_condition=PassageCondition.CANDIDATE_OMITTED,
                candidate_mutation=None,
                raw_available=True,
                notes="Primary candidate omitted while raw passage survives.",
                **common,
            ),
            RawPassageRecord(
                passage_id=f"{prefix}-raw-unavailable",
                raw_text=None,
                context_passages=(),
                candidate_condition=PassageCondition.RAW_UNAVAILABLE,
                candidate_mutation=mutation,
                raw_available=False,
                notes="Candidate corrupted and raw passage unavailable.",
                **common,
            ),
            RawPassageRecord(
                passage_id=f"{prefix}-ambiguous",
                raw_text=self.ambiguous_text,
                context_passages=(),
                candidate_condition=PassageCondition.AMBIGUOUS_RAW,
                candidate_mutation=mutation,
                raw_available=True,
                notes="Passage intentionally omits one material field.",
                **common,
            ),
            RawPassageRecord(
                passage_id=f"{prefix}-misleading",
                raw_text=self.complete_text,
                context_passages=self.distractor_passages,
                candidate_condition=PassageCondition.MISLEADING_CONTEXT,
                candidate_mutation=mutation,
                raw_available=True,
                notes="Complete passage accompanied by a misleading nearby passage.",
                **common,
            ),
        )


def validate_bundles(
    bundles: Iterable[RawPassageBundle], *, split: str
) -> tuple[RawPassageBundle, ...]:
    materialized = tuple(bundles)
    expected = DEVELOPMENT_TOPOLOGIES if split == "development" else HELDOUT_TOPOLOGIES
    expected_author = "B" if split == "development" else "A"
    if len(materialized) != len(expected):
        raise ValueError(
            f"{split} requires exactly {len(expected)} authored topology bundles"
        )
    seen_ids: set[str] = set()
    seen_topologies: set[str] = set()
    for bundle in materialized:
        if bundle.bundle_id in seen_ids:
            raise ValueError(f"duplicate bundle_id: {bundle.bundle_id}")
        seen_ids.add(bundle.bundle_id)
        if bundle.topology_family in seen_topologies:
            raise ValueError(
                f"duplicate topology bundle: {bundle.topology_family}"
            )
        seen_topologies.add(bundle.topology_family)
        if bundle.topology_family not in expected:
            raise ValueError(f"{split} bundle crosses topology split")
        if bundle.author_session != expected_author:
            raise ValueError(
                f"{split} bundle must be authored by Session {expected_author}"
            )
        if not bundle.complete_text.strip() or not bundle.ambiguous_text.strip():
            raise ValueError("bundle passage text cannot be blank")
        if not bundle.distractor_passages:
            raise ValueError("bundle requires at least one distractor passage")
    if seen_topologies != set(expected):
        raise ValueError("bundle topology coverage does not match frozen split")
    expanded = tuple(record for bundle in materialized for record in bundle.expand())
    validate_records(expanded, split=split)
    return materialized


def load_bundle_json(path: Path, *, split: str) -> tuple[RawPassageBundle, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("authored-passage source must be a JSON list")
    bundles = tuple(RawPassageBundle.from_mapping(item) for item in payload)
    return validate_bundles(bundles, split=split)


def expand_bundles(
    bundles: Iterable[RawPassageBundle], *, split: str
) -> tuple[RawPassageRecord, ...]:
    validated = validate_bundles(bundles, split=split)
    return tuple(record for bundle in validated for record in bundle.expand())
