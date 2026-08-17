from __future__ import annotations

from typing import Optional

from .model import TargetQuery


class GoldWorldMixin:
    def _world_definitions(self, system_time: int) -> dict[str, tuple[Optional[str], Optional[int]]]:
        definitions: dict[str, tuple[Optional[str], Optional[int]]] = {}
        for event in self._events_through(system_time):
            if event.event_type != "world_create" or event.object_id is None:
                continue
            attrs = self._attrs(event)
            parent = attrs.get("parent") or None
            raw_fork = attrs.get("fork_valid_time")
            fork = None if raw_fork in {None, "", "None"} else int(raw_fork)
            definitions[event.object_id] = (parent, fork)
        return definitions

    def _world_ancestry(self, branch_id: str, system_time: int) -> list[str]:
        definitions = self._world_definitions(system_time)
        if branch_id not in definitions:
            return []
        ancestry = [branch_id]
        while definitions[ancestry[-1]][0] is not None:
            parent = definitions[ancestry[-1]][0]
            assert parent is not None
            if parent in ancestry:
                raise ValueError("cycle in declarative world fixture")
            if parent not in definitions:
                raise ValueError(f"missing parent world: {parent}")
            ancestry.append(parent)
        return list(reversed(ancestry))

    def _answer_world(self, query: TargetQuery) -> str:
        if query.proposition_id is None or query.world_branch_id is None:
            return "unknown"
        definitions = self._world_definitions(query.system_time)
        ancestry = self._world_ancestry(query.world_branch_id, query.system_time)
        if not ancestry:
            return "unknown"

        # Determine the world-time projection for each ancestor. The child is
        # evaluated at the query time. Every ancestor is capped at the minimum
        # fork valid time below it.
        projected_time = {query.world_branch_id: query.valid_time}
        running = query.valid_time
        for index in range(len(ancestry) - 1, 0, -1):
            child = ancestry[index]
            fork = definitions[child][1]
            if fork is not None:
                running = min(running, fork)
            projected_time[ancestry[index - 1]] = running

        selected_value: Optional[str] = None
        for branch in ancestry:
            tv = projected_time[branch]
            assignments = []
            for event in self._events_through(query.system_time):
                if event.event_type != "world_claim":
                    continue
                if event.proposition_id != query.proposition_id or event.about_world_branch_id != branch:
                    continue
                if not self._active(event, tv):
                    continue
                attrs = self._attrs(event)
                if attrs.get("status", "active") != "active":
                    continue
                assignments.append(event)
            if assignments:
                chosen = max(assignments, key=lambda e: (e.valid_from, e.system_time, e.event_id))
                selected_value = self._attrs(chosen).get("value", "unknown")
        return selected_value if selected_value is not None else "unknown"
