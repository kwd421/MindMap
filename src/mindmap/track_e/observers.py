from __future__ import annotations

from typing import Iterable

from mindmap.canonical.model import CommonEvent

from .generic_observer import GenericObserver as _GenericObserver
from .model import Alert, ObserverSurface
from .typed_observer import TypedObserver as _TypedObserver


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
        return tuple(self._deduplicate(alerts))


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
        return tuple(self._deduplicate(alerts))
