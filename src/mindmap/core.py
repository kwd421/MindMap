from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


POLICY_RANK = {"public": 0, "private": 1, "sealed": 2}
REQUESTER_CLEARANCE = {"public_user": 0, "trusted_user": 1, "admin": 2}
GRANT_OPS = {"observe", "receive", "read", "copy", "restore", "unseal"}
REVOKE_OPS = {"seal", "forget", "revoke"}


@dataclass(frozen=True)
class EvidenceEvent:
    event_id: str
    raw_payload: str
    source_span: str
    speaker_instance_id: str
    occurred_at: int
    valid_from: int
    valid_to: Optional[int]
    recorded_at: int
    world_branch_id: str
    origin_family_id: str
    integrity_hash: str
    extractor_version: str = "gold-v0.2"
    policy_label: str = "public"


@dataclass(frozen=True)
class ClaimRevision:
    claim_id: str
    revision_id: str
    subject: str
    predicate: str
    object: str
    attitude_or_modality: str
    holder_mind_instance_id: Optional[str]
    valid_from: int
    valid_to: Optional[int]
    recorded_at: int
    world_branch_id: str
    about_world_branch_id: Optional[str] = None
    asserted_in_world_branch_id: Optional[str] = None
    source_event_ids: tuple[str, ...] = ()
    derives_from_claim_ids: tuple[str, ...] = ()
    supersedes_revision_id: Optional[str] = None
    joint_hypothesis_id: Optional[str] = None
    calibrated_mass: float = 1.0
    policy_label: str = "public"


@dataclass(frozen=True)
class ExposureTransition:
    exposure_id: str
    mind_instance_id: str
    object_kind: str
    object_id: str
    operation: str
    source_mind_instance_id: Optional[str]
    occurred_at: int
    recorded_at: int
    world_branch_id: str
    source_world_branch_id: Optional[str] = None
    destination_world_branch_id: Optional[str] = None
    parent_exposure_id: Optional[str] = None
    policy_label: str = "public"


@dataclass(frozen=True)
class MindInstance:
    mind_instance_id: str
    character_identity_id: str
    parent_mind_instance_id: Optional[str]
    fork_recorded_at: Optional[int]
    inherited_through_tx: Optional[int]
    originating_snapshot_id: Optional[str]
    world_branch_id: str


@dataclass(frozen=True)
class WorldBranch:
    world_branch_id: str
    parent_world_branch_id: Optional[str]
    fork_valid_time: Optional[int]
    fork_recorded_at: Optional[int]


@dataclass(frozen=True)
class Query:
    query_id: str
    scenario_id: str
    kind: str
    world_branch_id: str
    valid_time: int
    transaction_time: int
    expected: str
    target_mind_instance_id: Optional[str] = None
    requester_id: Optional[str] = None
    subject: Optional[str] = None
    predicate: Optional[str] = None
    evidence_id: Optional[str] = None
    claim_id: Optional[str] = None
    about_world_branch_id: Optional[str] = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class Scenario:
    scenario_id: str
    template: str
    seed: int
    evidence: list[EvidenceEvent]
    claims: list[ClaimRevision]
    exposures: list[ExposureTransition]
    minds: list[MindInstance]
    branches: list[WorldBranch]
    queries: list[Query]
    metadata: dict[str, str] = field(default_factory=dict)


class ResolutionError(RuntimeError):
    pass


def _active_interval(valid_from: int, valid_to: Optional[int], t: int) -> bool:
    return valid_from <= t and (valid_to is None or t < valid_to)


class MemoryIndex:
    """Read-only helper over one Scenario.

    World-branch ancestry and cognitive-instance ancestry are deliberately
    separate DAGs. A cognitive copy need not fork the external world and a
    world fork need not create a new mind instance.
    """

    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self.evidence = {x.event_id: x for x in scenario.evidence}
        self.claims_by_revision = {x.revision_id: x for x in scenario.claims}
        self.claims_by_id: dict[str, list[ClaimRevision]] = {}
        for claim in scenario.claims:
            self.claims_by_id.setdefault(claim.claim_id, []).append(claim)
        self.minds = {x.mind_instance_id: x for x in scenario.minds}
        self.branches = {x.world_branch_id: x for x in scenario.branches}

    def branch_cutoff(self, query_branch: str, ancestor_branch: str, query_tx: int) -> Optional[int]:
        """Maximum transaction time inherited from an ancestor world branch."""
        if query_branch == ancestor_branch:
            return query_tx
        current = self.branches.get(query_branch)
        cutoff = query_tx
        seen: set[str] = set()
        while current and current.parent_world_branch_id is not None:
            if current.world_branch_id in seen:
                raise ResolutionError("cycle in world branch ancestry")
            seen.add(current.world_branch_id)
            if current.fork_recorded_at is None:
                return None
            cutoff = min(cutoff, current.fork_recorded_at)
            parent_id = current.parent_world_branch_id
            if parent_id == ancestor_branch:
                return cutoff
            current = self.branches.get(parent_id)
        return None

    def mind_cutoff(self, query_mind: str, ancestor_mind: str, query_tx: int) -> Optional[int]:
        """Maximum transaction time inherited from an ancestor mind instance."""
        if query_mind == ancestor_mind:
            return query_tx
        current = self.minds.get(query_mind)
        cutoff = query_tx
        seen: set[str] = set()
        while current and current.parent_mind_instance_id is not None:
            if current.mind_instance_id in seen:
                raise ResolutionError("cycle in mind lineage")
            seen.add(current.mind_instance_id)
            if current.inherited_through_tx is None:
                return None
            cutoff = min(cutoff, current.inherited_through_tx)
            parent_id = current.parent_mind_instance_id
            if parent_id == ancestor_mind:
                return cutoff
            current = self.minds.get(parent_id)
        return None

    def branch_record_eligible(self, record_branch: str, query_branch: str, recorded_at: int, query_tx: int) -> bool:
        cutoff = self.branch_cutoff(query_branch, record_branch, query_tx)
        return cutoff is not None and recorded_at <= cutoff

    def mind_record_eligible(self, owner_mind: str, query_mind: str, recorded_at: int, query_tx: int) -> bool:
        cutoff = self.mind_cutoff(query_mind, owner_mind, query_tx)
        return cutoff is not None and recorded_at <= cutoff

    def claim_ancestors(self, claim: ClaimRevision) -> tuple[set[str], set[str]]:
        """Return ultimate evidence IDs and visited claim revision IDs."""
        evidence_ids: set[str] = set(claim.source_event_ids)
        visited: set[str] = set()
        stack = list(claim.derives_from_claim_ids)
        while stack:
            ref = stack.pop()
            if ref in visited:
                continue
            visited.add(ref)
            parent = self.claims_by_revision.get(ref)
            if parent is None:
                versions = self.claims_by_id.get(ref, [])
                parent = max(versions, key=lambda x: x.recorded_at) if versions else None
            if parent is None:
                continue
            evidence_ids.update(parent.source_event_ids)
            stack.extend(parent.derives_from_claim_ids)
        return evidence_ids, visited

    def strictest_policy(self, claim: ClaimRevision) -> str:
        labels = [claim.policy_label]
        evidence_ids, visited_claims = self.claim_ancestors(claim)
        for event_id in evidence_ids:
            event = self.evidence.get(event_id)
            if event is not None:
                labels.append(event.policy_label)
        for revision_id in visited_claims:
            parent = self.claims_by_revision.get(revision_id)
            if parent is not None:
                labels.append(parent.policy_label)
        return max(labels, key=lambda x: POLICY_RANK[x])

    def origin_families(self, claim: ClaimRevision) -> set[str]:
        evidence_ids, _ = self.claim_ancestors(claim)
        return {
            self.evidence[eid].origin_family_id
            for eid in evidence_ids
            if eid in self.evidence
        }

    @staticmethod
    def claim_about_branch(claim: ClaimRevision) -> str:
        return claim.about_world_branch_id or claim.world_branch_id

    @staticmethod
    def claim_context_branch(claim: ClaimRevision) -> str:
        return claim.asserted_in_world_branch_id or claim.world_branch_id

    @staticmethod
    def exposure_context_branch(exposure: ExposureTransition) -> str:
        return exposure.destination_world_branch_id or exposure.world_branch_id


class BaseResolver:
    name = "base"

    def answer(self, scenario: Scenario, query: Query) -> str:
        raise NotImplementedError

    @staticmethod
    def _format_bool(value: bool) -> str:
        return "yes" if value else "no"


class GlobalCharacterResolver(BaseResolver):
    """Weak baseline: character-level memory, no branch or mind lineage.

    It retains bitemporal fields but collapses all world branches and all copied
    minds that share a character identity. Disclosure checks only the final row.
    """

    name = "B3_global_character"

    def answer(self, scenario: Scenario, query: Query) -> str:
        idx = MemoryIndex(scenario)
        if query.kind == "world":
            claim = self._latest_world_claim(idx, query, branch_scoped=False)
            return claim.object if claim else "unknown"
        if query.kind == "access":
            return self._format_bool(self._character_has_access(idx, query, branch_scoped=False))
        if query.kind == "ever_exposed":
            return self._format_bool(self._character_ever_exposed(idx, query, branch_scoped=False))
        if query.kind == "attitude":
            claim = self._latest_attitude(idx, query, branch_scoped=False)
            return self._attitude_answer(claim)
        if query.kind == "disclose":
            claim = self._claim_for_query(idx, query)
            if claim is None:
                return "unknown"
            clearance = REQUESTER_CLEARANCE.get(query.requester_id or "public_user", 0)
            return self._format_bool(POLICY_RANK[claim.policy_label] <= clearance)
        if query.kind == "source_count":
            claim = self._claim_for_query(idx, query)
            if claim is None:
                return "0"
            return str(len(claim.source_event_ids) + len(claim.derives_from_claim_ids))
        if query.kind == "lineage":
            return self._format_bool(self._character_has_access(idx, query, branch_scoped=False))
        raise ResolutionError(f"unsupported query kind: {query.kind}")

    def _claim_for_query(self, idx: MemoryIndex, query: Query) -> Optional[ClaimRevision]:
        if query.claim_id is None:
            return None
        versions = idx.claims_by_id.get(query.claim_id, [])
        eligible = [c for c in versions if c.recorded_at <= query.transaction_time]
        return max(eligible, key=lambda x: x.recorded_at) if eligible else None

    def _latest_world_claim(self, idx: MemoryIndex, query: Query, branch_scoped: bool) -> Optional[ClaimRevision]:
        candidates = []
        for claim in idx.scenario.claims:
            if claim.holder_mind_instance_id is not None:
                continue
            if claim.subject != query.subject or claim.predicate != query.predicate:
                continue
            if claim.recorded_at > query.transaction_time:
                continue
            if not _active_interval(claim.valid_from, claim.valid_to, query.valid_time):
                continue
            if branch_scoped:
                target_about = query.about_world_branch_id or query.world_branch_id
                if idx.claim_about_branch(claim) != target_about:
                    continue
                if not idx.branch_record_eligible(
                    idx.claim_context_branch(claim), query.world_branch_id, claim.recorded_at, query.transaction_time
                ):
                    continue
            candidates.append(claim)
        return max(candidates, key=lambda x: (x.recorded_at, x.revision_id)) if candidates else None

    def _character_has_access(self, idx: MemoryIndex, query: Query, branch_scoped: bool) -> bool:
        if query.target_mind_instance_id is None or query.evidence_id is None:
            return False
        target = idx.minds[query.target_mind_instance_id]
        character = target.character_identity_id
        transitions = []
        for exposure in idx.scenario.exposures:
            mind = idx.minds.get(exposure.mind_instance_id)
            if mind is None or mind.character_identity_id != character:
                continue
            if exposure.object_id != query.evidence_id or exposure.recorded_at > query.transaction_time:
                continue
            if branch_scoped and not idx.branch_record_eligible(
                idx.exposure_context_branch(exposure), query.world_branch_id, exposure.recorded_at, query.transaction_time
            ):
                continue
            transitions.append(exposure)
        if not transitions:
            return False
        latest = max(transitions, key=lambda x: (x.recorded_at, x.exposure_id))
        return latest.operation in GRANT_OPS

    def _character_ever_exposed(self, idx: MemoryIndex, query: Query, branch_scoped: bool) -> bool:
        if query.target_mind_instance_id is None or query.evidence_id is None:
            return False
        target = idx.minds[query.target_mind_instance_id]
        character = target.character_identity_id
        for exposure in idx.scenario.exposures:
            mind = idx.minds.get(exposure.mind_instance_id)
            if mind is None or mind.character_identity_id != character:
                continue
            if exposure.object_id != query.evidence_id or exposure.operation not in GRANT_OPS:
                continue
            if exposure.recorded_at > query.transaction_time:
                continue
            if branch_scoped and not idx.branch_record_eligible(
                idx.exposure_context_branch(exposure), query.world_branch_id, exposure.recorded_at, query.transaction_time
            ):
                continue
            return True
        return False

    def _latest_attitude(self, idx: MemoryIndex, query: Query, branch_scoped: bool) -> Optional[ClaimRevision]:
        if query.target_mind_instance_id is None:
            return None
        target = idx.minds[query.target_mind_instance_id]
        character = target.character_identity_id
        candidates = []
        for claim in idx.scenario.claims:
            holder = claim.holder_mind_instance_id
            if holder is None or holder not in idx.minds:
                continue
            if idx.minds[holder].character_identity_id != character:
                continue
            if claim.subject != query.subject or claim.predicate != query.predicate:
                continue
            if claim.recorded_at > query.transaction_time:
                continue
            if not _active_interval(claim.valid_from, claim.valid_to, query.valid_time):
                continue
            if branch_scoped:
                target_about = query.about_world_branch_id or query.world_branch_id
                if idx.claim_about_branch(claim) != target_about:
                    continue
                if not idx.branch_record_eligible(
                    idx.claim_context_branch(claim), query.world_branch_id, claim.recorded_at, query.transaction_time
                ):
                    continue
            candidates.append(claim)
        return max(candidates, key=lambda x: (x.recorded_at, x.revision_id)) if candidates else None

    @staticmethod
    def _attitude_answer(claim: Optional[ClaimRevision]) -> str:
        if claim is None:
            return "unknown"
        return f"{claim.attitude_or_modality}:{claim.object}"


class BranchScopedCharacterResolver(GlobalCharacterResolver):
    """Strong scoped baseline: world branch aware, but copied minds collapse."""

    name = "B5_branch_scoped_character"

    def answer(self, scenario: Scenario, query: Query) -> str:
        idx = MemoryIndex(scenario)
        if query.kind == "world":
            claim = self._latest_world_claim(idx, query, branch_scoped=True)
            return claim.object if claim else "unknown"
        if query.kind == "access":
            return self._format_bool(self._character_has_access(idx, query, branch_scoped=True))
        if query.kind == "ever_exposed":
            return self._format_bool(self._character_ever_exposed(idx, query, branch_scoped=True))
        if query.kind == "attitude":
            claim = self._latest_attitude(idx, query, branch_scoped=True)
            return self._attitude_answer(claim)
        if query.kind == "disclose":
            claim = self._claim_for_query(idx, query)
            if claim is None:
                return "unknown"
            if not idx.branch_record_eligible(
                idx.claim_context_branch(claim), query.world_branch_id, claim.recorded_at, query.transaction_time
            ):
                return "unknown"
            clearance = REQUESTER_CLEARANCE.get(query.requester_id or "public_user", 0)
            return self._format_bool(POLICY_RANK[claim.policy_label] <= clearance)
        if query.kind == "source_count":
            claim = self._claim_for_query(idx, query)
            if claim is None:
                return "0"
            return str(len(claim.source_event_ids) + len(claim.derives_from_claim_ids))
        if query.kind == "lineage":
            return self._format_bool(self._character_has_access(idx, query, branch_scoped=True))
        raise ResolutionError(f"unsupported query kind: {query.kind}")


class NCMResolver(BaseResolver):
    """Reference resolver with world branches, cognitive lineage, exposure, and policy ancestry."""

    name = "B6_ncm_psi"

    def answer(self, scenario: Scenario, query: Query) -> str:
        idx = MemoryIndex(scenario)
        if query.kind == "world":
            claim = self._latest_world_claim(idx, query)
            return claim.object if claim else "unknown"
        if query.kind in {"access", "lineage"}:
            return self._format_bool(self._mind_has_access(idx, query))
        if query.kind == "ever_exposed":
            return self._format_bool(self._mind_ever_exposed(idx, query))
        if query.kind == "attitude":
            claim = self._latest_attitude(idx, query)
            return GlobalCharacterResolver._attitude_answer(claim)
        if query.kind == "disclose":
            claim = self._claim_for_query(idx, query)
            if claim is None:
                return "unknown"
            if not idx.branch_record_eligible(
                idx.claim_context_branch(claim), query.world_branch_id, claim.recorded_at, query.transaction_time
            ):
                return "unknown"
            clearance = REQUESTER_CLEARANCE.get(query.requester_id or "public_user", 0)
            return self._format_bool(POLICY_RANK[idx.strictest_policy(claim)] <= clearance)
        if query.kind == "source_count":
            claim = self._claim_for_query(idx, query)
            return str(len(idx.origin_families(claim))) if claim else "0"
        raise ResolutionError(f"unsupported query kind: {query.kind}")

    def _claim_for_query(self, idx: MemoryIndex, query: Query) -> Optional[ClaimRevision]:
        if query.claim_id is None:
            return None
        versions = idx.claims_by_id.get(query.claim_id, [])
        candidates = [
            c
            for c in versions
            if idx.branch_record_eligible(
                idx.claim_context_branch(c), query.world_branch_id, c.recorded_at, query.transaction_time
            )
        ]
        return max(candidates, key=lambda x: (x.recorded_at, x.revision_id)) if candidates else None

    def _latest_world_claim(self, idx: MemoryIndex, query: Query) -> Optional[ClaimRevision]:
        candidates = []
        for claim in idx.scenario.claims:
            if claim.holder_mind_instance_id is not None:
                continue
            if claim.subject != query.subject or claim.predicate != query.predicate:
                continue
            target_about = query.about_world_branch_id or query.world_branch_id
            if idx.claim_about_branch(claim) != target_about:
                continue
            if not idx.branch_record_eligible(
                idx.claim_context_branch(claim), query.world_branch_id, claim.recorded_at, query.transaction_time
            ):
                continue
            if not _active_interval(claim.valid_from, claim.valid_to, query.valid_time):
                continue
            candidates.append(claim)
        return max(candidates, key=lambda x: (x.recorded_at, x.revision_id)) if candidates else None

    def _mind_has_access(self, idx: MemoryIndex, query: Query) -> bool:
        if query.target_mind_instance_id is None or query.evidence_id is None:
            return False
        transitions = []
        for exposure in idx.scenario.exposures:
            if exposure.object_id != query.evidence_id:
                continue
            if not idx.branch_record_eligible(
                idx.exposure_context_branch(exposure), query.world_branch_id, exposure.recorded_at, query.transaction_time
            ):
                continue
            if not idx.mind_record_eligible(
                exposure.mind_instance_id,
                query.target_mind_instance_id,
                exposure.recorded_at,
                query.transaction_time,
            ):
                continue
            if exposure.mind_instance_id != query.target_mind_instance_id and exposure.policy_label == "sealed":
                continue
            transitions.append(exposure)
        if not transitions:
            return False
        latest = max(transitions, key=lambda x: (x.recorded_at, x.exposure_id))
        return latest.operation in GRANT_OPS

    def _mind_ever_exposed(self, idx: MemoryIndex, query: Query) -> bool:
        if query.target_mind_instance_id is None or query.evidence_id is None:
            return False
        for exposure in idx.scenario.exposures:
            if exposure.object_id != query.evidence_id or exposure.operation not in GRANT_OPS:
                continue
            if not idx.branch_record_eligible(
                idx.exposure_context_branch(exposure), query.world_branch_id, exposure.recorded_at, query.transaction_time
            ):
                continue
            if not idx.mind_record_eligible(
                exposure.mind_instance_id,
                query.target_mind_instance_id,
                exposure.recorded_at,
                query.transaction_time,
            ):
                continue
            return True
        return False

    def _latest_attitude(self, idx: MemoryIndex, query: Query) -> Optional[ClaimRevision]:
        if query.target_mind_instance_id is None:
            return None
        candidates = []
        for claim in idx.scenario.claims:
            holder = claim.holder_mind_instance_id
            if holder is None:
                continue
            if claim.subject != query.subject or claim.predicate != query.predicate:
                continue
            target_about = query.about_world_branch_id or query.world_branch_id
            if idx.claim_about_branch(claim) != target_about:
                continue
            if not idx.branch_record_eligible(
                idx.claim_context_branch(claim), query.world_branch_id, claim.recorded_at, query.transaction_time
            ):
                continue
            if not idx.mind_record_eligible(
                holder, query.target_mind_instance_id, claim.recorded_at, query.transaction_time
            ):
                continue
            if not _active_interval(claim.valid_from, claim.valid_to, query.valid_time):
                continue
            candidates.append(claim)
        return max(candidates, key=lambda x: (x.recorded_at, x.revision_id)) if candidates else None


class LineageOnlyResolver(NCMResolver):
    """Ablation: branch + cognitive lineage + exposure, but no ancestry policy."""

    name = "B5a_lineage_only"

    def answer(self, scenario: Scenario, query: Query) -> str:
        if query.kind not in {"disclose", "source_count"}:
            return super().answer(scenario, query)
        idx = MemoryIndex(scenario)
        claim = self._claim_for_query(idx, query)
        if claim is None:
            return "unknown" if query.kind == "disclose" else "0"
        if query.kind == "disclose":
            clearance = REQUESTER_CLEARANCE.get(query.requester_id or "public_user", 0)
            return self._format_bool(POLICY_RANK[claim.policy_label] <= clearance)
        return str(len(claim.source_event_ids) + len(claim.derives_from_claim_ids))


class PolicyOnlyCharacterResolver(BranchScopedCharacterResolver):
    """Ablation: branch + provenance policy, but copied minds collapse."""

    name = "B5b_policy_only"

    def answer(self, scenario: Scenario, query: Query) -> str:
        if query.kind not in {"disclose", "source_count"}:
            return super().answer(scenario, query)
        idx = MemoryIndex(scenario)
        claim = self._claim_for_query(idx, query)
        if claim is None:
            return "unknown" if query.kind == "disclose" else "0"
        if not idx.branch_record_eligible(
            idx.claim_context_branch(claim), query.world_branch_id, claim.recorded_at, query.transaction_time
        ):
            return "unknown" if query.kind == "disclose" else "0"
        if query.kind == "disclose":
            clearance = REQUESTER_CLEARANCE.get(query.requester_id or "public_user", 0)
            return self._format_bool(POLICY_RANK[idx.strictest_policy(claim)] <= clearance)
        return str(len(idx.origin_families(claim)))
