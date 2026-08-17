from __future__ import annotations

from dataclasses import dataclass

from .model import DatasetSplit, RenderingFamily


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    fixture_id: str
    topology_family: str
    event_id: str
    query_id: str
    split: DatasetSplit
    rendering_family: RenderingFamily
    corruption_field: str


FROZEN_MANIFEST_VERSION = "track-x-v0.1-manifest-1"
CALIBRATION_BINS = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
FIXED_COVERAGE_LEVELS = (0.50, 0.75, 0.90, 1.00)
FIXED_RISK_LEVELS = (0.00, 0.05, 0.10, 0.20)


FROZEN_MANIFEST: tuple[ManifestEntry, ...] = (
    ManifestEntry(
        "F01",
        "branch_visibility",
        "F01.c2",
        "F01.q3",
        DatasetSplit.DEVELOPMENT,
        RenderingFamily.EXPLICIT,
        "about_world_branch_id",
    ),
    ManifestEntry(
        "F02",
        "mind_copy_without_world_fork",
        "F02.a1",
        "F02.q5",
        DatasetSplit.DEVELOPMENT,
        RenderingFamily.CONVERSATIONAL,
        "attitude_transition",
    ),
    ManifestEntry(
        "F03",
        "world_fork_without_mind_copy",
        "F03.c2",
        "F03.q2",
        DatasetSplit.DEVELOPMENT,
        RenderingFamily.ELLIPTICAL,
        "about_world_branch_id",
    ),
    ManifestEntry(
        "F04",
        "unsynchronized_same_principal_replicas",
        "F04.a2",
        "F04.q2",
        DatasetSplit.DEVELOPMENT,
        RenderingFamily.EXPLICIT,
        "attitude_transition",
    ),
    ManifestEntry(
        "F05",
        "identity_fork_copy_attribution",
        "F05.x2",
        "F05.q3",
        DatasetSplit.DEVELOPMENT,
        RenderingFamily.CONVERSATIONAL,
        "transfer_kind",
    ),
    ManifestEntry(
        "F06",
        "receive_accept_reject",
        "F06.xr",
        "F06.q1",
        DatasetSplit.DEVELOPMENT,
        RenderingFamily.ELLIPTICAL,
        "destination_mind_instance_id",
    ),
    ManifestEntry(
        "F07",
        "exposure_policy_lifecycle",
        "F07.seal",
        "F07.q3",
        DatasetSplit.DEVELOPMENT,
        RenderingFamily.EXPLICIT,
        "policy_operation",
    ),
    ManifestEntry(
        "F08",
        "restore_manifest_gap",
        "F08.l",
        "F08.q1",
        DatasetSplit.HELDOUT,
        RenderingFamily.CONVERSATIONAL,
        "snapshot_cutoff",
    ),
    ManifestEntry(
        "F09",
        "cross_world_reference_context",
        "F09.xb",
        "F09.q4",
        DatasetSplit.HELDOUT,
        RenderingFamily.ELLIPTICAL,
        "destination_mind_instance_id",
    ),
    ManifestEntry(
        "F10",
        "protected_only_revocation",
        "F10.r",
        "F10.q4",
        DatasetSplit.HELDOUT,
        RenderingFamily.EXPLICIT,
        "policy_operation",
    ),
    ManifestEntry(
        "F11",
        "independent_public_survives",
        "F11.rs",
        "F11.q4",
        DatasetSplit.HELDOUT,
        RenderingFamily.CONVERSATIONAL,
        "object_id",
    ),
    ManifestEntry(
        "F12",
        "same_origin_dedup",
        "F12.del",
        "F12.q4",
        DatasetSplit.HELDOUT,
        RenderingFamily.ELLIPTICAL,
        "object_id",
    ),
    ManifestEntry(
        "F13",
        "authorized_replication",
        "F13.rep",
        "F13.q2",
        DatasetSplit.HELDOUT,
        RenderingFamily.EXPLICIT,
        "authorization_id",
    ),
    ManifestEntry(
        "F14",
        "temporal_negative_controls",
        "F14.w2",
        "F14.q2",
        DatasetSplit.HELDOUT,
        RenderingFamily.CONVERSATIONAL,
        "attributes.value",
    ),
)


def validate_manifest(entries: tuple[ManifestEntry, ...] = FROZEN_MANIFEST) -> None:
    if not entries:
        raise ValueError("Track X manifest cannot be empty")
    fixture_ids = [entry.fixture_id for entry in entries]
    if len(fixture_ids) != len(set(fixture_ids)):
        raise ValueError("each topology fixture must appear exactly once")
    case_keys = [(entry.event_id, entry.query_id) for entry in entries]
    if len(case_keys) != len(set(case_keys)):
        raise ValueError("manifest event/query pairs must be unique")

    development = {
        entry.topology_family
        for entry in entries
        if entry.split is DatasetSplit.DEVELOPMENT
    }
    heldout = {
        entry.topology_family
        for entry in entries
        if entry.split is DatasetSplit.HELDOUT
    }
    if not development or not heldout:
        raise ValueError("both development and held-out topology sets are required")
    if development & heldout:
        raise ValueError("topology families cannot cross split boundaries")
    if len(development) != 7 or len(heldout) != 7:
        raise ValueError("v0.1 freezes seven topology families per split")
    if {entry.rendering_family for entry in entries} != set(RenderingFamily):
        raise ValueError("all rendering families must occur in the manifest")


validate_manifest()
