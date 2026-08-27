from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .model import Attribution, CommonEvent, TargetQuery


@dataclass(frozen=True)
class _ExposureState:
    time: int
    event_id: str
    active: bool
    attribution: str
    historical: bool = True


class GoldStateMixin:
    def _mind_principals(self, system_time: int) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for event in self._events_through(system_time):
            if event.event_type == "mind_create" and event.object_id and event.actor_principal_id:
                mapping[event.object_id] = event.actor_principal_id
        return mapping

    def _auth_granted(self, authorization_id: Optional[str], system_time: int) -> bool:
        if authorization_id is None:
            return False
        history = [
            event
            for event in self._events_through(system_time)
            if event.event_type == "authorization" and event.object_id == authorization_id
        ]
        if not history:
            return False
        last = history[-1]
        return (last.policy_operation or self._attrs(last).get("status")) == "grant"

    def _valid_replication(self, event: CommonEvent) -> bool:
        source = event.source_mind_instance_id
        destination = event.destination_mind_instance_id
        if source is None or destination is None:
            return False
        principals = self._mind_principals(event.system_time)
        if principals.get(source) is None or principals.get(source) != principals.get(destination):
            return False
        if not self._auth_granted(event.authorization_id, event.system_time):
            return False
        for candidate in self._events_through(event.system_time):
            if (
                candidate.event_type == "lineage"
                and candidate.source_mind_instance_id == source
                and candidate.destination_mind_instance_id == destination
                and candidate.lineage_kind in {"operational_replica", "checkpoint_branch"}
            ):
                return True
        return False

    def _snapshot_inheritance(self, mind_id: str, system_time: int) -> tuple[list[_ExposureState], list[tuple[int, str, CommonEvent]]]:
        inherited_evidence: list[_ExposureState] = []
        inherited_attitudes: list[tuple[int, str, CommonEvent]] = []
        for edge in self._events_through(system_time):
            if edge.event_type != "lineage" or edge.destination_mind_instance_id != mind_id or not edge.snapshot_id:
                continue
            cutoff = edge.snapshot_cutoff if edge.snapshot_cutoff is not None else edge.system_time
            manifest = [
                entry
                for entry in self._events_through(edge.system_time)
                if entry.event_type == "snapshot_member" and entry.snapshot_id == edge.snapshot_id
            ]
            for entry in manifest:
                attrs = self._attrs(entry)
                if attrs.get("copy_eligible", "true").lower() != "true" or not entry.object_id:
                    continue
                source = self.event_by_id.get(entry.object_id)
                if source is None or source.system_time > cutoff:
                    continue
                if entry.object_kind == "evidence":
                    if attrs.get("historically_exposed", "true").lower() != "true":
                        continue
                    inherited_evidence.append(
                        _ExposureState(
                            edge.system_time,
                            edge.event_id,
                            attrs.get("availability_state", "active") == "active",
                            entry.attribution_kind or Attribution.UNKNOWN.value,
                        )
                    )
                elif entry.object_kind == "attitude" and source.event_type == "attitude":
                    inherited_attitudes.append((edge.system_time, edge.event_id, source))
        return inherited_evidence, inherited_attitudes

    def _exposure_trace(self, mind_id: str, evidence_id: str, system_time: int) -> list[_ExposureState]:
        trace: list[_ExposureState] = []
        default_attribution = {
            "observe": Attribution.DIRECT_OBSERVATION.value,
            "receive": Attribution.ATTRIBUTED_REPORT.value,
            "read": Attribution.ATTRIBUTED_REPORT.value,
            "evidence_copy": Attribution.EVIDENCE_COPY.value,
            "state_replication": Attribution.SAME_PRINCIPAL_STATE_REPLICATION.value,
            "restore": Attribution.SAME_PRINCIPAL_SNAPSHOT_INHERITANCE.value,
            "reacquire": Attribution.UNKNOWN.value,
        }
        for event in self._events_through(system_time):
            if event.event_type != "exposure":
                continue
            if event.destination_mind_instance_id != mind_id or event.object_id != evidence_id:
                continue
            operation = event.transfer_kind or ""
            if operation == "forget_active":
                trace.append(_ExposureState(event.system_time, event.event_id, False, Attribution.UNKNOWN.value, False))
                continue
            if operation not in default_attribution:
                continue
            if operation == "state_replication" and not self._valid_replication(event):
                continue
            trace.append(
                _ExposureState(
                    event.system_time,
                    event.event_id,
                    True,
                    event.attribution_kind or default_attribution[operation],
                )
            )

        inherited, _ = self._snapshot_inheritance(mind_id, system_time)
        # Snapshot entries are object-specific; filter by manifest object.
        # Reconstruct them here to preserve gold independence from G/T helpers.
        for edge in self._events_through(system_time):
            if event_is_not_snapshot_lineage(edge, mind_id):
                continue
            cutoff = edge.snapshot_cutoff if edge.snapshot_cutoff is not None else edge.system_time
            for entry in self._events_through(edge.system_time):
                if (
                    entry.event_type != "snapshot_member"
                    or entry.snapshot_id != edge.snapshot_id
                    or entry.object_kind != "evidence"
                    or entry.object_id != evidence_id
                ):
                    continue
                attrs = self._attrs(entry)
                source = self.evidence_by_id.get(evidence_id)
                if (
                    attrs.get("copy_eligible", "true").lower() == "true"
                    and attrs.get("historically_exposed", "true").lower() == "true"
                    and source is not None
                    and source.system_time <= cutoff
                ):
                    trace.append(
                        _ExposureState(
                            edge.system_time,
                            edge.event_id,
                            attrs.get("availability_state", "active") == "active",
                            entry.attribution_kind or Attribution.UNKNOWN.value,
                        )
                    )
        del inherited  # kept conceptually separate; object-specific replay above is authoritative
        return sorted(trace, key=lambda row: (row.time, row.event_id))

    def _answer_ever_exposed(self, query: TargetQuery) -> bool:
        if query.mind_instance_id is None or query.evidence_id is None:
            return False
        return any(row.historical for row in self._exposure_trace(query.mind_instance_id, query.evidence_id, query.system_time))

    def _policy_projection(self, object_id: str, system_time: int, mind_id: Optional[str]) -> tuple[str, bool, bool]:
        source = self.evidence_by_id.get(object_id)
        label = source.policy_label if source and source.policy_label else "public"
        active = source is not None and source.system_time <= system_time
        self_access = True
        for event in self._events_through(system_time):
            if event.event_type != "policy" or event.object_id != object_id:
                continue
            operation = event.policy_operation or ""
            if operation == "self_seal" and event.destination_mind_instance_id in {None, mind_id}:
                self_access = False
            elif operation == "self_unseal" and event.destination_mind_instance_id in {None, mind_id}:
                self_access = True
            elif operation == "declassify" and event.policy_label:
                label = event.policy_label
            elif operation == "grant":
                active = True
                if event.policy_label:
                    label = event.policy_label
            elif operation in {"revoke", "evidence_delete", "derived_data_erase", "quarantine"}:
                if operation == "revoke" and event.destination_mind_instance_id not in {None, mind_id}:
                    continue
                active = False
                label = "blocked"
        return label, self_access, active

    def _answer_available(self, query: TargetQuery) -> bool:
        if query.mind_instance_id is None or query.evidence_id is None:
            return False
        trace = self._exposure_trace(query.mind_instance_id, query.evidence_id, query.system_time)
        if not trace:
            return False
        retained = trace[-1].active
        _, self_access, object_active = self._policy_projection(query.evidence_id, query.system_time, query.mind_instance_id)
        return retained and self_access and object_active

    def _answer_attitude(self, query: TargetQuery) -> str:
        if query.mind_instance_id is None or query.proposition_id is None or query.world_branch_id is None:
            return "unknown"
        candidates: list[tuple[int, str, str]] = []
        for event in self._events_through(query.system_time):
            if (
                event.event_type == "attitude"
                and event.destination_mind_instance_id == query.mind_instance_id
                and event.proposition_id == query.proposition_id
                and event.about_world_branch_id == query.world_branch_id
                and self._active(event, query.valid_time)
            ):
                candidates.append((event.system_time, event.event_id, event.attitude_transition or "unknown"))

        _, inherited_attitudes = self._snapshot_inheritance(query.mind_instance_id, query.system_time)
        for inherited_time, lineage_id, source in inherited_attitudes:
            if (
                source.proposition_id == query.proposition_id
                and source.about_world_branch_id == query.world_branch_id
                and self._active(source, query.valid_time)
            ):
                candidates.append((inherited_time, lineage_id, source.attitude_transition or "unknown"))
        if not candidates:
            return "unknown"
        return max(candidates, key=lambda row: (row[0], row[1]))[2]

    def _answer_attribution(self, query: TargetQuery) -> str:
        if query.mind_instance_id is None or query.proposition_id is None:
            return Attribution.UNKNOWN.value
        rank = {
            Attribution.UNKNOWN.value: 0,
            Attribution.RECONSTRUCTION.value: 1,
            Attribution.EVIDENCE_COPY.value: 2,
            Attribution.ATTRIBUTED_REPORT.value: 3,
            Attribution.SAME_PRINCIPAL_STATE_REPLICATION.value: 4,
            Attribution.SAME_PRINCIPAL_SNAPSHOT_INHERITANCE.value: 5,
            Attribution.DIRECT_OBSERVATION.value: 6,
        }
        values: list[str] = []
        for event in self._events_through(query.system_time):
            if event.event_type == "evidence" and event.proposition_id == query.proposition_id and event.object_id:
                values.extend(
                    row.attribution
                    for row in self._exposure_trace(query.mind_instance_id, event.object_id, query.system_time)
                    if row.historical
                )
        return max(values, key=lambda value: rank.get(value, 0)) if values else Attribution.UNKNOWN.value


def event_is_not_snapshot_lineage(event: CommonEvent, mind_id: str) -> bool:
    """Local gold helper kept outside the class to discourage shared imports."""
    return not (
    event.event_type == "lineage"
    and event.destination_mind_instance_id == mind_id
    and event.snapshot_id is not None
    )
