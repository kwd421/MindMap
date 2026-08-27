from __future__ import annotations

from dataclasses import replace

from mindmap.canonical.fixtures import all_fixtures
from mindmap.canonical.gold import GoldSemantics
from mindmap.canonical.model import CommonEvent, Fixture, freeze_attrs

from .manifest import FROZEN_MANIFEST, ManifestEntry
from .model import CandidateCondition, RawCandidateCase
from .render import render_event


def _fixture_map() -> dict[str, Fixture]:
    return {fixture.fixture_id: fixture for fixture in all_fixtures()}


def _corrupt(event: CommonEvent, field_name: str) -> CommonEvent:
    if field_name == "about_world_branch_id":
        return replace(event, about_world_branch_id="wrong-world")
    if field_name == "attitude_transition":
        replacement = (
            "believe" if event.attitude_transition == "disbelieve" else "disbelieve"
        )
        return replace(event, attitude_transition=replacement)
    if field_name == "transfer_kind":
        replacement = "receive" if event.transfer_kind != "receive" else "evidence_copy"
        return replace(event, transfer_kind=replacement)
    if field_name == "destination_mind_instance_id":
        return replace(event, destination_mind_instance_id="wrong-mind")
    if field_name == "policy_operation":
        replacements = {
            "self_seal": "self_unseal",
            "self_unseal": "self_seal",
            "revoke": "grant",
            "evidence_delete": "grant",
            "grant": "revoke",
        }
        return replace(
            event,
            policy_operation=replacements.get(event.policy_operation, "revoke"),
        )
    if field_name == "snapshot_cutoff":
        cutoff = event.snapshot_cutoff if event.snapshot_cutoff is not None else 0
        return replace(event, snapshot_cutoff=max(0, cutoff - 6))
    if field_name == "object_id":
        return replace(event, object_id=f"{event.object_id}.wrong")
    if field_name == "authorization_id":
        return replace(event, authorization_id="AUTH.WRONG")
    if field_name == "attributes.value":
        attributes = dict(event.attributes)
        attributes["value"] = "wrong-value"
        return replace(event, attributes=freeze_attrs(attributes))
    raise ValueError(f"unsupported frozen corruption field: {field_name}")


def _entry_cases(entry: ManifestEntry, ordinal: int) -> tuple[RawCandidateCase, ...]:
    fixture = _fixture_map()[entry.fixture_id]
    event_index = next(
        index
        for index, event in enumerate(fixture.events)
        if event.event_id == entry.event_id
    )
    gold_event = fixture.events[event_index]
    expected_case = next(
        case for case in fixture.cases if case.query.query_id == entry.query_id
    )
    expected_answer = GoldSemantics(fixture.events).answer(expected_case.query)
    context_events = tuple(
        event for index, event in enumerate(fixture.events) if index != event_index
    )
    raw_text = render_event(gold_event, entry.rendering_family)
    corrupted = _corrupt(gold_event, entry.corruption_field)
    prefix = f"X{ordinal:02d}-{entry.fixture_id}"

    common = {
        "topology_family": entry.topology_family,
        "split": entry.split,
        "rendering_family": entry.rendering_family,
        "gold_event": gold_event,
        "context_events": context_events,
        "insertion_index": event_index,
        "query": expected_case.query,
        "expected_answer": expected_answer,
    }

    return (
        RawCandidateCase(
            case_id=f"{prefix}-clean",
            raw_text=raw_text,
            candidate_event=gold_event,
            condition=CandidateCondition.CLEAN,
            mutated_fields=(),
            recoverable_from_raw=True,
            notes="Clean candidate control.",
            **common,
        ),
        RawCandidateCase(
            case_id=f"{prefix}-field",
            raw_text=raw_text,
            candidate_event=corrupted,
            condition=CandidateCondition.FIELD_CORRUPTION,
            mutated_fields=(entry.corruption_field,),
            recoverable_from_raw=True,
            notes="One frozen answer- or invariant-relevant field is corrupted.",
            **common,
        ),
        RawCandidateCase(
            case_id=f"{prefix}-omitted",
            raw_text=raw_text,
            candidate_event=None,
            condition=CandidateCondition.CANDIDATE_OMITTED,
            mutated_fields=("event_omitted",),
            recoverable_from_raw=True,
            notes="Primary extraction omitted an event that remains recoverable from raw evidence.",
            **common,
        ),
        RawCandidateCase(
            case_id=f"{prefix}-raw-unavailable",
            raw_text=None,
            candidate_event=corrupted,
            condition=CandidateCondition.RAW_UNAVAILABLE,
            mutated_fields=(entry.corruption_field,),
            recoverable_from_raw=False,
            notes="Corrupted candidate with no surviving raw evidence.",
            **common,
        ),
    )


def all_raw_verifier_cases() -> tuple[RawCandidateCase, ...]:
    cases: list[RawCandidateCase] = []
    for ordinal, entry in enumerate(FROZEN_MANIFEST, start=1):
        cases.extend(_entry_cases(entry, ordinal))
    return tuple(cases)
