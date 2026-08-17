from __future__ import annotations

from typing import Optional

from .model import Answer, Attribution, TargetQuery, TargetSpace
from .typed_rows import (
    ATTRIBUTION_ORDER,
    POLICY_ORDER,
    REQUESTER_LEVEL,
    AcquiredRow,
    AttitudeRow,
    ExposureRow,
    JustificationRow,
    WorldBranchRow,
)


class TypedResolutionMixin:
    def answer(self, query: TargetQuery) -> Answer:
        dispatch = {
            TargetSpace.WORLD: self._world,
            TargetSpace.EVER_EXPOSED: self._ever_exposed,
            TargetSpace.AVAILABLE: self._available,
            TargetSpace.ATTITUDE: self._attitude,
            TargetSpace.ATTRIBUTION: self._attribution,
            TargetSpace.DISCLOSE: lambda q: bool(self._justifications(q)),
            TargetSpace.JUSTIFICATION: lambda q: tuple(self._justifications(q)),
        }
        return dispatch[query.target_space](query)

    def _branch_chain(self, branch_id: str, system_time: int) -> list[WorldBranchRow]:
        if branch_id not in self.branches or self.branches[branch_id].fork_system_time > system_time:
            return []
        chain: list[WorldBranchRow] = []
        current = self.branches[branch_id]
        seen: set[str] = set()
        while True:
            if current.world_branch_id in seen:
                raise ValueError("branch cycle")
            seen.add(current.world_branch_id)
            chain.append(current)
            if current.parent_world_branch_id is None:
                break
            parent = self.branches[current.parent_world_branch_id]
            if parent.fork_system_time > system_time:
                raise ValueError("parent branch not visible")
            current = parent
        return list(reversed(chain))

    @staticmethod
    def _interval_active(start: int, end: Optional[int], t: int) -> bool:
        return start <= t and (end is None or t < end)

    def _world(self, query: TargetQuery) -> str:
        if query.proposition_id is None or query.world_branch_id is None:
            return "unknown"
        chain = self._branch_chain(query.world_branch_id, query.system_time)
        if not chain:
            return "unknown"
        effective_time: dict[str, int] = {query.world_branch_id: query.valid_time}
        cutoff = query.valid_time
        for index in range(len(chain) - 1, 0, -1):
            fork = chain[index].fork_valid_time
            if fork is not None:
                cutoff = min(cutoff, fork)
            effective_time[chain[index - 1].world_branch_id] = cutoff

        selected: Optional[WorldClaimRow] = None
        selected_depth = -1
        for depth, branch in enumerate(chain):
            tv = effective_time[branch.world_branch_id]
            rows = [
                row
                for row in self.world_claims
                if row.recorded_system_time <= query.system_time
                and row.proposition_id == query.proposition_id
                and row.about_world_branch_id == branch.world_branch_id
                and row.status == "active"
                and self._interval_active(row.valid_from, row.valid_to, tv)
            ]
            if rows:
                local = max(rows, key=lambda row: (row.valid_from, row.recorded_system_time, row.revision_id))
                if depth >= selected_depth:
                    selected = local
                    selected_depth = depth
        return selected.value if selected else "unknown"

    def _authorization_active(self, auth_id: Optional[str], system_time: int) -> bool:
        if auth_id is None:
            return False
        rows = [row for row in self.authorizations if row.authorization_id == auth_id and row.recorded_system_time <= system_time]
        if not rows:
            return False
        return max(rows, key=lambda row: (row.recorded_system_time, row.operation)).operation == "grant"

    def _replication_eligible(self, row: ExposureRow) -> bool:
        if not row.source_mind_instance_id:
            return False
        source = self.minds.get(row.source_mind_instance_id)
        destination = self.minds.get(row.destination_mind_instance_id)
        if source is None or destination is None or source.principal_id != destination.principal_id:
            return False
        if not self._authorization_active(row.authorization_id, row.recorded_system_time):
            return False
        return any(
            edge.source_mind_instance_id == row.source_mind_instance_id
            and edge.destination_mind_instance_id == row.destination_mind_instance_id
            and edge.created_system_time <= row.recorded_system_time
            and edge.kind in {"operational_replica", "checkpoint_branch"}
            for edge in self.lineage
        )

    def _snapshot_rows(self, mind_id: str, evidence_id: str, system_time: int) -> list[AcquiredRow]:
        acquisitions: list[AcquiredRow] = []
        for edge in self.lineage:
            if edge.destination_mind_instance_id != mind_id or edge.created_system_time > system_time or not edge.snapshot_id:
                continue
            cutoff = edge.cutoff_system_time if edge.cutoff_system_time is not None else edge.created_system_time
            for entry in self.snapshot_manifest:
                if (
                    entry.snapshot_id != edge.snapshot_id
                    or entry.object_kind != "evidence"
                    or entry.object_id != evidence_id
                    or entry.recorded_system_time > edge.created_system_time
                    or not entry.copy_eligible
                    or not entry.historically_exposed
                ):
                    continue
                source = self.evidence.get(evidence_id)
                if source is None or source.recorded_system_time > cutoff:
                    continue
                acquisitions.append(
                    AcquiredRow(
                        edge.created_system_time,
                        edge.lineage_edge_id,
                        entry.availability_state == "active",
                        entry.attribution_kind,
                    )
                )
        return acquisitions

    def _acquisition_rows(self, mind_id: str, evidence_id: str, system_time: int) -> list[AcquiredRow]:
        rows: list[AcquiredRow] = []
        for exposure in self.exposures:
            if exposure.destination_mind_instance_id != mind_id or exposure.object_id != evidence_id:
                continue
            if exposure.recorded_system_time > system_time:
                continue
            if exposure.operation == "forget_active":
                rows.append(AcquiredRow(exposure.recorded_system_time, exposure.exposure_id, False, Attribution.UNKNOWN.value, False))
            elif exposure.operation in {"observe", "receive", "read", "evidence_copy", "restore", "reacquire"}:
                rows.append(AcquiredRow(exposure.recorded_system_time, exposure.exposure_id, True, exposure.attribution_kind))
            elif exposure.operation == "state_replication" and self._replication_eligible(exposure):
                rows.append(AcquiredRow(exposure.recorded_system_time, exposure.exposure_id, True, exposure.attribution_kind))
        rows.extend(self._snapshot_rows(mind_id, evidence_id, system_time))
        return sorted(rows, key=lambda row: (row.recorded_system_time, row.event_id))

    def _ever_exposed(self, query: TargetQuery) -> bool:
        if not query.mind_instance_id or not query.evidence_id:
            return False
        return any(row.historical for row in self._acquisition_rows(query.mind_instance_id, query.evidence_id, query.system_time))

    def _policy_state(self, evidence_id: str, system_time: int, mind_id: Optional[str]) -> tuple[str, bool, bool]:
        evidence = self.evidence.get(evidence_id)
        label = evidence.initial_policy_label if evidence else "public"
        self_access = True
        active = evidence is not None and evidence.recorded_system_time <= system_time
        for row in sorted(
            [p for p in self.policies if p.object_id == evidence_id and p.recorded_system_time <= system_time],
            key=lambda p: (p.recorded_system_time, p.policy_event_id),
        ):
            if row.operation == "self_seal" and row.destination_mind_instance_id in {None, mind_id}:
                self_access = False
            elif row.operation == "self_unseal" and row.destination_mind_instance_id in {None, mind_id}:
                self_access = True
            elif row.operation == "declassify" and row.policy_label:
                label = row.policy_label
            elif row.operation in {"revoke", "evidence_delete", "derived_data_erase", "quarantine"}:
                if row.operation == "revoke" and row.destination_mind_instance_id not in {None, mind_id}:
                    continue
                active = False
                label = "blocked"
            elif row.operation == "grant":
                active = True
                if row.policy_label:
                    label = row.policy_label
        return label, self_access, active

    def _available(self, query: TargetQuery) -> bool:
        if not query.mind_instance_id or not query.evidence_id:
            return False
        rows = self._acquisition_rows(query.mind_instance_id, query.evidence_id, query.system_time)
        if not rows:
            return False
        latest = max(rows, key=lambda row: (row.recorded_system_time, row.event_id))
        _, self_access, active = self._policy_state(query.evidence_id, query.system_time, query.mind_instance_id)
        return latest.active and self_access and active

    def _inherited_attitudes(self, query: TargetQuery) -> list[AttitudeRow]:
        if not query.mind_instance_id or not query.proposition_id or not query.world_branch_id:
            return []
        rows: list[AttitudeRow] = []
        event_attitudes = {row.revision_id: row for row in self.attitudes}
        for edge in self.lineage:
            if edge.destination_mind_instance_id != query.mind_instance_id or edge.created_system_time > query.system_time or not edge.snapshot_id:
                continue
            cutoff = edge.cutoff_system_time if edge.cutoff_system_time is not None else edge.created_system_time
            for entry in self.snapshot_manifest:
                source = event_attitudes.get(entry.object_id)
                if (
                    entry.snapshot_id == edge.snapshot_id
                    and entry.object_kind == "attitude"
                    and entry.copy_eligible
                    and entry.recorded_system_time <= edge.created_system_time
                    and source is not None
                    and source.recorded_system_time <= cutoff
                    and source.proposition_id == query.proposition_id
                    and source.about_world_branch_id == query.world_branch_id
                    and self._interval_active(source.valid_from, source.valid_to, query.valid_time)
                ):
                    rows.append(
                        AttitudeRow(
                            f"inherited:{edge.lineage_edge_id}:{source.revision_id}",
                            query.mind_instance_id,
                            source.proposition_id,
                            source.about_world_branch_id,
                            source.attitude,
                            source.valid_from,
                            source.valid_to,
                            edge.created_system_time,
                        )
                    )
        return rows

    def _attitude(self, query: TargetQuery) -> str:
        if not query.mind_instance_id or not query.proposition_id or not query.world_branch_id:
            return "unknown"
        rows = [
            row
            for row in self.attitudes
            if row.holder_mind_instance_id == query.mind_instance_id
            and row.proposition_id == query.proposition_id
            and row.about_world_branch_id == query.world_branch_id
            and row.recorded_system_time <= query.system_time
            and self._interval_active(row.valid_from, row.valid_to, query.valid_time)
        ]
        rows.extend(self._inherited_attitudes(query))
        return max(rows, key=lambda row: (row.recorded_system_time, row.revision_id)).attitude if rows else "unknown"

    def _attribution(self, query: TargetQuery) -> str:
        if not query.mind_instance_id or not query.proposition_id:
            return Attribution.UNKNOWN.value
        values: list[str] = []
        for evidence in self.evidence.values():
            if evidence.proposition_id != query.proposition_id or evidence.recorded_system_time > query.system_time:
                continue
            for row in self._acquisition_rows(query.mind_instance_id, evidence.evidence_id, query.system_time):
                if row.historical:
                    values.append(row.attribution_kind)
        return max(values, key=lambda value: ATTRIBUTION_ORDER.get(value, 0)) if values else Attribution.UNKNOWN.value

    def _active_justification_rows(self, proposition_id: str, system_time: int) -> list[JustificationRow]:
        latest: dict[str, JustificationRow] = {}
        for row in self.justifications:
            if row.proposition_id != proposition_id or row.recorded_system_time > system_time:
                continue
            previous = latest.get(row.justification_id)
            if previous is None or row.recorded_system_time >= previous.recorded_system_time:
                latest[row.justification_id] = row
        return [row for row in latest.values() if row.status == "active"]

    def _justifications(self, query: TargetQuery) -> list[str]:
        if query.proposition_id is None:
            return []
        clearance = REQUESTER_LEVEL.get(query.requester_id or "public_user", 0)
        accepted: list[str] = []
        for row in self._active_justification_rows(query.proposition_id, query.system_time):
            labels: list[int] = []
            families: set[str] = set()
            usable = True
            for member_id in row.members:
                evidence = self.evidence.get(member_id)
                if evidence is None or evidence.recorded_system_time > query.system_time:
                    usable = False
                    break
                label, _, active = self._policy_state(member_id, query.system_time, None)
                if not active:
                    usable = False
                    break
                labels.append(POLICY_ORDER.get(label, POLICY_ORDER["blocked"]))
                families.add(evidence.origin_family_id)
            if not usable or len(families) < row.min_independent_sources:
                continue
            if max(labels, default=0) <= clearance:
                accepted.append(row.justification_id)
        return sorted(accepted)
