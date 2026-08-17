from __future__ import annotations

from .gold_base import GoldBase
from .gold_provenance import GoldProvenanceMixin
from .gold_state import GoldStateMixin
from .gold_world import GoldWorldMixin
from .model import Answer, TargetQuery, TargetSpace


class GoldSemantics(GoldWorldMixin, GoldStateMixin, GoldProvenanceMixin, GoldBase):
    """Independent declarative reference semantics for Track S."""

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
