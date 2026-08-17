from __future__ import annotations

from .model import CommonEvent, TargetQuery


class GoldProvenanceMixin:
    def _current_justification_events(self, proposition_id: str, system_time: int) -> list[CommonEvent]:
        latest: dict[str, CommonEvent] = {}
        for event in self._events_through(system_time):
            if event.event_type != "justification" or event.proposition_id != proposition_id or not event.object_id:
                continue
            latest[event.object_id] = event
        active = []
        for event in latest.values():
            attrs = self._attrs(event)
            if attrs.get("status", "active") == "active" and event.policy_operation not in {"revoke", "invalidate"}:
                active.append(event)
        return active

    def _answer_justifications(self, query: TargetQuery) -> list[str]:
        if query.proposition_id is None:
            return []
        clearance = {"public_user": 0, "trusted_user": 1, "admin": 3}.get(query.requester_id or "public_user", 0)
        label_rank = {"public": 0, "private": 1, "sealed": 2, "blocked": 3}
        accepted: list[str] = []
        for justification in self._current_justification_events(query.proposition_id, query.system_time):
            labels: list[int] = []
            families: set[str] = set()
            sufficient = True
            for member_id in justification.derivation_members:
                member = self.evidence_by_id.get(member_id) or self.event_by_id.get(member_id)
                if member is None or member.system_time > query.system_time:
                    sufficient = False
                    break
                label, _, active = self._policy_projection(member_id, query.system_time, None)
                if not active:
                    sufficient = False
                    break
                labels.append(label_rank.get(label, 3))
                families.add(member.source_family_id or member.event_id)
            minimum = int(self._attrs(justification).get("min_independent_sources", "1"))
            if sufficient and len(families) >= minimum and max(labels, default=0) <= clearance:
                accepted.append(justification.object_id or "")
        return sorted(accepted)
