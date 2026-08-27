from __future__ import annotations

import hashlib
import random
from typing import Optional

from .core import (
    ClaimRevision,
    EvidenceEvent,
    ExposureTransition,
    MindInstance,
    Query,
    Scenario,
    WorldBranch,
)

ROOMS = ["Room 1", "Room 2", "Room 3", "Room 4", "Room 5", "Room 6", "Room 7"]
ATTITUDES = ["believe", "suspect", "disbelieve", "suspend"]


class ScenarioBuilder:
    def __init__(self, scenario_id: str, template: str, seed: int):
        self.scenario_id = scenario_id
        self.template = template
        self.seed = seed
        self.evidence: list[EvidenceEvent] = []
        self.claims: list[ClaimRevision] = []
        self.exposures: list[ExposureTransition] = []
        self.minds: list[MindInstance] = []
        self.branches: list[WorldBranch] = []
        self.queries: list[Query] = []
        self.metadata: dict[str, str] = {}
        self._e = self._c = self._x = self._q = 0

    def add_branch(self, branch_id: str, parent: Optional[str] = None, fork_valid_time: Optional[int] = None, fork_recorded_at: Optional[int] = None) -> None:
        self.branches.append(WorldBranch(branch_id, parent, fork_valid_time, fork_recorded_at))

    def add_mind(self, mind_id: str, character_id: str = "char-A", parent: Optional[str] = None, fork_recorded_at: Optional[int] = None, inherited_through_tx: Optional[int] = None, snapshot: Optional[str] = None, branch: str = "main") -> None:
        self.minds.append(MindInstance(mind_id, character_id, parent, fork_recorded_at, inherited_through_tx, snapshot, branch))

    def add_event(self, text: str, speaker: str, recorded_at: int, branch: str = "main", occurred_at: Optional[int] = None, valid_from: Optional[int] = None, valid_to: Optional[int] = None, origin_family: Optional[str] = None, policy: str = "public") -> str:
        self._e += 1
        event_id = f"{self.scenario_id}-e{self._e:02d}"
        self.evidence.append(EvidenceEvent(
            event_id=event_id,
            raw_payload=text,
            source_span=text,
            speaker_instance_id=speaker,
            occurred_at=recorded_at if occurred_at is None else occurred_at,
            valid_from=recorded_at if valid_from is None else valid_from,
            valid_to=valid_to,
            recorded_at=recorded_at,
            world_branch_id=branch,
            origin_family_id=origin_family or event_id,
            integrity_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            policy_label=policy,
        ))
        return event_id

    def add_claim(self, subject: str, predicate: str, obj: str, recorded_at: int, branch: str = "main", about_branch: Optional[str] = None, asserted_in_branch: Optional[str] = None, holder: Optional[str] = None, attitude: str = "world", valid_from: int = 0, valid_to: Optional[int] = None, source_events: tuple[str, ...] = (), derives_from: tuple[str, ...] = (), supersedes: Optional[str] = None, policy: str = "public", claim_id: Optional[str] = None) -> tuple[str, str]:
        self._c += 1
        claim_id = claim_id or f"{self.scenario_id}-c{self._c:02d}"
        revision_id = f"{claim_id}-r{self._c:02d}"
        self.claims.append(ClaimRevision(
            claim_id=claim_id,
            revision_id=revision_id,
            subject=subject,
            predicate=predicate,
            object=obj,
            attitude_or_modality=attitude,
            holder_mind_instance_id=holder,
            valid_from=valid_from,
            valid_to=valid_to,
            recorded_at=recorded_at,
            world_branch_id=branch,
            about_world_branch_id=about_branch or branch,
            asserted_in_world_branch_id=asserted_in_branch or branch,
            source_event_ids=source_events,
            derives_from_claim_ids=derives_from,
            supersedes_revision_id=supersedes,
            joint_hypothesis_id=f"{revision_id}-h",
            calibrated_mass=1.0,
            policy_label=policy,
        ))
        return claim_id, revision_id

    def add_exposure(self, mind: str, object_id: str, operation: str, recorded_at: int, branch: str = "main", source_branch: Optional[str] = None, destination_branch: Optional[str] = None, source_mind: Optional[str] = None, object_kind: str = "evidence", policy: str = "public", parent_exposure_id: Optional[str] = None) -> str:
        self._x += 1
        exposure_id = f"{self.scenario_id}-x{self._x:02d}"
        self.exposures.append(ExposureTransition(
            exposure_id=exposure_id,
            mind_instance_id=mind,
            object_kind=object_kind,
            object_id=object_id,
            operation=operation,
            source_mind_instance_id=source_mind,
            occurred_at=recorded_at,
            recorded_at=recorded_at,
            world_branch_id=branch,
            source_world_branch_id=source_branch or branch,
            destination_world_branch_id=destination_branch or branch,
            parent_exposure_id=parent_exposure_id,
            policy_label=policy,
        ))
        return exposure_id

    def add_query(self, kind: str, expected: str, tx: int, tv: int = 100, branch: str = "main", target_mind: Optional[str] = None, requester: Optional[str] = None, subject: Optional[str] = None, predicate: Optional[str] = None, evidence_id: Optional[str] = None, claim_id: Optional[str] = None, about_branch: Optional[str] = None, label: Optional[str] = None) -> None:
        self._q += 1
        self.queries.append(Query(
            query_id=f"{self.scenario_id}-q{self._q:02d}",
            scenario_id=self.scenario_id,
            kind=kind,
            world_branch_id=branch,
            valid_time=tv,
            transaction_time=tx,
            expected=expected,
            target_mind_instance_id=target_mind,
            requester_id=requester,
            subject=subject,
            predicate=predicate,
            evidence_id=evidence_id,
            claim_id=claim_id,
            about_world_branch_id=about_branch or branch,
            metadata={"label": label or kind},
        ))

    def build(self) -> Scenario:
        return Scenario(self.scenario_id, self.template, self.seed, self.evidence, self.claims, self.exposures, self.minds, self.branches, self.queries, self.metadata)


def _rooms(rr: random.Random, n: int = 3) -> list[str]:
    return rr.sample(ROOMS, n)


def _base_fork_builder(sid: str, template: str, seed: int, rr: random.Random) -> tuple[ScenarioBuilder, str, str, str]:
    b = ScenarioBuilder(sid, template, seed)
    b.add_branch("main")
    b.add_mind("A0", branch="main")
    b.add_mind("A1", parent="A0", fork_recorded_at=10, inherited_through_tx=10, branch="main")
    b.add_mind("A2", parent="A0", fork_recorded_at=10, inherited_through_tx=10, branch="main")
    old_room, new_room, decoy = _rooms(rr, 3)
    e0 = b.add_event(f"The key is initially in {old_room}.", "A0", 5)
    b.add_claim("key", "located_in", old_room, 5, valid_from=0, source_events=(e0,))
    b.add_exposure("A0", e0, "observe", 5)
    b.add_claim("key", "located_in", old_room, 5, holder="A0", attitude="believe", source_events=(e0,))
    b.metadata.update({"old_room": old_room, "new_room": new_room, "decoy": decoy})
    return b, old_room, new_room, decoy


def build_mind_fork_isolation(sid: str, seed: int) -> Scenario:
    rr = random.Random(seed)
    b, old_room, new_room, _ = _base_fork_builder(sid, "mind_fork_isolation", seed, rr)
    e1 = b.add_event(f"After the fork, A1 sees the key moved to {new_room}.", "A1", 12)
    b.add_claim("key", "located_in", new_room, 12, valid_from=12, source_events=(e1,))
    b.add_exposure("A1", e1, "observe", 12)
    b.add_claim("key", "located_in", new_room, 12, holder="A1", attitude="believe", source_events=(e1,))
    b.add_query("world", new_room, 20, subject="key", predicate="located_in")
    b.add_query("access", "yes", 20, target_mind="A1", evidence_id=e1)
    b.add_query("access", "no", 20, target_mind="A2", evidence_id=e1)
    b.add_query("attitude", f"believe:{new_room}", 20, target_mind="A1", subject="key", predicate="located_in")
    b.add_query("attitude", f"believe:{old_room}", 20, target_mind="A2", subject="key", predicate="located_in")
    b.add_query("lineage", "yes", 20, target_mind="A2", evidence_id=b.evidence[0].event_id)
    return b.build()


def build_selective_transfer(sid: str, seed: int) -> Scenario:
    rr = random.Random(seed)
    b, old_room, new_room, _ = _base_fork_builder(sid, "selective_transfer", seed, rr)
    e1 = b.add_event(f"A1 directly observes the key in {new_room}.", "A1", 12, policy="private")
    b.add_claim("key", "located_in", new_room, 12, valid_from=12, source_events=(e1,), policy="private")
    b.add_exposure("A1", e1, "observe", 12, policy="private")
    b.add_claim("key", "located_in", new_room, 12, holder="A1", attitude="believe", source_events=(e1,), policy="private")
    b.add_exposure("A2", e1, "receive", 20, source_mind="A1", policy="private")
    attitude = rr.choice(ATTITUDES[:3])
    b.add_claim("key", "located_in", new_room, 22, holder="A2", attitude=attitude, source_events=(e1,), policy="private")
    b.add_query("access", "no", 15, target_mind="A2", evidence_id=e1, label="pre_transfer_access")
    b.add_query("access", "yes", 25, target_mind="A2", evidence_id=e1, label="post_transfer_access")
    b.add_query("attitude", f"believe:{old_room}", 18, target_mind="A2", subject="key", predicate="located_in", label="pre_adoption_attitude")
    b.add_query("attitude", f"{attitude}:{new_room}", 25, target_mind="A2", subject="key", predicate="located_in", label="post_transfer_attitude")
    b.add_query("attitude", f"believe:{new_room}", 25, target_mind="A1", subject="key", predicate="located_in")
    b.add_query("world", new_room, 25, subject="key", predicate="located_in")
    return b.build()


def build_sealed_memory(sid: str, seed: int) -> Scenario:
    rr = random.Random(seed)
    b, _, new_room, _ = _base_fork_builder(sid, "sealed_memory", seed, rr)
    e1 = b.add_event(f"A1 records that the key is in {new_room}.", "A1", 12, policy="private")
    b.add_claim("key", "located_in", new_room, 12, valid_from=12, source_events=(e1,), policy="private")
    b.add_exposure("A1", e1, "observe", 12, policy="private")
    b.add_claim("key", "located_in", new_room, 12, holder="A1", attitude="believe", source_events=(e1,), policy="private")
    b.add_exposure("A2", e1, "receive", 20, source_mind="A1", policy="private")
    b.add_claim("key", "located_in", new_room, 22, holder="A2", attitude="believe", source_events=(e1,), policy="private")
    b.add_exposure("A2", e1, "seal", 30, source_mind="A2", policy="sealed")
    b.add_query("access", "yes", 25, target_mind="A2", evidence_id=e1)
    b.add_query("access", "no", 35, target_mind="A2", evidence_id=e1)
    b.add_query("access", "yes", 35, target_mind="A1", evidence_id=e1)
    b.add_query("attitude", f"believe:{new_room}", 35, target_mind="A2", subject="key", predicate="located_in")
    b.add_query("ever_exposed", "yes", 35, target_mind="A2", evidence_id=e1, label="historically_exposed_after_seal")
    b.add_query("lineage", "yes", 35, target_mind="A2", evidence_id=b.evidence[0].event_id)
    return b.build()


def build_restore_gap(sid: str, seed: int) -> Scenario:
    rr = random.Random(seed)
    b = ScenarioBuilder(sid, "restore_gap", seed)
    b.add_branch("main")
    b.add_mind("A0", branch="main")
    old_room, mid_room, new_room = _rooms(rr, 3)
    e0 = b.add_event(f"The key is in {old_room}.", "A0", 5)
    b.add_exposure("A0", e0, "observe", 5)
    b.add_claim("key", "located_in", old_room, 5, holder="A0", attitude="believe", source_events=(e0,))
    e1 = b.add_event(f"The key is moved to {mid_room} before backup.", "A0", 12)
    b.add_exposure("A0", e1, "observe", 12)
    b.add_claim("key", "located_in", mid_room, 12, holder="A0", attitude="believe", source_events=(e1,))
    e2 = b.add_event(f"After backup, the key is moved to {new_room}.", "A0", 20)
    b.add_exposure("A0", e2, "observe", 20)
    b.add_claim("key", "located_in", new_room, 20, holder="A0", attitude="believe", source_events=(e2,))
    b.add_mind("A_restore", parent="A0", fork_recorded_at=30, inherited_through_tx=15, snapshot="snap-15", branch="main")
    b.add_query("lineage", "yes", 35, target_mind="A_restore", evidence_id=e0)
    b.add_query("lineage", "yes", 35, target_mind="A_restore", evidence_id=e1)
    b.add_query("lineage", "no", 35, target_mind="A_restore", evidence_id=e2)
    b.add_query("access", "yes", 35, target_mind="A0", evidence_id=e2)
    b.add_query("attitude", f"believe:{mid_room}", 35, target_mind="A_restore", subject="key", predicate="located_in")
    b.add_query("attitude", f"believe:{new_room}", 35, target_mind="A0", subject="key", predicate="located_in")
    return b.build()


def build_world_fork_isolation(sid: str, seed: int) -> Scenario:
    rr = random.Random(seed)
    b = ScenarioBuilder(sid, "world_fork_isolation", seed)
    b.add_branch("main")
    b.add_branch("alt", parent="main", fork_valid_time=10, fork_recorded_at=10)
    b.add_mind("A0", branch="main")
    b.add_mind("A_main", parent="A0", fork_recorded_at=10, inherited_through_tx=10, branch="main")
    b.add_mind("A_alt", parent="A0", fork_recorded_at=10, inherited_through_tx=10, branch="alt")
    old_room, main_room, alt_room = _rooms(rr, 3)
    e0 = b.add_event(f"Before divergence, the key is in {old_room}.", "A0", 5)
    b.add_claim("key", "located_in", old_room, 5, valid_from=0, source_events=(e0,))
    em = b.add_event(f"On main, the key moves to {main_room}.", "A_main", 12, branch="main")
    b.add_claim("key", "located_in", main_room, 12, branch="main", valid_from=12, source_events=(em,))
    ea = b.add_event(f"On alt, the key moves to {alt_room}.", "A_alt", 13, branch="alt")
    b.add_claim("key", "located_in", alt_room, 13, branch="alt", valid_from=12, source_events=(ea,))
    b.add_exposure("A_main", em, "observe", 12, branch="main")
    b.add_exposure("A_alt", ea, "observe", 13, branch="alt")
    b.add_claim("key", "located_in", main_room, 12, branch="main", holder="A_main", attitude="believe", source_events=(em,))
    b.add_claim("key", "located_in", alt_room, 13, branch="alt", holder="A_alt", attitude="believe", source_events=(ea,))
    b.add_query("world", main_room, 20, branch="main", subject="key", predicate="located_in")
    b.add_query("world", alt_room, 20, branch="alt", subject="key", predicate="located_in")
    b.add_query("attitude", f"believe:{main_room}", 20, branch="main", target_mind="A_main", subject="key", predicate="located_in")
    b.add_query("attitude", f"believe:{alt_room}", 20, branch="alt", target_mind="A_alt", subject="key", predicate="located_in")
    b.add_query("access", "no", 20, branch="main", target_mind="A_main", evidence_id=ea)
    b.add_query("access", "no", 20, branch="alt", target_mind="A_alt", evidence_id=em)
    return b.build()


def build_cross_world_report(sid: str, seed: int) -> Scenario:
    """A belief held in W2 can remain explicitly about W1."""
    rr = random.Random(seed)
    b = ScenarioBuilder(sid, "cross_world_report", seed)
    b.add_branch("w1")
    b.add_branch("w2")
    b.add_mind("M1", character_id="char-A", branch="w1")
    b.add_mind("M2", character_id="char-B", branch="w2")
    room_w1, room_w2 = _rooms(rr, 2)
    e1 = b.add_event(f"In W1, M1 observes the key in {room_w1}.", "M1", 10, branch="w1")
    b.add_claim("key", "located_in", room_w1, 10, branch="w1", about_branch="w1", asserted_in_branch="w1", valid_from=10, source_events=(e1,))
    b.add_exposure("M1", e1, "observe", 10, branch="w1", source_branch="w1", destination_branch="w1")
    b.add_claim("key", "located_in", room_w1, 10, branch="w1", about_branch="w1", asserted_in_branch="w1", holder="M1", attitude="believe", source_events=(e1,))
    e2 = b.add_event(f"In W2, M2 observes the local key in {room_w2}.", "M2", 11, branch="w2")
    b.add_claim("key", "located_in", room_w2, 11, branch="w2", about_branch="w2", asserted_in_branch="w2", valid_from=11, source_events=(e2,))
    b.add_exposure("M2", e2, "observe", 11, branch="w2", source_branch="w2", destination_branch="w2")
    b.add_claim("key", "located_in", room_w2, 11, branch="w2", about_branch="w2", asserted_in_branch="w2", holder="M2", attitude="believe", source_events=(e2,))
    b.add_exposure("M2", e1, "receive", 20, branch="w2", source_branch="w1", destination_branch="w2", source_mind="M1")
    b.add_claim("key", "located_in", room_w1, 22, branch="w2", about_branch="w1", asserted_in_branch="w2", holder="M2", attitude="believe", source_events=(e1,))
    b.add_query("world", room_w1, 25, branch="w1", about_branch="w1", subject="key", predicate="located_in")
    b.add_query("world", room_w2, 25, branch="w2", about_branch="w2", subject="key", predicate="located_in")
    b.add_query("attitude", f"believe:{room_w1}", 25, branch="w2", about_branch="w1", target_mind="M2", subject="key", predicate="located_in", label="belief_in_w2_about_w1")
    b.add_query("attitude", f"believe:{room_w2}", 25, branch="w2", about_branch="w2", target_mind="M2", subject="key", predicate="located_in", label="belief_in_w2_about_w2")
    b.add_query("access", "yes", 25, branch="w2", target_mind="M2", evidence_id=e1)
    b.add_query("ever_exposed", "no", 19, branch="w2", target_mind="M2", evidence_id=e1)
    return b.build()


def build_private_derivation(sid: str, seed: int) -> Scenario:
    rr = random.Random(seed)
    b = ScenarioBuilder(sid, "private_derivation", seed)
    b.add_branch("main")
    b.add_mind("A0", branch="main")
    room = rr.choice(ROOMS)
    e1 = b.add_event(f"Private note: the key is in {room}.", "A0", 10, policy="private")
    c1, r1 = b.add_claim("key", "located_in", room, 10, source_events=(e1,), policy="private")
    e2 = b.add_event("A profile summary is generated from the private note.", "A0", 12, origin_family=b.evidence[-1].origin_family_id, policy="public")
    c2, _ = b.add_claim("key", "located_in", room, 12, source_events=(e2,), derives_from=(r1,), policy="public")
    b.add_query("disclose", "no", 20, requester="public_user", claim_id=c2)
    b.add_query("disclose", "yes", 20, requester="trusted_user", claim_id=c2)
    b.add_query("disclose", "yes", 20, requester="admin", claim_id=c2)
    b.add_query("source_count", "1", 20, claim_id=c2)
    b.add_query("world", room, 20, subject="key", predicate="located_in")
    b.add_query("disclose", "no", 11, requester="public_user", claim_id=c1)
    return b.build()


def build_rumor_laundering(sid: str, seed: int) -> Scenario:
    rr = random.Random(seed)
    b = ScenarioBuilder(sid, "rumor_laundering", seed)
    b.add_branch("main")
    b.add_mind("A0", branch="main")
    room = rr.choice(ROOMS)
    origin = f"{sid}-rumor-root"
    e1 = b.add_event(f"One anonymous rumor says the key is in {room}.", "A0", 8, origin_family=origin)
    _, r1 = b.add_claim("key", "located_in", room, 8, holder="A0", attitude="suspect", source_events=(e1,))
    e2 = b.add_event("A summary repeats the same rumor.", "A0", 10, origin_family=origin)
    c2, r2 = b.add_claim("key", "located_in", room, 10, holder="A0", attitude="suspect", source_events=(e2,), derives_from=(r1,))
    e3 = b.add_event("A profile repeats the summary once more.", "A0", 12, origin_family=origin)
    c3, _ = b.add_claim("key", "located_in", room, 12, holder="A0", attitude="suspect", source_events=(e3,), derives_from=(r2,))
    b.add_query("source_count", "1", 20, claim_id=c3)
    b.add_query("source_count", "1", 20, claim_id=c2)
    b.add_query("attitude", f"suspect:{room}", 20, target_mind="A0", subject="key", predicate="located_in")
    b.add_query("disclose", "yes", 20, requester="public_user", claim_id=c3)
    b.add_query("access", "no", 20, target_mind="A0", evidence_id=e1)
    b.add_query("world", "unknown", 20, subject="key", predicate="located_in")
    return b.build()


def build_backdated_correction(sid: str, seed: int) -> Scenario:
    rr = random.Random(seed)
    b = ScenarioBuilder(sid, "backdated_correction", seed)
    b.add_branch("main")
    b.add_mind("A0", branch="main")
    old_room, corrected_room = _rooms(rr, 2)
    e0 = b.add_event(f"Initial record says the key is in {old_room}.", "A0", 5)
    _, r0 = b.add_claim("key", "located_in", old_room, 5, valid_from=0, source_events=(e0,), claim_id=f"{sid}-location")
    e1 = b.add_event(f"A later audit establishes that since time 12 it was in {corrected_room}.", "A0", 30, occurred_at=12, valid_from=12)
    b.add_claim("key", "located_in", corrected_room, 30, valid_from=12, source_events=(e1,), supersedes=r0, claim_id=f"{sid}-location")
    b.add_query("world", old_room, 20, tv=20, subject="key", predicate="located_in", label="before_learning_correction")
    b.add_query("world", corrected_room, 35, tv=20, subject="key", predicate="located_in", label="after_learning_correction")
    b.add_query("world", old_room, 35, tv=8, subject="key", predicate="located_in", label="before_valid_change")
    b.add_query("world", corrected_room, 35, tv=12, subject="key", predicate="located_in")
    b.add_query("disclose", "yes", 35, requester="public_user", claim_id=f"{sid}-location")
    b.add_query("source_count", "1", 35, claim_id=f"{sid}-location")
    return b.build()


def build_belief_vs_world(sid: str, seed: int) -> Scenario:
    rr = random.Random(seed)
    b, old_room, true_room, decoy = _base_fork_builder(sid, "belief_vs_world", seed, rr)
    e1 = b.add_event(f"A1 verifies the key is in {true_room}.", "A1", 12)
    b.add_claim("key", "located_in", true_room, 12, valid_from=12, source_events=(e1,))
    b.add_exposure("A1", e1, "observe", 12)
    b.add_claim("key", "located_in", true_room, 12, holder="A1", attitude="believe", source_events=(e1,))
    e2 = b.add_event(f"A deceptive source tells A2 that the key is in {decoy}.", "B0", 14)
    b.add_exposure("A2", e2, "receive", 14, source_mind="B0")
    b.add_claim("key", "located_in", decoy, 16, holder="A2", attitude="believe", source_events=(e2,))
    b.add_query("world", true_room, 20, subject="key", predicate="located_in")
    b.add_query("attitude", f"believe:{true_room}", 20, target_mind="A1", subject="key", predicate="located_in")
    b.add_query("attitude", f"believe:{decoy}", 20, target_mind="A2", subject="key", predicate="located_in")
    b.add_query("access", "no", 20, target_mind="A2", evidence_id=e1)
    b.add_query("access", "yes", 20, target_mind="A2", evidence_id=e2)
    b.add_query("attitude", f"believe:{old_room}", 11, target_mind="A2", subject="key", predicate="located_in")
    return b.build()


def build_combined(sid: str, seed: int) -> Scenario:
    rr = random.Random(seed)
    b = ScenarioBuilder(sid, "combined", seed)
    b.add_branch("main")
    b.add_branch("alt", parent="main", fork_valid_time=10, fork_recorded_at=10)
    b.add_mind("A0", branch="main")
    b.add_mind("A1", parent="A0", fork_recorded_at=10, inherited_through_tx=10, branch="main")
    b.add_mind("A2", parent="A0", fork_recorded_at=10, inherited_through_tx=10, branch="main")
    b.add_mind("A_alt", parent="A0", fork_recorded_at=10, inherited_through_tx=10, branch="alt")
    old_room, main_room, alt_room, rumor_room = rr.sample(ROOMS, 4)
    e0 = b.add_event(f"Initially the key is in {old_room}.", "A0", 5)
    b.add_claim("key", "located_in", old_room, 5, valid_from=0, source_events=(e0,))
    b.add_exposure("A0", e0, "observe", 5)
    b.add_claim("key", "located_in", old_room, 5, holder="A0", attitude="believe", source_events=(e0,))
    em = b.add_event(f"A1 privately sees the key move to {main_room} on main.", "A1", 12, branch="main", policy="private")
    _, rm = b.add_claim("key", "located_in", main_room, 12, branch="main", valid_from=12, source_events=(em,), policy="private")
    b.add_exposure("A1", em, "observe", 12, branch="main", policy="private")
    b.add_claim("key", "located_in", main_room, 12, branch="main", holder="A1", attitude="believe", source_events=(em,), policy="private")
    ea = b.add_event(f"On alt the key moves to {alt_room}.", "A_alt", 13, branch="alt")
    b.add_claim("key", "located_in", alt_room, 13, branch="alt", valid_from=12, source_events=(ea,))
    b.add_exposure("A_alt", ea, "observe", 13, branch="alt")
    b.add_claim("key", "located_in", alt_room, 13, branch="alt", holder="A_alt", attitude="believe", source_events=(ea,))
    er = b.add_event(f"A rumor sent to A2 says {rumor_room}.", "B0", 15, branch="main")
    b.add_exposure("A2", er, "receive", 15, branch="main", source_mind="B0")
    b.add_claim("key", "located_in", rumor_room, 16, branch="main", holder="A2", attitude="suspect", source_events=(er,))
    b.add_exposure("A2", em, "receive", 20, branch="main", source_mind="A1", policy="private")
    b.add_claim("key", "located_in", main_room, 22, branch="main", holder="A2", attitude="believe", source_events=(em,), policy="private")
    b.add_exposure("A2", em, "seal", 30, branch="main", source_mind="A2", policy="sealed")
    summary_event = b.add_event("A public summary is derived from A1's private observation.", "A1", 24, branch="main", origin_family=b.evidence[-3].origin_family_id, policy="public")
    summary_claim, _ = b.add_claim("key", "located_in", main_room, 24, branch="main", source_events=(summary_event,), derives_from=(rm,), policy="public")
    b.add_query("world", main_room, 35, branch="main", subject="key", predicate="located_in")
    b.add_query("world", alt_room, 35, branch="alt", subject="key", predicate="located_in")
    b.add_query("access", "no", 18, branch="main", target_mind="A2", evidence_id=em)
    b.add_query("access", "no", 35, branch="main", target_mind="A2", evidence_id=em)
    b.add_query("attitude", f"believe:{main_room}", 35, branch="main", target_mind="A2", subject="key", predicate="located_in")
    b.add_query("disclose", "no", 35, branch="main", requester="public_user", claim_id=summary_claim)
    return b.build()


BUILDERS = [
    build_mind_fork_isolation,
    build_selective_transfer,
    build_sealed_memory,
    build_restore_gap,
    build_world_fork_isolation,
    build_cross_world_report,
    build_private_derivation,
    build_rumor_laundering,
    build_backdated_correction,
    build_belief_vs_world,
    build_combined,
]


def generate_scenarios(seed: int = 20260817, per_template: int = 24) -> list[Scenario]:
    scenarios: list[Scenario] = []
    counter = 0
    for template_index, builder in enumerate(BUILDERS):
        for j in range(per_template):
            counter += 1
            scenario_seed = seed + template_index * 100_003 + j * 1_009
            scenarios.append(builder(f"s{counter:04d}", scenario_seed))
    return scenarios
