from __future__ import annotations

from typing import Optional

from .gold_base import GoldBase
from .gold_provenance import GoldProvenanceMixin
from .gold_state import GoldStateMixin
from .gold_world import GoldWorldMixin
from .model import Answer, CommonEvent, TargetQuery, TargetSpace


class GoldSemantics(GoldWorldMixin, GoldStateMixin, GoldProvenanceMixin, GoldBase):
    """Independent declarative reference semantics for Track S."""

    def _auth_granted(
        self,
        authorization_id: Optional[str],
        system_time: int,
        *,
        source_mind_instance_id: Optional[str] = None,
        destination_mind_instance_id: Optional[str] = None,
    ) -> bool:
        if authorization_id is None:
            return False
        history = [
            event
            for event in self._events_through(system_time)
            if event.event_type == "authorization" and event.object_id == authorization_id
        ]
        if not history:
            return False

        scopes = {
            (event.source_mind_instance_id, event.destination_mind_instance_id)
            for event in history
        }
        if len(scopes) != 1:
            raise ValueError(f"authorization scope changed: {authorization_id}")
        scope = next(iter(scopes))
        if source_mind_instance_id is not None or destination_mind_instance_id is not None:
            if scope != (source_mind_instance_id, destination_mind_instance_id):
                return False

        latest_time = max(event.system_time for event in history)
        latest = [event for event in history if event.system_time == latest_time]
        operations = {
            event.policy_operation or self._attrs(event).get("status", "revoke")
            for event in latest
        }
        if len(operations) != 1:
            raise ValueError(
                f"ambiguous same-time authorization revisions: {authorization_id}"
            )
        return next(iter(operations)) == "grant"

    def _valid_replication(self, event: CommonEvent) -> bool:
        source = event.source_mind_instance_id
        destination = event.destination_mind_instance_id
        if source is None or destination is None:
            return False
        principals = self._mind_principals(event.system_time)
        if principals.get(source) is None or principals.get(source) != principals.get(destination):
            return False
        if not self._auth_granted(
            event.authorization_id,
            event.system_time,
            source_mind_instance_id=source,
            destination_mind_instance_id=destination,
        ):
            return False
        return any(
            candidate.event_type == "lineage"
            and candidate.source_mind_instance_id == source
            and candidate.destination_mind_instance_id == destination
            and candidate.lineage_kind in {"operational_replica", "checkpoint_branch"}
            for candidate in self._events_through(event.system_time)
        )

    def answer(self, query: TargetQuery) -> Answer:
        if query.target_space == TargetSpace.WORLD:
            return self._answer_world(query)
        if query.target_space == TargetSpace.EVER_EXPOSED:
            return self._answer_ever_exposed(query)
        if query.target_space == TargetSpace.AVAILABLE:
            return self._answer_available(query)
        if query.target_space == TargetSpace.ATTITUDE:
            return self._answer_attitude(query)
        if query.target_space == TargetSpace.ATTRIBUTION:
            return self._answer_attribution(query)
        if query.target_space == TargetSpace.DISCLOSE:
            return len(self._answer_justifications(query)) > 0
        if query.target_space == TargetSpace.JUSTIFICATION:
            return tuple(self._answer_justifications(query))
        raise AssertionError(query.target_space)
