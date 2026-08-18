from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mindmap.canonical.fixtures import all_fixtures
from mindmap.canonical.gold import GoldSemantics
from mindmap.canonical.model import Answer, CommonEvent, Fixture, TargetQuery

from .model import VerificationDecision, VerificationStatus
from .v02_bundles import expand_bundles, load_bundle_json
from .v02_data import PassageCondition, RawPassageRecord
from .v02_pipeline import (
    DevelopmentIndependentVerifier,
    DevelopmentPrimaryExtractor,
    PrimaryExtraction,
    V02VerifierInput,
    apply_candidate_mutation,
)


@dataclass(frozen=True, slots=True)
class V02DevelopmentCase:
    record: RawPassageRecord
    gold_event: CommonEvent
    context_events: tuple[CommonEvent, ...]
    insertion_index: int
    query: TargetQuery
    expected_answer: Answer
    primary_extraction: PrimaryExtraction
    candidate_event: CommonEvent | None
    verifier_decision: VerificationDecision

    def events_with(self, event: CommonEvent | None) -> tuple[CommonEvent, ...]:
        rows = list(self.context_events)
        if event is not None:
            rows.insert(self.insertion_index, event)
        return tuple(rows)


_EXPECTED_STATUSES = {
    PassageCondition.CLEAN: VerificationStatus.ACCEPT,
    PassageCondition.FIELD_CORRUPTION: VerificationStatus.CORRECT,
    PassageCondition.CANDIDATE_OMITTED: VerificationStatus.CORRECT,
    PassageCondition.RAW_UNAVAILABLE: VerificationStatus.ABSTAIN,
    PassageCondition.AMBIGUOUS_RAW: VerificationStatus.ABSTAIN,
    PassageCondition.MISLEADING_CONTEXT: VerificationStatus.CORRECT,
}


def expected_status(condition: PassageCondition) -> VerificationStatus:
    return _EXPECTED_STATUSES[condition]


def _fixture_map() -> dict[str, Fixture]:
    return {fixture.fixture_id: fixture for fixture in all_fixtures()}


def _candidate_for(
    record: RawPassageRecord,
    gold_event: CommonEvent,
    primary: PrimaryExtraction,
) -> CommonEvent | None:
    if record.candidate_condition is PassageCondition.CLEAN:
        return primary.event
    if record.candidate_condition is PassageCondition.CANDIDATE_OMITTED:
        return None
    mutation = record.candidate_mutation
    if mutation is None:
        raise ValueError(f"{record.passage_id} lacks required candidate mutation")
    source = primary.event if primary.event is not None else gold_event
    return apply_candidate_mutation(source, mutation)


def build_development_cases(
    *,
    repository_root: Path,
    primary_extractor: DevelopmentPrimaryExtractor | None = None,
    verifier: DevelopmentIndependentVerifier | None = None,
) -> tuple[V02DevelopmentCase, ...]:
    primary_extractor = primary_extractor or DevelopmentPrimaryExtractor()
    verifier = verifier or DevelopmentIndependentVerifier()
    bundle_path = (
        repository_root
        / "data"
        / "track_x_v02"
        / "development"
        / "session_b.json"
    )
    bundles = load_bundle_json(bundle_path, split="development")
    records = expand_bundles(bundles, split="development")
    fixtures = _fixture_map()
    cases: list[V02DevelopmentCase] = []

    for record in records:
        fixture = fixtures[record.fixture_id]
        insertion_index = next(
            index
            for index, event in enumerate(fixture.events)
            if event.event_id == record.event_id
        )
        gold_event = fixture.events[insertion_index]
        context_events = tuple(
            event
            for index, event in enumerate(fixture.events)
            if index != insertion_index
        )
        expected_case = next(
            case for case in fixture.cases if case.query.query_id == record.query_id
        )
        expected_answer = GoldSemantics(fixture.events).answer(expected_case.query)
        primary = primary_extractor.extract(record.raw_text)
        candidate = _candidate_for(record, gold_event, primary)
        verifier_input = V02VerifierInput(
            raw_text=record.raw_text,
            context_passages=record.context_passages,
            candidate_event=candidate,
            context_events=context_events,
            insertion_index=insertion_index,
        )
        decision = verifier.verify(verifier_input)
        cases.append(
            V02DevelopmentCase(
                record=record,
                gold_event=gold_event,
                context_events=context_events,
                insertion_index=insertion_index,
                query=expected_case.query,
                expected_answer=expected_answer,
                primary_extraction=primary,
                candidate_event=candidate,
                verifier_decision=decision,
            )
        )
    return tuple(cases)
