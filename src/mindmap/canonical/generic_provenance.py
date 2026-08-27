from __future__ import annotations

from .model import CommonEvent, TargetQuery


_POLICY_RANK = {"public": 0, "private": 1, "sealed": 2, "blocked": 3}
_CLEARANCE = {"public_user": 0, "trusted_user": 1, "admin": 3}


class GenericProvenanceMixin:
    def _policy_label_for_member(self, member_id: str, system_time: int) -> tuple[str, bool]:
        label, _, active = self._object_policy_state(member_id, system_time)
        return label, active

    def _active_justifications(self, proposition_id: str, system_time: int) -> list[CommonEvent]:
        latest: dict[str, CommonEvent] = {}
        for event in self.events:
            if (
                event.event_type == "justification"
                and event.proposition_id == proposition_id
                and event.object_id
                and event.system_time <= system_time
            ):
                current = latest.get(event.object_id)
                if current is None or (event.system_time, event.event_id) > (current.system_time, current.event_id):
                    latest[event.object_id] = event
        return [
            event
            for event in latest.values()
            if self._attrs(event).get("status", "active") == "active"
            and event.policy_operation not in {"revoke", "invalidate"}
        ]

    def _admissible_justifications(self, query: TargetQuery) -> list[str]:
        if query.proposition_id is None:
            return []
        clearance = _CLEARANCE.get(query.requester_id or "public_user", 0)
        admissible: list[str] = []
        for justification in self._active_justifications(query.proposition_id, query.system_time):
            labels: list[int] = []
            active = True
            families: set[str] = set()
            for member_id in justification.derivation_members:
                member = self.evidence_by_id.get(member_id) or self.by_id.get(member_id)
                if member is None or member.system_time > query.system_time:
                    active = False
                    break
                label, member_active = self._policy_label_for_member(member_id, query.system_time)
                if not member_active:
                    active = False
                    break
                labels.append(_POLICY_RANK.get(label, _POLICY_RANK["blocked"]))
                families.add(member.source_family_id or member.event_id)
            min_sources = int(self._attrs(justification).get("min_independent_sources", "1"))
            if not active or len(families) < min_sources:
                continue
            strictest = max(labels, default=0)
            if strictest <= clearance:
                admissible.append(justification.object_id or "")
        return sorted(admissible)
