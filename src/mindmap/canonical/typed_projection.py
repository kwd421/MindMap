from __future__ import annotations

from typing import Iterable

from .model import (
    Attribution,
    CommonEvent,
    sorted_events,
    validate_temporal_references,
)
from .typed_rows import (
    PrincipalRow,
    MindRow,
    WorldBranchRow,
    MindPlacementRow,
    LineageRow,
    EvidenceRow,
    WorldClaimRow,
    AttitudeRow,
    ExposureRow,
    PolicyRow,
    JustificationRow,
    SnapshotManifestRow,
    AuthorizationRow,
    AcquiredRow
)


class TypedProjectionMixin:
    implementation_name = "T_typed_v0_2_ledger"

    def __init__(self, events: Iterable[CommonEvent]):
        input_events = tuple(events)
        validate_temporal_references(input_events)
        self.common_events = sorted_events(input_events)
        ids = [event.event_id for event in self.common_events]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate CommonEvent.event_id")
        self.event_by_id = {event.event_id: event for event in self.common_events}

        self.principals: dict[str, PrincipalRow] = {}
        self.minds: dict[str, MindRow] = {}
        self.branches: dict[str, WorldBranchRow] = {}
        self.placements: list[MindPlacementRow] = []
        self.lineage: list[LineageRow] = []
        self.evidence: dict[str, EvidenceRow] = {}
        self.world_claims: list[WorldClaimRow] = []
        self.attitudes: list[AttitudeRow] = []
        self.exposures: list[ExposureRow] = []
        self.policies: list[PolicyRow] = []
        self.justifications: list[JustificationRow] = []
        self.snapshot_manifest: list[SnapshotManifestRow] = []
        self.authorizations: list[AuthorizationRow] = []
        self._project()
        self._validate_references()

    @staticmethod
    def _attrs(event: CommonEvent) -> dict[str, str]:
        return dict(event.attributes)

    def _project(self) -> None:
        for event in self.common_events:
            attrs = self._attrs(event)
            if event.event_type == "principal_create":
                if not event.object_id:
                    raise ValueError("principal_create without object_id")
                self.principals[event.object_id] = PrincipalRow(event.object_id, event.system_time)
            elif event.event_type == "mind_create":
                if not event.object_id or not event.actor_principal_id:
                    raise ValueError("mind_create requires mind and principal")
                self.minds[event.object_id] = MindRow(event.object_id, event.actor_principal_id, event.system_time)
            elif event.event_type == "world_create":
                if not event.object_id:
                    raise ValueError("world_create without branch id")
                fork_text = attrs.get("fork_valid_time")
                fork_valid = None if fork_text in {None, "", "None"} else int(fork_text)
                self.branches[event.object_id] = WorldBranchRow(
                    event.object_id,
                    attrs.get("parent") or None,
                    fork_valid,
                    event.system_time,
                )
            elif event.event_type == "placement":
                if not event.object_id or not event.destination_mind_instance_id or not event.about_world_branch_id:
                    raise ValueError("placement lacks required identity")
                self.placements.append(
                    MindPlacementRow(
                        event.object_id,
                        event.destination_mind_instance_id,
                        event.about_world_branch_id,
                        event.valid_from,
                        event.valid_to,
                        event.system_time,
                    )
                )
            elif event.event_type == "lineage":
                if not event.destination_mind_instance_id or not event.lineage_kind:
                    raise ValueError("lineage lacks destination or kind")
                self.lineage.append(
                    LineageRow(
                        event.event_id,
                        event.lineage_kind,
                        event.source_mind_instance_id,
                        event.destination_mind_instance_id,
                        event.snapshot_id,
                        event.snapshot_cutoff,
                        event.authorization_id,
                        event.system_time,
                    )
                )
            elif event.event_type == "evidence":
                if not event.object_id:
                    raise ValueError("evidence lacks object id")
                self.evidence[event.object_id] = EvidenceRow(
                    event.object_id,
                    event.proposition_id,
                    event.actor_principal_id,
                    event.actor_mind_instance_id,
                    event.source_placement_id or event.destination_placement_id,
                    event.about_world_branch_id,
                    event.valid_from,
                    event.valid_to,
                    event.system_time,
                    event.source_family_id or event.object_id,
                    event.policy_label or "public",
                )
            elif event.event_type == "world_claim":
                if not event.proposition_id or not event.about_world_branch_id:
                    raise ValueError("world_claim lacks proposition or branch")
                self.world_claims.append(
                    WorldClaimRow(
                        event.event_id,
                        event.proposition_id,
                        event.about_world_branch_id,
                        attrs.get("value", "unknown"),
                        event.valid_from,
                        event.valid_to,
                        event.system_time,
                        attrs.get("status", "active"),
                    )
                )
            elif event.event_type == "attitude":
                if not event.destination_mind_instance_id or not event.proposition_id or not event.about_world_branch_id:
                    raise ValueError("attitude lacks holder/proposition/branch")
                self.attitudes.append(
                    AttitudeRow(
                        event.event_id,
                        event.destination_mind_instance_id,
                        event.proposition_id,
                        event.about_world_branch_id,
                        event.attitude_transition or "unknown",
                        event.valid_from,
                        event.valid_to,
                        event.system_time,
                    )
                )
            elif event.event_type == "exposure":
                if not event.destination_mind_instance_id or not event.object_id or not event.transfer_kind:
                    raise ValueError("exposure lacks destination/object/operation")
                attribution = event.attribution_kind or {
                    "observe": Attribution.DIRECT_OBSERVATION.value,
                    "receive": Attribution.ATTRIBUTED_REPORT.value,
                    "read": Attribution.ATTRIBUTED_REPORT.value,
                    "evidence_copy": Attribution.EVIDENCE_COPY.value,
                    "state_replication": Attribution.SAME_PRINCIPAL_STATE_REPLICATION.value,
                    "restore": Attribution.SAME_PRINCIPAL_SNAPSHOT_INHERITANCE.value,
                    "reacquire": Attribution.UNKNOWN.value,
                    "forget_active": Attribution.UNKNOWN.value,
                }.get(event.transfer_kind, Attribution.UNKNOWN.value)
                self.exposures.append(
                    ExposureRow(
                        event.event_id,
                        event.destination_mind_instance_id,
                        event.object_id,
                        event.transfer_kind,
                        event.source_mind_instance_id,
                        attribution,
                        event.authorization_id,
                        event.system_time,
                    )
                )
            elif event.event_type == "policy":
                if not event.object_id or not event.policy_operation:
                    raise ValueError("policy lacks object/operation")
                self.policies.append(
                    PolicyRow(
                        event.event_id,
                        event.object_id,
                        event.policy_operation,
                        event.destination_mind_instance_id,
                        event.policy_label,
                        event.system_time,
                    )
                )
            elif event.event_type == "justification":
                if not event.object_id or not event.proposition_id:
                    raise ValueError("justification lacks id/proposition")
                self.justifications.append(
                    JustificationRow(
                        event.object_id,
                        event.proposition_id,
                        event.derivation_members,
                        int(attrs.get("min_independent_sources", "1")),
                        "revoked" if event.policy_operation in {"revoke", "invalidate"} else attrs.get("status", "active"),
                        event.system_time,
                    )
                )
            elif event.event_type == "snapshot_member":
                if not event.snapshot_id or not event.object_kind or not event.object_id:
                    raise ValueError("snapshot_member lacks snapshot/object")
                self.snapshot_manifest.append(
                    SnapshotManifestRow(
                        event.event_id,
                        event.snapshot_id,
                        event.object_kind,
                        event.object_id,
                        attrs.get("copy_eligible", "true").lower() == "true",
                        attrs.get("historically_exposed", "true").lower() == "true",
                        attrs.get("availability_state", "active"),
                        event.attribution_kind or Attribution.UNKNOWN.value,
                        event.system_time,
                    )
                )
            elif event.event_type == "authorization":
                if not event.object_id:
                    raise ValueError("authorization lacks id")
                operation = event.policy_operation or attrs.get("status", "revoke")
                self.authorizations.append(
                    AuthorizationRow(
                        event.object_id,
                        event.source_mind_instance_id,
                        event.destination_mind_instance_id,
                        operation,
                        event.system_time,
                    )
                )

    def _validate_references(self) -> None:
        for mind in self.minds.values():
            if mind.principal_id not in self.principals:
                raise ValueError(f"mind references missing principal: {mind.mind_instance_id}")
        for branch in self.branches.values():
            if branch.parent_world_branch_id and branch.parent_world_branch_id not in self.branches:
                raise ValueError(f"missing parent branch: {branch.parent_world_branch_id}")
        for placement in self.placements:
            if placement.mind_instance_id not in self.minds or placement.world_branch_id not in self.branches:
                raise ValueError(f"invalid placement: {placement.placement_id}")
        for edge in self.lineage:
            if edge.destination_mind_instance_id not in self.minds:
                raise ValueError(f"lineage destination missing: {edge.destination_mind_instance_id}")
            if edge.source_mind_instance_id and edge.source_mind_instance_id not in self.minds:
                raise ValueError(f"lineage source missing: {edge.source_mind_instance_id}")
        for evidence in self.evidence.values():
            if evidence.actor_mind_instance_id and evidence.actor_mind_instance_id in self.minds:
                expected = self.minds[evidence.actor_mind_instance_id].principal_id
                if evidence.actor_principal_id and evidence.actor_principal_id != expected:
                    raise ValueError("evidence actor principal/mind mismatch")
