from __future__ import annotations

from typing import Optional

from .model import TargetQuery
from .typed_rows import WorldClaimRow


class TypedWorldResolutionMixin:
    def _branch_path(self, branch_id: str, system_time: int) -> list[tuple[str, int]]:
        visible = {
            key: branch
            for key, branch in self.branches.items()
            if branch.fork_system_time <= system_time
        }
        if branch_id not in visible:
            return [(branch_id, 2**62)]

        reverse: list[tuple[str, Optional[int]]] = []
        current = branch_id
        seen: set[str] = set()
        while True:
            if current in seen:
                raise ValueError("world branch cycle")
            seen.add(current)
            branch = visible[current]
            reverse.append((current, branch.fork_valid_time))
            parent = branch.parent_world_branch_id
            if parent is None:
                break
            if parent not in visible:
                raise ValueError(f"missing parent world branch: {parent}")
            current = parent
        reverse.reverse()
        return [(key, cutoff or 2**62) for key, cutoff in reverse]

    @staticmethod
    def _world_claim_active(
        claim: WorldClaimRow, valid_time: int, system_time: int
    ) -> bool:
        return (
            claim.recorded_system_time <= system_time
            and claim.valid_from <= valid_time
            and (claim.valid_to is None or valid_time < claim.valid_to)
            and claim.status == "active"
        )

    def _world(self, query: TargetQuery) -> str:
        if query.proposition_id is None or query.world_branch_id is None:
            return "unknown"

        path = self._branch_path(query.world_branch_id, query.system_time)
        effective = {query.world_branch_id: query.valid_time}
        cap = query.valid_time
        for index in range(len(path) - 1, 0, -1):
            _, child_fork = path[index]
            cap = min(cap, child_fork)
            effective[path[index - 1][0]] = cap

        winner: Optional[WorldClaimRow] = None
        winner_depth = -1
        for depth, (branch_id, _) in enumerate(path):
            valid_time = effective.get(branch_id, query.valid_time)
            candidates = [
                claim
                for claim in self.world_claims
                if claim.proposition_id == query.proposition_id
                and claim.about_world_branch_id == branch_id
                and self._world_claim_active(claim, valid_time, query.system_time)
            ]
            if not candidates:
                continue
            local = max(
                candidates,
                key=lambda claim: (
                    claim.valid_from,
                    claim.recorded_system_time,
                    claim.revision_id,
                ),
            )
            if depth >= winner_depth:
                winner = local
                winner_depth = depth
        return winner.value if winner else "unknown"
