from __future__ import annotations

from .fixtures_branch import (
    fixture_branch_visibility,
    fixture_mind_copy_without_world_fork,
    fixture_unsynchronized_replicas,
    fixture_world_fork_without_mind_copy,
)
from .fixtures_identity import (
    fixture_cross_world_reference_context,
    fixture_exposure_policy_lifecycle,
    fixture_identity_fork_copy_attribution,
    fixture_receive_accept_reject,
    fixture_restore_manifest_gap,
)
from .fixtures_policy import (
    fixture_authorized_replication,
    fixture_independent_public_survives,
    fixture_protected_only_revocation,
    fixture_same_origin_dedup,
    fixture_temporal_negative_controls,
)
from .model import Fixture


def all_fixtures() -> tuple[Fixture, ...]:
    return (
        fixture_branch_visibility(),
        fixture_mind_copy_without_world_fork(),
        fixture_world_fork_without_mind_copy(),
        fixture_unsynchronized_replicas(),
        fixture_identity_fork_copy_attribution(),
        fixture_receive_accept_reject(),
        fixture_exposure_policy_lifecycle(),
        fixture_restore_manifest_gap(),
        fixture_cross_world_reference_context(),
        fixture_protected_only_revocation(),
        fixture_independent_public_survives(),
        fixture_same_origin_dedup(),
        fixture_authorized_replication(),
        fixture_temporal_negative_controls(),
    )
