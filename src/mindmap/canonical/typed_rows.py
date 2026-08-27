from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .model import Attribution


POLICY_ORDER = {"public": 0, "private": 1, "sealed": 2, "blocked": 3}
REQUESTER_LEVEL = {"public_user": 0, "trusted_user": 1, "admin": 3}
ATTRIBUTION_ORDER = {
    Attribution.UNKNOWN.value: 0,
    Attribution.RECONSTRUCTION.value: 1,
    Attribution.EVIDENCE_COPY.value: 2,
    Attribution.ATTRIBUTED_REPORT.value: 3,
    Attribution.SAME_PRINCIPAL_STATE_REPLICATION.value: 4,
    Attribution.SAME_PRINCIPAL_SNAPSHOT_INHERITANCE.value: 5,
    Attribution.DIRECT_OBSERVATION.value: 6,
}


@dataclass(frozen=True)
class PrincipalRow:
    principal_id: str
    created_system_time: int

@dataclass(frozen=True)
class MindRow:
    mind_instance_id: str
    principal_id: str
    created_system_time: int

@dataclass(frozen=True)
class WorldBranchRow:
    world_branch_id: str
    parent_world_branch_id: Optional[str]
    fork_valid_time: Optional[int]
    fork_system_time: int

@dataclass(frozen=True)
class MindPlacementRow:
    placement_id: str
    mind_instance_id: str
    world_branch_id: str
    valid_from: int
    valid_to: Optional[int]
    recorded_system_time: int

@dataclass(frozen=True)
class LineageRow:
    lineage_edge_id: str
    kind: str
    source_mind_instance_id: Optional[str]
    destination_mind_instance_id: str
    snapshot_id: Optional[str]
    cutoff_system_time: Optional[int]
    authorization_id: Optional[str]
    created_system_time: int

@dataclass(frozen=True)
class EvidenceRow:
    evidence_id: str
    proposition_id: Optional[str]
    actor_principal_id: Optional[str]
    actor_mind_instance_id: Optional[str]
    assertion_context_placement_id: Optional[str]
    about_world_branch_id: Optional[str]
    valid_from: int
    valid_to: Optional[int]
    recorded_system_time: int
    origin_family_id: str
    initial_policy_label: str

@dataclass(frozen=True)
class WorldClaimRow:
    revision_id: str
    proposition_id: str
    about_world_branch_id: str
    value: str
    valid_from: int
    valid_to: Optional[int]
    recorded_system_time: int
    status: str

@dataclass(frozen=True)
class AttitudeRow:
    revision_id: str
    holder_mind_instance_id: str
    proposition_id: str
    about_world_branch_id: str
    attitude: str
    valid_from: int
    valid_to: Optional[int]
    recorded_system_time: int

@dataclass(frozen=True)
class ExposureRow:
    exposure_id: str
    destination_mind_instance_id: str
    object_kind: str
    object_id: str
    operation: str
    source_mind_instance_id: Optional[str]
    attribution_kind: str
    authorization_id: Optional[str]
    recorded_system_time: int

@dataclass(frozen=True)
class PolicyRow:
    policy_event_id: str
    object_kind: str
    object_id: str
    operation: str
    destination_mind_instance_id: Optional[str]
    policy_label: Optional[str]
    recorded_system_time: int

@dataclass(frozen=True)
class JustificationRow:
    justification_id: str
    proposition_id: str
    members: tuple[str, ...]
    min_independent_sources: int
    status: str
    recorded_system_time: int

@dataclass(frozen=True)
class SnapshotManifestRow:
    manifest_entry_id: str
    snapshot_id: str
    object_kind: str
    object_id: str
    copy_eligible: bool
    historically_exposed: bool
    availability_state: str
    attribution_kind: str
    recorded_system_time: int

@dataclass(frozen=True)
class AuthorizationRow:
    authorization_id: str
    source_mind_instance_id: Optional[str]
    destination_mind_instance_id: Optional[str]
    operation: str
    recorded_system_time: int

@dataclass(frozen=True)
class AcquiredRow:
    recorded_system_time: int
    event_id: str
    active: bool
    attribution_kind: str
    historical: bool = True
