from __future__ import annotations

from typing import Optional

from .model import Attribution, TargetQuery
from .typed_rows import ATTRIBUTION_ORDER, AcquiredRow


_ACQUIRE = {
    "observe",
    "receive",
    "read",
    "evidence_copy",
    "state_replication",
    "restore",
    "reacquire",
}


class TypedExposureResolutionMixin:
    def _authorization_active(
        self, authorization_id: Optional[str], system_time: int
    ) -> bool:
        if not authorization_id:
            return False
        candidates = [
            authorization
            for authorization in self.authorizations
            if authorization.authorization_id == authorization_id
            and authorization.recorded_system_time <= system_time
        ]
        if not candidates:
            return False
        latest = max(
            candidates,
            key=lambda value: (value.recorded_system_time, value.authorization_id),
        )
        return latest.operation == "grant"

    def _lineage_authorizes_replication(self, exposure) -> bool:
        source_id = exposure.source_mind_instance_id
        destination_id = exposure.destination_mind_instance_id
        if source_id is None:
            return False
        source = self.minds.get(source_id)
        destination = self.minds.get(destination_id)
        if (
            source is None
            or destination is None
            or source.principal_id != destination.principal_id
        ):
            return False
        if not self._authorization_active(
            exposure.authorization_id, exposure.recorded_system_time
        ):
            return False
        return any(
            edge.source_mind_instance_id == source_id
            and edge.destination_mind_instance_id == destination_id
            and edge.kind in {"operational_replica", "checkpoint_branch"}
            and edge.created_system_time <= exposure.recorded_system_time
            for edge in self.lineage
        )

    def _direct_acquisitions(
        self, mind_id: str, evidence_id: str, system_time: int
    ) -> list[AcquiredRow]:
        output: list[AcquiredRow] = []
        for exposure in self.exposures:
            if exposure.recorded_system_time > system_time:
                continue
            if (
                exposure.destination_mind_instance_id != mind_id
                or exposure.object_id != evidence_id
            ):
                continue
            if exposure.operation == "forget_active":
                output.append(
                    AcquiredRow(
                        exposure.recorded_system_time,
                        exposure.exposure_id,
                        False,
                        Attribution.UNKNOWN.value,
                        False,
                    )
                )
                continue
            if exposure.operation not in _ACQUIRE:
                continue
            if (
                exposure.operation == "state_replication"
                and not self._lineage_authorizes_replication(exposure)
            ):
                continue
            output.append(
                AcquiredRow(
                    exposure.recorded_system_time,
                    exposure.exposure_id,
                    True,
                    exposure.attribution_kind,
                    True,
                )
            )
        return output

    def _snapshot_acquisitions(
        self, mind_id: str, evidence_id: str, system_time: int
    ) -> list[AcquiredRow]:
        output: list[AcquiredRow] = []
        eligible_kinds = {
            "restore",
            "checkpoint_branch",
            "operational_replica",
            "identity_fork",
            "fragment_reconstruct",
        }
        for edge in self.lineage:
            if (
                edge.destination_mind_instance_id != mind_id
                or edge.created_system_time > system_time
                or edge.kind not in eligible_kinds
                or edge.snapshot_id is None
            ):
                continue
            cutoff = (
                edge.cutoff_system_time
                if edge.cutoff_system_time is not None
                else edge.created_system_time
            )
            for member in self.snapshot_manifest:
                if (
                    member.snapshot_id != edge.snapshot_id
                    or member.object_kind != "evidence"
                    or member.object_id != evidence_id
                    or member.recorded_system_time > edge.created_system_time
                    or not member.copy_eligible
                    or not member.historically_exposed
                ):
                    continue
                source = self.evidence.get(evidence_id)
                if source is None or source.recorded_system_time > cutoff:
                    continue
                output.append(
                    AcquiredRow(
                        edge.created_system_time,
                        edge.lineage_edge_id,
                        member.availability_state == "active",
                        member.attribution_kind,
                        True,
                    )
                )
        return output

    def _acquisitions(
        self, mind_id: str, evidence_id: str, system_time: int
    ) -> list[AcquiredRow]:
        return sorted(
            self._direct_acquisitions(mind_id, evidence_id, system_time)
            + self._snapshot_acquisitions(mind_id, evidence_id, system_time),
            key=lambda value: (value.recorded_system_time, value.event_id),
        )

    def _ever_exposed(self, query: TargetQuery) -> bool:
        if query.mind_instance_id is None or query.evidence_id is None:
            return False
        return any(
            acquisition.historical
            for acquisition in self._acquisitions(
                query.mind_instance_id, query.evidence_id, query.system_time
            )
        )

    def _object_policy_state(
        self,
        object_id: str,
        system_time: int,
        *,
        mind_id: Optional[str] = None,
    ) -> tuple[str, bool, bool]:
        source = self.evidence.get(object_id)
        label = source.initial_policy_label if source else "public"
        self_access = True
        object_active = True
        policies = sorted(
            (
                policy
                for policy in self.policies
                if policy.object_id == object_id
                and policy.recorded_system_time <= system_time
            ),
            key=lambda value: (value.recorded_system_time, value.policy_event_id),
        )
        for policy in policies:
            targeted = policy.destination_mind_instance_id in {None, mind_id}
            if policy.operation == "self_seal" and targeted:
                self_access = False
            elif policy.operation == "self_unseal" and targeted:
                self_access = True
            elif policy.operation == "declassify" and policy.policy_label:
                label = policy.policy_label
            elif policy.operation in {
                "revoke",
                "evidence_delete",
                "derived_data_erase",
                "quarantine",
            }:
                if policy.operation == "revoke" and not targeted:
                    continue
                object_active = False
                label = "blocked"
            elif policy.operation == "grant" and policy.policy_label:
                label = policy.policy_label
                object_active = True
        return label, self_access, object_active

    def _available(self, query: TargetQuery) -> bool:
        if query.mind_instance_id is None or query.evidence_id is None:
            return False
        acquisitions = self._acquisitions(
            query.mind_instance_id, query.evidence_id, query.system_time
        )
        if not acquisitions:
            return False
        latest = max(
            acquisitions, key=lambda value: (value.recorded_system_time, value.event_id)
        )
        _, self_access, object_active = self._object_policy_state(
            query.evidence_id,
            query.system_time,
            mind_id=query.mind_instance_id,
        )
        return latest.active and self_access and object_active

    def _attribution(self, query: TargetQuery) -> str:
        if query.mind_instance_id is None or query.proposition_id is None:
            return Attribution.UNKNOWN.value
        values: list[str] = []
        for evidence in self.evidence.values():
            if (
                evidence.proposition_id != query.proposition_id
                or evidence.recorded_system_time > query.system_time
            ):
                continue
            if (
                query.world_branch_id is not None
                and evidence.about_world_branch_id != query.world_branch_id
            ):
                continue
            for acquisition in self._acquisitions(
                query.mind_instance_id, evidence.evidence_id, query.system_time
            ):
                if acquisition.historical:
                    values.append(acquisition.attribution_kind)
        if not values:
            return Attribution.UNKNOWN.value
        return max(values, key=lambda value: ATTRIBUTION_ORDER.get(value, 0))
