from __future__ import annotations

from typing import Optional

from .model import TargetQuery
from .typed_rows import EvidenceRow, JustificationRow, POLICY_ORDER, REQUESTER_LEVEL


class TypedProvenanceResolutionMixin:
    def _active_justifications(
        self, proposition_id: str, system_time: int
    ) -> list[JustificationRow]:
        latest: dict[str, JustificationRow] = {}
        for justification in self.justifications:
            if (
                justification.proposition_id != proposition_id
                or justification.recorded_system_time > system_time
            ):
                continue
            current = latest.get(justification.justification_id)
            if current is None or (
                justification.recorded_system_time,
                justification.justification_id,
            ) >= (
                current.recorded_system_time,
                current.justification_id,
            ):
                latest[justification.justification_id] = justification
        return [value for value in latest.values() if value.status == "active"]

    def _admissible_justifications(self, query: TargetQuery) -> list[str]:
        if query.proposition_id is None:
            return []
        clearance = REQUESTER_LEVEL.get(query.requester_id or "public_user", 0)
        admissible: list[str] = []
        for justification in self._active_justifications(
            query.proposition_id, query.system_time
        ):
            labels: list[int] = []
            families: set[str] = set()
            active = True
            for member_id in justification.members:
                member: Optional[EvidenceRow] = self.evidence.get(member_id)
                if member is None or member.recorded_system_time > query.system_time:
                    active = False
                    break
                label, _, member_active = self._object_policy_state(
                    member_id, query.system_time
                )
                if not member_active:
                    active = False
                    break
                labels.append(POLICY_ORDER.get(label, POLICY_ORDER["blocked"]))
                families.add(member.origin_family_id)
            if not active or len(families) < justification.min_independent_sources:
                continue
            if max(labels, default=0) <= clearance:
                admissible.append(justification.justification_id)
        return sorted(admissible)
