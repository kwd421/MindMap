from __future__ import annotations

from .model import TargetQuery


class TypedAttitudeResolutionMixin:
    def _snapshot_attitudes(
        self,
        mind_id: str,
        proposition_id: str,
        about_branch: str,
        system_time: int,
        valid_time: int,
    ) -> list[tuple[int, str, str]]:
        output: list[tuple[int, str, str]] = []
        for edge in self.lineage:
            if (
                edge.destination_mind_instance_id != mind_id
                or edge.created_system_time > system_time
                or edge.snapshot_id is None
            ):
                continue
            cutoff = (
                edge.cutoff_system_time
                if edge.cutoff_system_time is not None
                else edge.created_system_time
            )
            for member in self.snapshot_manifest:
                if (
                    member.snapshot_id != edge.snapshot_id
                    or member.object_kind != "attitude"
                    or member.recorded_system_time > edge.created_system_time
                    or not member.copy_eligible
                ):
                    continue
                candidates = [
                    attitude
                    for attitude in self.attitudes
                    if attitude.revision_id == member.object_id
                    and attitude.recorded_system_time <= cutoff
                    and attitude.proposition_id == proposition_id
                    and attitude.about_world_branch_id == about_branch
                    and attitude.valid_from <= valid_time
                    and (
                        attitude.valid_to is None or valid_time < attitude.valid_to
                    )
                ]
                if not candidates:
                    continue
                source = max(
                    candidates,
                    key=lambda value: (
                        value.recorded_system_time,
                        value.revision_id,
                    ),
                )
                output.append(
                    (edge.created_system_time, edge.lineage_edge_id, source.attitude)
                )
        return output

    def _attitude(self, query: TargetQuery) -> str:
        if (
            query.mind_instance_id is None
            or query.proposition_id is None
            or query.world_branch_id is None
        ):
            return "unknown"

        candidates: list[tuple[int, str, str]] = []
        for attitude in self.attitudes:
            if (
                attitude.recorded_system_time <= query.system_time
                and attitude.holder_mind_instance_id == query.mind_instance_id
                and attitude.proposition_id == query.proposition_id
                and attitude.about_world_branch_id == query.world_branch_id
                and attitude.valid_from <= query.valid_time
                and (
                    attitude.valid_to is None or query.valid_time < attitude.valid_to
                )
            ):
                candidates.append(
                    (
                        attitude.recorded_system_time,
                        attitude.revision_id,
                        attitude.attitude,
                    )
                )
        candidates.extend(
            self._snapshot_attitudes(
                query.mind_instance_id,
                query.proposition_id,
                query.world_branch_id,
                query.system_time,
                query.valid_time,
            )
        )
        if not candidates:
            return "unknown"
        return max(candidates, key=lambda value: (value[0], value[1]))[2]
