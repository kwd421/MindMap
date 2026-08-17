from __future__ import annotations

from typing import Iterable, Optional

from .model import CommonEvent, TargetQuery, sorted_events


class GenericBase:
    implementation_name = "G_generic_event_ledger"

    def __init__(self, events: Iterable[CommonEvent]):
        self.events = sorted_events(events)
        ids = [event.event_id for event in self.events]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate CommonEvent.event_id")
        self.by_id = {event.event_id: event for event in self.events}
        self.evidence_by_id = {event.object_id: event for event in self.events if event.event_type == "evidence" and event.object_id is not None}

    @staticmethod
    def _attrs(event: CommonEvent) -> dict[str, str]:
        return dict(event.attributes)

    def _visible(self, query: TargetQuery, event_type: Optional[str] = None) -> list[CommonEvent]:
        return [
            event
            for event in self.events
            if event.system_time <= query.system_time and (event_type is None or event.event_type == event_type)
        ]
