from __future__ import annotations

from typing import Optional

from .typed_projection import TypedProjectionMixin
from .typed_resolution import TypedResolutionMixin
from .typed_rows import ExposureRow


class TypedLedger(TypedResolutionMixin, TypedProjectionMixin):
    """Normalized typed implementation (T) of the canonical finite semantics."""

    def _authorization_active(
        self,
        auth_id: Optional[str],
        system_time: int,
        *,
        source_mind_instance_id: Optional[str] = None,
        destination_mind_instance_id: Optional[str] = None,
    ) -> bool:
        if auth_id is None:
            return False
        rows = [
            row
            for row in self.authorizations
            if row.authorization_id == auth_id
            and row.recorded_system_time <= system_time
        ]
        if not rows:
            return False

        scopes = {
            (row.source_mind_instance_id, row.destination_mind_instance_id)
            for row in rows
        }
        if len(scopes) != 1:
            raise ValueError(f"authorization scope changed: {auth_id}")
        scope = next(iter(scopes))
        if source_mind_instance_id is not None or destination_mind_instance_id is not None:
            if scope != (source_mind_instance_id, destination_mind_instance_id):
                return False

        latest_time = max(row.recorded_system_time for row in rows)
        latest = [row for row in rows if row.recorded_system_time == latest_time]
        operations = {row.operation for row in latest}
        if len(operations) != 1:
            raise ValueError(f"ambiguous same-time authorization revisions: {auth_id}")
        return next(iter(operations)) == "grant"

    def _replication_eligible(self, row: ExposureRow) -> bool:
        source_id = row.source_mind_instance_id
        destination_id = row.destination_mind_instance_id
        if not source_id:
            return False
        source = self.minds.get(source_id)
        destination = self.minds.get(destination_id)
        if source is None or destination is None or source.principal_id != destination.principal_id:
            return False
        if not self._authorization_active(
            row.authorization_id,
            row.recorded_system_time,
            source_mind_instance_id=source_id,
            destination_mind_instance_id=destination_id,
        ):
            return False
        return any(
            edge.source_mind_instance_id == source_id
            and edge.destination_mind_instance_id == destination_id
            and edge.created_system_time <= row.recorded_system_time
            and edge.kind in {"operational_replica", "checkpoint_branch"}
            for edge in self.lineage
        )
