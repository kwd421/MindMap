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
from .v02_verifier_adapter import NormalizedDevelopmentVerifier


@dataclass(frozen=True, slots=True)
class V02Case:
    record: RawPassageRecord
    gold_event: CommonEvent
    context_events: tuple[CommonEvent, ...]
    insertion_index: int
    query: TargetQuery
    expected_answer: Answer
    primary_extraction: PrimaryExtraction
    controlled_candidate_event: CommonEvent | None
    primary_verifier_decision: VerificationDecision
    controlled_verifier_decision: VerificationDecision

    def events_with(self, event: CommonEvent | None) -> tuple[CommonEvent, ...]:
        rows = list(self.context_events)
        if event is not None:
            rows.insert(self.insertion_index, event)
        return tuple(rows)


# Compatibility alias for existing development-only callers.
V02DevelopmentCase = V02Case


_EXPECTED_CONTROLLED_STATUSES = {
    PassageCondition.CLEAN: VerificationStatus.ACCEPT,
    PassageCondition.FIELD_CORRUPTION: VerificationStatus.CORRECT,
    PassageCondition.CANDIDATE_OMITTED: VerificationStatus.CORRECT,
    PassageCondition.RAW_UNAVAILABLE: VerificationStatus.ABSTAIN,
    PassageCondition.AMBIGUOUS_RAW: VerificationStatus.ABSTAIN,
    PassageCondition.MISLEADING_CONTEXT: VerificationStatus.CORRECT,
}

_EXPECTED_PRIMARY_STATUSES = {
    PassageCondition.CLEAN: VerificationStatus.ACCEPT,
    PassageCondition.FIELD_CORRUPTION: VerificationStatus.ACCEPT,
    PassageCondition.CANDIDATE_OMITTED: VerificationStatus.ACCEPT,
    PassageCondition.RAW_UNAVAILABLE: VerificationStatus.ABSTAIN,
    PassageCondition.AMBIGUOUS_RAW: VerificationStatus.ABSTAIN,
    PassageCondition.MISLEADING_CONTEXT: VerificationStatus.ACCEPT,
}


def expected_controlled_status(condition: PassageCondition) -> VerificationStatus:
    return _EXPECTED_CONTROLLED_STATUSES[condition]


def expected_primary_status(condition: PassageCondition) -> VerificationStatus:
    return _EXPECTED_PRIMARY_STATUSES[condition]


def _fixture_map() -> dict[str, Fixture]:
    return {fixture.fixture_id: fixture for fixture in all_fixtures()}


def _controlled_candidate_for(
    record: RawPassageRecord,
    gold_event: CommonEvent,
) -> CommonEvent | None:
    """Construct a controlled candidate independently of primary extraction."""

    if record.candidate_condition is PassageCondition.CLEAN:
        return gold_event
    if record.candidate_condition is PassageCondition.CANDIDATE_OMITTED:
        return None
    mutation = record.candidate_mutation
    if mutation is None:
        raise ValueError(f"{record.passage_id} lacks required candidate mutation")
    return apply_candidate_mutation(gold_event, mutation)


def _verify(
    *,
    verifier: DevelopmentIndependentVerifier,
    record: RawPassageRecord,
    candidate: CommonEvent | None,
    context_events: tuple[CommonEvent, ...],
    insertion_index: int,
) -> VerificationDecision:
    return verifier.verify(
        V02VerifierInput(
            raw_text=record.raw_text,
            context_passages=record.context_passages,
            candidate_event=candidate,
            context_events=context_events,
            insertion_index=insertion_index,
        )
    )


def build_cases_from_records(
    records: tuple[RawPassageRecord, ...],
    *,
    primary_extractor: DevelopmentPrimaryExtractor | None = None,
    verifier: DevelopmentIndependentVerifier | None = None,
) -> tuple[V02Case, ...]:
    """Apply one frozen primary/verifier implementation to either split."""

    primary_extractor = primary_extractor or DevelopmentPrimaryExtractor()
    verifier = verifier or NormalizedDevelopmentVerifier()
    fixtures = _fixture_map()
    cases: list[V02Case] = []

    for record in records:
        fixture = fixtures.get(record.fixture_id)
        if fixture is None:
            raise ValueError(f"unknown canonical fixture: {record.fixture_id}")
        if fixture.family != record.topology_family:
            raise ValueError(
                f"passage topology {record.topology_family} does not match "
                f"fixture family {fixture.family}"
            )
        try:
            insertion_index = next(
                index
                for index, event in enumerate(fixture.events)
                if event.event_id == record.event_id
            )
        except StopIteration as exc:
            raise ValueError(
                f"{record.passage_id} references unknown event {record.event_id}"
            ) from exc
        gold_event = fixture.events[insertion_index]
        context_events = tuple(
            event
            for index, event in enumerate(fixture.events)
            if index != insertion_index
        )
        try:
            expected_case = next(
                case
                for case in fixture.cases
                if case.query.query_id == record.query_id
            )
        except StopIteration as exc:
            raise ValueError(
                f"{record.passage_id} references unknown query {record.query_id}"
            ) from exc
        expected_answer = GoldSemantics(fixture.events).answer(expected_case.query)
        primary = primary_extractor.extract(record.raw_text)
        controlled_candidate = _controlled_candidate_for(record, gold_event)
        primary_decision = _verify(
            verifier=verifier,
            record=record,
            candidate=primary.event,
            context_events=context_events,
            insertion_index=insertion_index,
        )
        controlled_decision = _verify(
            verifier=verifier,
            record=record,
            candidate=controlled_candidate,
            context_events=context_events,
            insertion_index=insertion_index,
        )
        cases.append(
            V02Case(
                record=record,
                gold_event=gold_event,
                context_events=context_events,
                insertion_index=insertion_index,
                query=expected_case.query,
                expected_answer=expected_answer,
                primary_extraction=primary,
                controlled_candidate_event=controlled_candidate,
                primary_verifier_decision=primary_decision,
                controlled_verifier_decision=controlled_decision,
            )
        )
    return tuple(cases)


def build_cases_from_bundle_file(
    bundle_path: Path,
    *,
    split: str,
    primary_extractor: DevelopmentPrimaryExtractor | None = None,
    verifier: DevelopmentIndependentVerifier | None = None,
) -> tuple[V02Case, ...]:
    bundles = load_bundle_json(bundle_path, split=split)
    records = expand_bundles(bundles, split=split)
    return build_cases_from_records(
        records,
        primary_extractor=primary_extractor,
        verifier=verifier,
    )


def build_development_cases(
    *,
    repository_root: Path,
    primary_extractor: DevelopmentPrimaryExtractor | None = None,
    verifier: DevelopmentIndependentVerifier | None = None,
) -> tuple[V02Case, ...]:
    bundle_path = (
        repository_root
        / "data"
        / "track_x_v02"
        / "development"
        / "session_b.json"
    )
    return build_cases_from_bundle_file(
        bundle_path,
        split="development",
        primary_extractor=primary_extractor,
        verifier=verifier,
    )


def build_heldout_cases(
    *,
    repository_root: Path,
    primary_extractor: DevelopmentPrimaryExtractor | None = None,
    verifier: DevelopmentIndependentVerifier | None = None,
) -> tuple[V02Case, ...]:
    bundle_path = (
        repository_root
        / "data"
        / "track_x_v02"
        / "heldout"
        / "session_a.json"
    )
    return build_cases_from_bundle_file(
        bundle_path,
        split="heldout",
        primary_extractor=primary_extractor,
        verifier=verifier,
    )
