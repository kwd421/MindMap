from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Iterable

from mindmap.canonical.model import CommonEvent, sorted_events

from .model import JournalCommitment, ProjectionCommitment


def canonical_event_bytes(event: CommonEvent) -> bytes:
    return json.dumps(
        asdict(event),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def event_hash(event: CommonEvent) -> str:
    return hashlib.sha256(canonical_event_bytes(event)).hexdigest()


def journal_head(events: Iterable[CommonEvent], previous_head_hash: str | None = None) -> str:
    digest = hashlib.sha256()
    if previous_head_hash:
        digest.update(previous_head_hash.encode("ascii"))
    for sequence, event in enumerate(sorted_events(events), start=1):
        digest.update(str(sequence).encode("ascii"))
        digest.update(b"\0")
        digest.update(event.event_id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(event_hash(event).encode("ascii"))
    return digest.hexdigest()


def make_journal_commitment(
    events: Iterable[CommonEvent],
    *,
    stream_id: str,
    issuer: str = "fixture-authority",
    previous_head_hash: str | None = None,
) -> JournalCommitment:
    ordered = sorted_events(events)
    return JournalCommitment(
        stream_id=stream_id,
        sequence_start=1,
        sequence_end=len(ordered),
        ordered_event_ids=tuple(event.event_id for event in ordered),
        event_hashes=tuple((event.event_id, event_hash(event)) for event in ordered),
        head_hash=journal_head(ordered, previous_head_hash),
        previous_head_hash=previous_head_hash,
        issuer=issuer,
    )


def projection_hash(rows: Iterable[tuple[str, str]]) -> str:
    digest = hashlib.sha256()
    for key, value in sorted(rows):
        digest.update(key.encode("utf-8"))
        digest.update(b"\0")
        digest.update(value.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def make_projection_commitment(
    *,
    projection_id: str,
    projection_kind: str,
    journal_head_hash: str,
    rows: Iterable[tuple[str, str]],
    schema_version: str = "mindmap-v0.2",
    configuration_hash: str = "canonical-default",
) -> ProjectionCommitment:
    return ProjectionCommitment(
        projection_id=projection_id,
        projection_kind=projection_kind,
        journal_head_hash=journal_head_hash,
        projection_hash=projection_hash(rows),
        schema_version=schema_version,
        configuration_hash=configuration_hash,
    )
