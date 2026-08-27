from __future__ import annotations

from dataclasses import dataclass

from .model import Attribution, CommonEvent, TargetQuery


_ACQUIRE = {"observe", "receive", "read", "evidence_copy", "state_replication", "restore", "reacquire"}
_ATTR_PRIORITY = {
    Attribution.UNKNOWN.value: 0,
    Attribution.RECONSTRUCTION.value: 1,
    Attribution.EVIDENCE_COPY.value: 2,
    Attribution.ATTRIBUTED_REPORT.value: 3,
    Attribution.SAME_PRINCIPAL_STATE_REPLICATION.value: 4,
    Attribution.SAME_PRINCIPAL_SNAPSHOT_INHERITANCE.value: 5,
    Attribution.DIRECT_OBSERVATION.value: 6,
}

@dataclass(frozen=True)
class _Acquisition:
    system_time: int
    event_id: str
    active: bool
    attribution: str
    historical: bool = True


class GenericStateMixin:
    def _mind_principals(self, system_time: int) -> dict[str, str]:
        result: dict[str, str] = {}
        for event in self.events:
            if event.system_time <= system_time and event.event_type == "mind_create" and event.object_id:
                if event.actor_principal_id is None:
                    raise ValueError("mind_create lacks principal")
                result[event.object_id] = event.actor_principal_id
        return result

    def _authorization_active(self, authorization_id: Optional[str], at_system_time: int) -> bool:
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
        latest = max(events, key=lambda event: (event.system_time, event.event_id))
        return latest.policy_operation == "grant" or self._attrs(latest).get("status") == "grant"

    def _lineage_authorizes_replication(self, exposure: CommonEvent) -> bool:
        if exposure.source_mind_instance_id is None or exposure.destination_mind_instance_id is None:
            return False
        principals = self._mind_principals(exposure.system_time)
        if principals.get(exposure.source_mind_instance_id) != principals.get(exposure.destination_mind_instance_id):
            return False
        if not self._authorization_active(exposure.authorization_id, exposure.system_time):
            return False
        return any(
            event.event_type == "lineage"
            and event.system_time <= exposure.system_time
            and event.source_mind_instance_id == exposure.source_mind_instance_id
            and event.destination_mind_instance_id == exposure.destination_mind_instance_id
            and event.lineage_kind in {"operational_replica", "checkpoint_branch"}
            for event in self.events
        )

    def _direct_acquisitions(self, mind_id: str, evidence_id: str, system_time: int) -> list[_Acquisition]:
        output: list[_Acquisition] = []
        for event in self.events:
            if event.system_time > system_time or event.event_type != "exposure":
                continue
            if (event.object_kind or "evidence") != "evidence":
                continue
            if event.destination_mind_instance_id != mind_id or event.object_id != evidence_id:
                continue
            operation = event.transfer_kind or ""
            if operation == "forget_active":
                output.append(_Acquisition(event.system_time, event.event_id, False, Attribution.UNKNOWN.value, False))
                continue
            if operation not in _ACQUIRE:
                continue
            if operation == "state_replication" and not self._lineage_authorizes_replication(event):
                continue
            attribution = event.attribution_kind
            if attribution is None:
                attribution = {
                    "observe": Attribution.DIRECT_OBSERVATION.value,
                    "receive": Attribution.ATTRIBUTED_REPORT.value,
                    "read": Attribution.ATTRIBUTED_REPORT.value,
                    "evidence_copy": Attribution.EVIDENCE_COPY.value,
                    "state_replication": Attribution.SAME_PRINCIPAL_STATE_REPLICATION.value,
                    "restore": Attribution.SAME_PRINCIPAL_SNAPSHOT_INHERITANCE.value,
                    "reacquire": Attribution.UNKNOWN.value,
                }.get(operation, Attribution.UNKNOWN.value)
            output.append(_Acquisition(event.system_time, event.event_id, True, attribution))
        return output

    def _snapshot_acquisitions(self, mind_id: str, evidence_id: str, system_time: int) -> list[_Acquisition]:
        output: list[_Acquisition] = []
        lineage_events = [
            event
            for event in self.events
            if event.event_type == "lineage"
            and event.destination_mind_instance_id == mind_id
            and event.system_time <= system_time
            and event.snapshot_id
            and event.lineage_kind in {"restore", "checkpoint_branch", "operational_replica", "identity_fork", "fragment_reconstruct"}
        ]
        for lineage in lineage_events:
            cutoff = lineage.snapshot_cutoff if lineage.snapshot_cutoff is not None else lineage.system_time
            members = [
                event
                for event in self.events
                if event.event_type == "snapshot_member"
                and event.snapshot_id == lineage.snapshot_id
                and event.object_kind == "evidence"
                and event.object_id == evidence_id
                and event.system_time <= lineage.system_time
            ]
            for member in members:
                attrs = self._attrs(member)
                if attrs.get("copy_eligible", "true").lower() != "true":
                    continue
                source = self.evidence_by_id.get(evidence_id)
                if source is None or source.system_time > cutoff:
                    continue
                historical = attrs.get("historically_exposed", "true").lower() == "true"
                if not historical:
                    continue
                active = attrs.get("availability_state", "active") == "active"
                attribution = member.attribution_kind or Attribution.UNKNOWN.value
                output.append(_Acquisition(lineage.system_time, lineage.event_id, active, attribution))
        return output

    def _acquisitions(self, mind_id: str, evidence_id: str, system_time: int) -> list[_Acquisition]:
        return sorted(
            self._direct_acquisitions(mind_id, evidence_id, system_time)
            + self._snapshot_acquisitions(mind_id, evidence_id, system_time),
            key=lambda item: (item.system_time, item.event_id),
        )

    def _ever_exposed(self, query: TargetQuery) -> bool:
        if query.mind_instance_id is None or query.evidence_id is None:
            return False
        return any(item.historical for item in self._acquisitions(query.mind_instance_id, query.evidence_id, query.system_time))

    def _object_policy_state(self, object_id: str, system_time: int, *, mind_id: Optional[str] = None) -> tuple[str, bool, bool]:
        initial = "public"
        source = self.evidence_by_id.get(object_id)
        if source and source.policy_label:
            initial = source.policy_label
        label = initial
        self_access = True
        object_active = True
        events = [
            event
            for event in self.events
            if event.event_type == "policy"
            and event.object_id == object_id
            and (event.object_kind or "evidence") == "evidence"
            and event.system_time <= system_time
        ]
        for event in sorted(events, key=lambda item: (item.system_time, item.event_id)):
            operation = event.policy_operation or ""
            targeted = event.destination_mind_instance_id in {None, mind_id}
            if operation == "self_seal" and targeted:
                self_access = False
            elif operation == "self_unseal" and targeted:
                self_access = True
            elif operation == "declassify" and event.policy_label:
                label = event.policy_label
            elif operation in {"revoke", "evidence_delete", "derived_data_erase", "quarantine"}:
                if operation == "revoke" and event.destination_mind_instance_id not in {None, mind_id}:
                    continue
                object_active = False
                label = "blocked"
            elif operation == "grant" and event.policy_label:
                label = event.policy_label
                object_active = True
        return label, self_access, object_active

    def _available(self, query: TargetQuery) -> bool:
        if query.mind_instance_id is None or query.evidence_id is None:
            return False
        acquisitions = self._acquisitions(query.mind_instance_id, query.evidence_id, query.system_time)
        if not acquisitions:
            return False
        latest = max(acquisitions, key=lambda item: (item.system_time, item.event_id))
        _, self_access, object_active = self._object_policy_state(
            query.evidence_id, query.system_time, mind_id=query.mind_instance_id
        )
        return latest.active and self_access and object_active

    def _snapshot_attitudes(self, mind_id: str, proposition_id: str, about_branch: str, system_time: int, valid_time: int) -> list[tuple[int, str, str]]:
        output: list[tuple[int, str, str]] = []
        for lineage in self.events:
            if (
                lineage.event_type != "lineage"
                or lineage.destination_mind_instance_id != mind_id
                or lineage.system_time > system_time
                or not lineage.snapshot_id
            ):
                continue
            cutoff = lineage.snapshot_cutoff if lineage.snapshot_cutoff is not None else lineage.system_time
            for member in self.events:
                if (
                    member.event_type != "snapshot_member"
                    or member.snapshot_id != lineage.snapshot_id
                    or member.object_kind != "attitude"
                    or member.system_time > lineage.system_time
                    or self._attrs(member).get("copy_eligible", "true").lower() != "true"
                ):
                    continue
                source = self.by_id.get(member.object_id or "")
                if (
                    source is None
                    or source.event_type != "attitude"
                    or source.system_time > cutoff
                    or source.proposition_id != proposition_id
                    or source.about_world_branch_id != about_branch
                    or not source.active_at(valid_time)
                ):
                    continue
                output.append((lineage.system_time, lineage.event_id, source.attitude_transition or "unknown"))
        return output

    def _attitude(self, query: TargetQuery) -> str:
        if query.mind_instance_id is None or query.proposition_id is None or query.world_branch_id is None:
            return "unknown"
        candidates: list[tuple[int, str, str]] = []
        for event in self.events:
            if (
                event.system_time <= query.system_time
                and event.event_type == "attitude"
                and event.destination_mind_instance_id == query.mind_instance_id
                and event.proposition_id == query.proposition_id
                and event.about_world_branch_id == query.world_branch_id
                and event.active_at(query.valid_time)
            ):
                candidates.append((event.system_time, event.event_id, event.attitude_transition or "unknown"))
        candidates.extend(
            self._snapshot_attitudes(
                query.mind_instance_id,
                query.proposition_id,
                query.world_branch_id,
                query.system_time,
                query.valid_time,
            )
        )
        return max(candidates, key=lambda item: (item[0], item[1]))[2] if candidates else "unknown"

    def _attribution(self, query: TargetQuery) -> str:
        if query.mind_instance_id is None or query.proposition_id is None:
            return Attribution.UNKNOWN.value
        attributions: list[str] = []
        evidence_ids = [
            event.object_id
            for event in self.events
            if event.event_type == "evidence"
            and event.proposition_id == query.proposition_id
            and event.object_id is not None
            and event.system_time <= query.system_time
        ]
        for evidence_id in evidence_ids:
            for acquisition in self._acquisitions(query.mind_instance_id, evidence_id, query.system_time):
                if acquisition.historical:
                    attributions.append(acquisition.attribution)
        if not attributions:
            return Attribution.UNKNOWN.value
        return max(attributions, key=lambda value: _ATTR_PRIORITY.get(value, 0))
