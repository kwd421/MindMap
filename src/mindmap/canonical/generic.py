from __future__ import annotations

from typing import Optional

from .generic_base import GenericBase
from .generic_provenance import GenericProvenanceMixin
from .generic_state import GenericStateMixin
from .generic_world import GenericWorldMixin
from .model import Answer, CommonEvent, TargetQuery, TargetSpace


class GenericLedger(GenericWorldMixin, GenericStateMixin, GenericProvenanceMixin, GenericBase):
    """Complete equal-information generic event-ledger implementation (G)."""

    def _authorization_active(
        self,
        authorization_id: Optional[str],
        at_system_time: int,
        *,
        source_mind_instance_id: Optional[str] = None,
        destination_mind_instance_id: Optional[str] = None,
    ) -> bool:
        """Resolve one scoped authorization without inventing a same-time order.

        Authorization identifiers represent one stable source/destination grant.
        Reusing an identifier for another scope is invalid. Conflicting revisions
        at the same transaction/system time are ambiguous because the canonical
        v0.2 input has no independent journal-sequence field that could order
        them; fail closed instead of using event-id spelling as semantics.
        """

        if not authorization_id:
            return False
        events = [
            event
            for event in self.events
            if event.event_type == "authorization"
            and event.object_id == authorization_id
            and event.system_time <= at_system_time
        ]
        if not events:
            return False

        scopes = {
            (event.source_mind_instance_id, event.destination_mind_instance_id)
            for event in events
        }
        if len(scopes) != 1:
            raise ValueError(f"authorization scope changed: {authorization_id}")
        scope = next(iter(scopes))
        if source_mind_instance_id is not None or destination_mind_instance_id is not None:
            if scope != (source_mind_instance_id, destination_mind_instance_id):
                return False

        latest_time = max(event.system_time for event in events)
        latest = [event for event in events if event.system_time == latest_time]
        operations = {
            event.policy_operation or self._attrs(event).get("status", "revoke")
            for event in latest
        }
        if len(operations) != 1:
            raise ValueError(
                f"ambiguous same-time authorization revisions: {authorization_id}"
            )
        return next(iter(operations)) == "grant"

    def _lineage_authorizes_replication(self, exposure: CommonEvent) -> bool:
        source = exposure.source_mind_instance_id
        destination = exposure.destination_mind_instance_id
        if source is None or destination is None:
            return False
        principals = self._mind_principals(exposure.system_time)
        if principals.get(source) is None or principals.get(source) != principals.get(destination):
            return False
        if not self._authorization_active(
            exposure.authorization_id,
            exposure.system_time,
            source_mind_instance_id=source,
            destination_mind_instance_id=destination,
        ):
            return False
        return any(
            event.event_type == "lineage"
            and event.system_time <= exposure.system_time
            and event.source_mind_instance_id == source
            and event.destination_mind_instance_id == destination
            and event.lineage_kind in {"operational_replica", "checkpoint_branch"}
            for event in self.events
        )

    def answer(self, query: TargetQuery) -> Answer:
        if query.target_space is TargetSpace.WORLD:
            return self._world(query)
        if query.target_space is TargetSpace.EVER_EXPOSED:
            return self._ever_exposed(query)
        if query.target_space is TargetSpace.AVAILABLE:
            return self._available(query)
        if query.target_space is TargetSpace.ATTITUDE:
            return self._attitude(query)
        if query.target_space is TargetSpace.ATTRIBUTION:
            return self._attribution(query)
        if query.target_space is TargetSpace.DISCLOSE:
            return bool(self._admissible_justifications(query))
        if query.target_space is TargetSpace.JUSTIFICATION:
            return tuple(self._admissible_justifications(query))
        raise ValueError(f"unsupported target space: {query.target_space}")
