from __future__ import annotations

from typing import Iterable

from .model import CommonEvent, validate_temporal_references


class GoldBase:
    implementation_name = "Gold_declarative_reference"

    def __init__(self, events: Iterable[CommonEvent]):
        input_events = tuple(events)
        validate_temporal_references(input_events)
        self.log = tuple(sorted(input_events, key=lambda e: (e.system_time, e.event_id)))
        ids = [event.event_id for event in self.log]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate event id in gold fixture")
        self.event_by_id = {event.event_id: event for event in self.log}
        self.evidence_by_id = {event.object_id: event for event in self.log if event.event_type == "evidence" and event.object_id is not None}

    @staticmethod
    def _attrs(event: CommonEvent) -> dict[str, str]:
        return {key: value for key, value in event.attributes}

    @staticmethod
    def _active(event: CommonEvent, valid_time: int) -> bool:
        return event.valid_from <= valid_time and (event.valid_to is None or valid_time < event.valid_to)

    def _events_through(self, system_time: int) -> list[CommonEvent]:
        return [event for event in self.log if event.system_time <= system_time]
