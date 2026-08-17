from __future__ import annotations

from typing import Iterable

from mindmap.canonical.model import CommonEvent

from .generic_observer import GenericObserver as _GenericObserver
from .model import Alert, JournalCommitment, ObserverSurface
from .typed_observer import TypedObserver as _TypedObserver


_ACQUISITION_OPERATIONS = {
    "observe",
    "receive",
    "read",
    "evidence_copy",
    "state_replication",
    "restore",
    "reacquire",
}


def _explicit_source_alerts(
    rows: tuple[CommonEvent, ...], *, rule: str
) -> list[Alert]:
    """Check transfer source exposure without treating evidence authorship as memory."""

    evidence_time = {
        event.object_id: event.system_time
        for event in rows
        if event.event_type == "evidence" and event.object_id
    }
    manifest_members: set[tuple[str, str]] = set()
    for event in rows:
        if (
            event.event_type == "snapshot_member"
            and event.snapshot_id
            and event.object_kind == "evidence"
            and event.object_id
        ):
            attrs = dict(event.attributes)
            if attrs.get("copy_eligible", False) and attrs.get(
                "historically_exposed", False
            ):
                manifest_members.add((event.snapshot_id, event.object_id))

    lineage = [event for event in rows if event.event_type == "lineage"]

    def inherited(
        mind_id: str,
        evidence_id: str,
        system_time: int,
        visited: frozenset[tuple[str, str, int]],
    ) -> bool:
        marker = (mind_id, evidence_id, system_time)
        if marker in visited:
            return False
        visited = visited | {marker}
        for edge in lineage:
            if (
                edge.destination_mind_instance_id != mind_id
                or edge.system_time > system_time
                or edge.snapshot_id is None
                or (edge.snapshot_id, evidence_id) not in manifest_members
            ):
                continue
            cutoff = (
                edge.snapshot_cutoff
                if edge.snapshot_cutoff is not None
                else edge.system_time
            )
            if evidence_time.get(evidence_id, 2**62) <= cutoff:
                return True
            if edge.source_mind_instance_id and inherited(
                edge.source_mind_instance_id, evidence_id, cutoff, visited
            ):
                return True
        return False

    acquired: set[tuple[str, str]] = set()
    alerts: list[Alert] = []
    for event in sorted(rows, key=lambda value: (value.system_time, value.event_id)):
        if (
            event.event_type != "exposure"
            or event.destination_mind_instance_id is None
            or event.object_id is None
        ):
            continue
        source = event.source_mind_instance_id
        if source is not None and (
            source,
            event.object_id,
        ) not in acquired and not inherited(
            source, event.object_id, event.system_time, frozenset()
        ):
            alerts.append(
                Alert(
                    rule,
                    candidate_event_ids=frozenset({event.event_id}),
                    constraint_ids=frozenset({"transfer_source_exposed"}),
                    surface=ObserverSurface.SEMANTIC_JOURNAL,
                )
            )
        if event.transfer_kind in _ACQUISITION_OPERATIONS:
            acquired.add((event.destination_mind_instance_id, event.object_id))
    return alerts


def _normalize_alert_candidates(
    rows: tuple[CommonEvent, ...],
    alerts: Iterable[Alert],
    journal_commitment: JournalCommitment | None,
) -> list[Alert]:
    """Map typed row/object identifiers back to source journal event IDs.

    Localization is scored in the journal event domain. This normalization does
    not change whether a fault is detected; it only makes candidate sets
    comparable across generic and typed physical representations.
    """

    object_to_event: dict[str, str] = {}
    event_by_id = {event.event_id: event for event in rows}
    for event in rows:
        if event.object_id:
            object_to_event[event.object_id] = event.event_id

    normalized: list[Alert] = []
    for alert in alerts:
        original = set(alert.candidate_event_ids)
        candidates = {object_to_event.get(value, value) for value in original}

        if "snapshot_member_post_cutoff" in alert.rule:
            snapshot_ids: set[str] = set()
            for candidate in candidates:
                event = event_by_id.get(candidate)
                if event and event.event_type == "snapshot_member" and event.snapshot_id:
                    snapshot_ids.add(event.snapshot_id)
            for event in rows:
                if event.event_type == "lineage" and event.snapshot_id in snapshot_ids:
                    candidates.add(event.event_id)

        if "sequence_or_membership_mismatch" in alert.rule and journal_commitment:
            actual = tuple(event.event_id for event in rows)
            expected = journal_commitment.ordered_event_ids
            for index in range(max(len(actual), len(expected))):
                actual_id = actual[index] if index < len(actual) else None
                expected_id = expected[index] if index < len(expected) else None
                if actual_id == expected_id:
                    continue
                if actual_id:
                    candidates.add(actual_id)
                if expected_id:
                    candidates.add(expected_id)

        normalized.append(
            Alert(
                rule=alert.rule,
                candidate_event_ids=frozenset(candidates),
                constraint_ids=alert.constraint_ids,
                surface=alert.surface,
                detail=alert.detail,
            )
        )
    return normalized


class GenericObserver(_GenericObserver):
    """Generic observer with complete local identity/context constraints."""

    def inspect(self, events: Iterable[CommonEvent], **kwargs) -> tuple[Alert, ...]:
        rows = tuple(events)
        alerts = list(super().inspect(rows, **kwargs))
        surface = kwargs["surface"]
        if surface >= ObserverSurface.LOCAL_SCHEMA:
            minds = {
                event.object_id: event.actor_principal_id
                for event in rows
                if event.event_type == "mind_create" and event.object_id
            }
            placements = {
                event.object_id
                for event in rows
                if event.event_type == "placement" and event.object_id
            }
            for event in rows:
                if event.event_type != "evidence":
                    continue
                if event.source_placement_id and event.source_placement_id not in placements:
                    alerts.append(
                        Alert(
                            "generic_evidence_unknown_placement",
                            candidate_event_ids=frozenset({event.event_id}),
                            constraint_ids=frozenset({"evidence_placement_fk"}),
                            surface=ObserverSurface.LOCAL_SCHEMA,
                        )
                    )
                if event.actor_mind_instance_id:
                    principal = minds.get(event.actor_mind_instance_id)
                    if (
                        principal is not None
                        and event.actor_principal_id is not None
                        and principal != event.actor_principal_id
                    ):
                        alerts.append(
                            Alert(
                                "generic_actor_principal_mind_mismatch",
                                candidate_event_ids=frozenset({event.event_id}),
                                constraint_ids=frozenset(
                                    {"actor_principal_matches_mind"}
                                ),
                                surface=ObserverSurface.LOCAL_SCHEMA,
                            )
                        )
        if surface >= ObserverSurface.SEMANTIC_JOURNAL:
            alerts.extend(
                _explicit_source_alerts(
                    rows, rule="generic_source_not_explicitly_exposed"
                )
            )
        normalized = _normalize_alert_candidates(
            rows, alerts, kwargs.get("journal_commitment")
        )
        return tuple(self._deduplicate(normalized))


class TypedObserver(_TypedObserver):
    """Typed observer with explicit typed foreign-key and identity checks."""

    def inspect(self, events: Iterable[CommonEvent], **kwargs) -> tuple[Alert, ...]:
        rows = tuple(events)
        alerts = list(super().inspect(rows, **kwargs))
        surface = kwargs["surface"]
        if surface >= ObserverSurface.LOCAL_SCHEMA:
            placement_ids = {
                event.object_id
                for event in rows
                if event.event_type == "placement" and event.object_id is not None
            }
            mind_principal: dict[str, str | None] = {}
            for event in rows:
                if event.event_type == "mind_create" and event.object_id is not None:
                    mind_principal[event.object_id] = event.actor_principal_id
            for event in rows:
                if event.event_type != "evidence":
                    continue
                missing_context = (
                    event.source_placement_id is not None
                    and event.source_placement_id not in placement_ids
                )
                if missing_context:
                    alerts.append(
                        Alert(
                            "typed_evidence_unknown_placement",
                            candidate_event_ids=frozenset({event.event_id}),
                            constraint_ids=frozenset({"evidence_placement_fk"}),
                            surface=ObserverSurface.LOCAL_SCHEMA,
                        )
                    )
                if event.actor_mind_instance_id in mind_principal:
                    expected = mind_principal[event.actor_mind_instance_id]
                    if (
                        expected is not None
                        and event.actor_principal_id is not None
                        and expected != event.actor_principal_id
                    ):
                        alerts.append(
                            Alert(
                                "typed_actor_principal_mind_mismatch",
                                candidate_event_ids=frozenset({event.event_id}),
                                constraint_ids=frozenset(
                                    {"actor_principal_matches_mind"}
                                ),
                                surface=ObserverSurface.LOCAL_SCHEMA,
                            )
                        )
        if surface >= ObserverSurface.SEMANTIC_JOURNAL:
            alerts.extend(
                _explicit_source_alerts(
                    rows, rule="typed_source_not_explicitly_exposed"
                )
            )
        normalized = _normalize_alert_candidates(
            rows, alerts, kwargs.get("journal_commitment")
        )
        return tuple(self._deduplicate(normalized))
