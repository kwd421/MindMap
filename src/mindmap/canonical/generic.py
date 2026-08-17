from __future__ import annotations

from .generic_base import GenericBase
from .generic_provenance import GenericProvenanceMixin
from .generic_state import GenericStateMixin
from .generic_world import GenericWorldMixin
from .model import Answer, TargetQuery, TargetSpace


class GenericLedger(GenericWorldMixin, GenericStateMixin, GenericProvenanceMixin, GenericBase):
    """Complete equal-information generic event-ledger implementation (G)."""

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
