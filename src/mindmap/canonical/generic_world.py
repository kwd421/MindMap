from __future__ import annotations

from typing import Optional

from .model import TargetQuery


class GenericWorldMixin:
    def _branch_table(self, system_time: int) -> dict[str, tuple[Optional[str], Optional[int], int]]:
        table: dict[str, tuple[Optional[str], Optional[int], int]] = {}
        for event in self.events:
            if event.system_time > system_time or event.event_type != "world_create" or event.object_id is None:
                continue
            attrs = self._attrs(event)
            parent = attrs.get("parent") or None
            fork_valid = int(attrs["fork_valid_time"]) if attrs.get("fork_valid_time") not in {None, "", "None"} else None
            table[event.object_id] = (parent, fork_valid, event.system_time)
        return table

    def _branch_path(self, branch_id: str, system_time: int) -> list[tuple[str, int]]:
        """Return root->query branch and each branch's effective valid time.

        For an ancestor, effective valid time is capped at the minimum fork
        valid time on the path. A later system import about pre-fork state can
        therefore alter a later reconstruction, while post-fork parent world
        updates do not leak to the child.
        """
        table = self._branch_table(system_time)
        if branch_id not in table:
            return [(branch_id, 2**62)]
        reverse: list[tuple[str, Optional[int]]] = []
        current = branch_id
        seen: set[str] = set()
        while True:
            if current in seen:
                raise ValueError("world branch cycle")
            seen.add(current)
            parent, fork_valid, _ = table[current]
            reverse.append((current, fork_valid))
            if parent is None:
                break
            if parent not in table:
                raise ValueError(f"missing parent world branch: {parent}")
            current = parent
        reverse.reverse()
        return [(branch, fork or 2**62) for branch, fork in reverse]

    def _world(self, query: TargetQuery) -> str:
        if query.proposition_id is None or query.world_branch_id is None:
            return "unknown"
        path = self._branch_path(query.world_branch_id, query.system_time)
        # Compute the effective valid-time cap for each ancestor.
        cap = query.valid_time
        effective: dict[str, int] = {query.world_branch_id: query.valid_time}
        for index in range(len(path) - 1, 0, -1):
            child, child_fork = path[index]
            del child
            cap = min(cap, child_fork)
            effective[path[index - 1][0]] = cap

        winner: Optional[CommonEvent] = None
        winner_depth = -1
        for depth, (branch, _) in enumerate(path):
            tv = effective.get(branch, query.valid_time)
            candidates = [
                event
                for event in self._visible(query, "world_claim")
                if event.proposition_id == query.proposition_id
                and event.about_world_branch_id == branch
                and event.active_at(tv)
                and self._attrs(event).get("status", "active") == "active"
            ]
            if not candidates:
                continue
            local = max(candidates, key=lambda event: (event.valid_from, event.system_time, event.event_id))
            if depth >= winner_depth:
                winner = local
                winner_depth = depth
        return self._attrs(winner).get("value", "unknown") if winner else "unknown"
