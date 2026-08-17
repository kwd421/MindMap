from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from typing import Iterable

from mindmap.canonical.model import CommonEvent

from .commitment import event_hash, journal_head, projection_hash
from .model import (
    Alert,
    JournalCommitment,
    ObserverSurface,
    ProjectionCommitment,
)


KNOWN_TYPES = frozenset(
    {
        "principal_create",
        "mind_create",
        "world_create",
        "placement",
        "lineage",
        "evidence",
        "world_claim",
        "attitude",
        "exposure",
        "policy",
        "justification",
        "snapshot_member",
        "authorization",
    }
)


class GenericObserver:
    name = "G_generic_observer_v0.2"

    def inspect(
        self,
        events: Iterable[CommonEvent],
        *,
        surface: ObserverSurface,
        journal_commitment: JournalCommitment | None = None,
        projection_commitment: ProjectionCommitment | None = None,
        projection_rows: Iterable[tuple[str, str]] = (),
    ) -> tuple[Alert, ...]:
        rows = tuple(events)
        alerts: list[Alert] = []
        alerts.extend(self._byte_alerts(rows))
        if surface >= ObserverSurface.LOCAL_SCHEMA:
            alerts.extend(self._local_alerts(rows))
        if surface >= ObserverSurface.SEMANTIC_JOURNAL:
            alerts.extend(self._semantic_alerts(rows))
        if surface >= ObserverSurface.EXTERNAL_COMMITMENT:
            alerts.extend(self._commitment_alerts(rows, journal_commitment))
        if surface >= ObserverSurface.PROJECTION_COMMITMENT:
            alerts.extend(
                self._projection_alerts(
                    rows,
                    journal_commitment,
                    projection_commitment,
                    tuple(projection_rows),
                )
            )
        return tuple(self._deduplicate(alerts))

    @staticmethod
    def _deduplicate(alerts: Iterable[Alert]) -> list[Alert]:
        seen: set[tuple[object, ...]] = set()
        output: list[Alert] = []
        for alert in alerts:
            key = (
                alert.rule,
                alert.candidate_event_ids,
                alert.constraint_ids,
                alert.surface,
                alert.detail,
            )
            if key not in seen:
                seen.add(key)
                output.append(alert)
        return output

    @staticmethod
    def _byte_alerts(events: tuple[CommonEvent, ...]) -> list[Alert]:
        alerts: list[Alert] = []
        seen: dict[str, str] = {}
        for event in events:
            digest = event_hash(event)
            if not event.event_id:
                alerts.append(
                    Alert(
                        "missing_event_id",
                        constraint_ids=frozenset({"event_id_nonempty"}),
                        surface=ObserverSurface.BYTES,
                    )
                )
            elif event.event_id in seen and seen[event.event_id] != digest:
                alerts.append(
                    Alert(
                        "duplicate_conflicting_event_id",
                        candidate_event_ids=frozenset({event.event_id}),
                        constraint_ids=frozenset({"event_id_unique"}),
                        surface=ObserverSurface.BYTES,
                    )
                )
            else:
                seen[event.event_id] = digest
        return alerts

    @staticmethod
    def _attrs(event: CommonEvent) -> dict[str, str]:
        return dict(event.attributes)

    def _local_alerts(self, events: tuple[CommonEvent, ...]) -> list[Alert]:
        alerts: list[Alert] = []
        principals = {e.object_id for e in events if e.event_type == "principal_create"}
        minds = {e.object_id for e in events if e.event_type == "mind_create"}
        branches = {e.object_id for e in events if e.event_type == "world_create"}
        placements = {e.object_id for e in events if e.event_type == "placement"}
        evidence = {e.object_id for e in events if e.event_type == "evidence"}
        snapshots = {e.snapshot_id for e in events if e.event_type == "snapshot_member"}

        def require(event: CommonEvent, condition: bool, rule: str, constraint: str) -> None:
            if not condition:
                alerts.append(
                    Alert(
                        rule,
                        candidate_event_ids=frozenset({event.event_id}),
                        constraint_ids=frozenset({constraint}),
                        surface=ObserverSurface.LOCAL_SCHEMA,
                    )
                )

        for event in events:
            if event.event_type not in KNOWN_TYPES:
                alerts.append(
                    Alert(
                        "unknown_event_type",
                        candidate_event_ids=frozenset({event.event_id}),
                        constraint_ids=frozenset({"known_event_type"}),
                        surface=ObserverSurface.LOCAL_SCHEMA,
                        detail=event.event_type,
                    )
                )
                continue
            require(event, event.system_time >= 0, "invalid_system_time", "system_time_nonnegative")
            require(
                event,
                event.valid_to is None or event.valid_to > event.valid_from,
                "invalid_valid_interval",
                "valid_interval_half_open",
            )

            match event.event_type:
                case "principal_create":
                    require(event, bool(event.object_id), "principal_missing_id", "principal_required_fields")
                case "mind_create":
                    require(event, bool(event.object_id and event.actor_principal_id), "mind_missing_fields", "mind_required_fields")
                    require(event, event.actor_principal_id in principals, "mind_unknown_principal", "mind_principal_fk")
                case "world_create":
                    require(event, bool(event.object_id), "world_missing_id", "world_required_fields")
                    parent = self._attrs(event).get("parent") or None
                    require(event, parent is None or parent in branches, "world_unknown_parent", "world_parent_fk")
                case "placement":
                    require(event, bool(event.object_id and event.destination_mind_instance_id and event.about_world_branch_id), "placement_missing_fields", "placement_required_fields")
                    require(event, event.destination_mind_instance_id in minds, "placement_unknown_mind", "placement_mind_fk")
                    require(event, event.about_world_branch_id in branches, "placement_unknown_world", "placement_world_fk")
                case "lineage":
                    require(event, bool(event.destination_mind_instance_id and event.lineage_kind), "lineage_missing_fields", "lineage_required_fields")
                    require(event, event.destination_mind_instance_id in minds, "lineage_unknown_destination", "lineage_destination_fk")
                    require(event, event.source_mind_instance_id is None or event.source_mind_instance_id in minds, "lineage_unknown_source", "lineage_source_fk")
                    require(event, event.snapshot_id is None or event.snapshot_id in snapshots, "lineage_unknown_snapshot", "lineage_snapshot_fk")
                case "evidence":
                    require(event, bool(event.object_id and event.proposition_id and event.about_world_branch_id), "evidence_missing_fields", "evidence_required_fields")
                    require(event, event.about_world_branch_id in branches, "evidence_unknown_world", "evidence_world_fk")
                    require(event, event.actor_mind_instance_id is None or event.actor_mind_instance_id in minds, "evidence_unknown_actor_mind", "evidence_actor_mind_fk")
                    require(event, event.source_placement_id is None or event.source_placement_id in placements, "evidence_unknown_placement", "evidence_placement_fk")
                case "world_claim":
                    require(event, bool(event.proposition_id and event.about_world_branch_id), "world_claim_missing_fields", "world_claim_required_fields")
                    require(event, event.about_world_branch_id in branches, "world_claim_unknown_world", "world_claim_world_fk")
                case "attitude":
                    require(event, bool(event.destination_mind_instance_id and event.proposition_id and event.about_world_branch_id), "attitude_missing_fields", "attitude_required_fields")
                    require(event, event.destination_mind_instance_id in minds, "attitude_unknown_mind", "attitude_mind_fk")
                    require(event, event.about_world_branch_id in branches, "attitude_unknown_world", "attitude_world_fk")
                case "exposure":
                    require(event, bool(event.destination_mind_instance_id and event.object_id and event.transfer_kind), "exposure_missing_fields", "exposure_required_fields")
                    require(event, event.destination_mind_instance_id in minds, "exposure_unknown_destination", "exposure_destination_fk")
                    require(event, event.source_mind_instance_id is None or event.source_mind_instance_id in minds, "exposure_unknown_source", "exposure_source_fk")
                    require(event, event.object_id in evidence, "exposure_unknown_evidence", "exposure_evidence_fk")
                case "policy":
                    require(event, bool(event.object_id and event.policy_operation), "policy_missing_fields", "policy_required_fields")
                    require(event, event.object_id in evidence, "policy_unknown_evidence", "policy_evidence_fk")
                case "justification":
                    require(event, bool(event.object_id and event.proposition_id and event.derivation_members), "justification_missing_fields", "justification_required_fields")
                    for member in event.derivation_members:
                        require(event, member in evidence, "justification_unknown_member", "justification_member_fk")
                case "snapshot_member":
                    require(event, bool(event.snapshot_id and event.object_kind and event.object_id), "snapshot_member_missing_fields", "snapshot_member_required_fields")
                    if event.object_kind == "evidence":
                        require(event, event.object_id in evidence, "snapshot_unknown_evidence", "snapshot_evidence_fk")
                case "authorization":
                    require(event, bool(event.object_id and event.policy_operation), "authorization_missing_fields", "authorization_required_fields")
                    require(event, event.source_mind_instance_id is None or event.source_mind_instance_id in minds, "authorization_unknown_source", "authorization_source_fk")
                    require(event, event.destination_mind_instance_id is None or event.destination_mind_instance_id in minds, "authorization_unknown_destination", "authorization_destination_fk")
        return alerts

    def _semantic_alerts(self, events: tuple[CommonEvent, ...]) -> list[Alert]:
        alerts: list[Alert] = []
        attrs = {event.event_id: self._attrs(event) for event in events}
        principal_by_mind = {
            event.object_id: event.actor_principal_id
            for event in events
            if event.event_type == "mind_create" and event.object_id
        }
        branches = {
            event.object_id: self._attrs(event).get("parent") or None
            for event in events
            if event.event_type == "world_create" and event.object_id
        }
        evidence_by_id = {
            event.object_id: event
            for event in events
            if event.event_type == "evidence" and event.object_id
        }
        exposures = [event for event in events if event.event_type == "exposure"]
        lineage = [event for event in events if event.event_type == "lineage"]
        authorizations = [event for event in events if event.event_type == "authorization"]
        policies = [event for event in events if event.event_type == "policy"]
        justifications = [event for event in events if event.event_type == "justification"]

        def add(rule: str, event_ids: set[str], constraint: str, detail: str = "") -> None:
            alerts.append(
                Alert(
                    rule,
                    candidate_event_ids=frozenset(event_ids),
                    constraint_ids=frozenset({constraint}),
                    surface=ObserverSurface.SEMANTIC_JOURNAL,
                    detail=detail,
                )
            )

        # Cycle checks are performed over the complete visible relation, not event order.
        for branch in branches:
            seen: set[str] = set()
            cursor: str | None = branch
            while cursor is not None:
                if cursor in seen:
                    add("world_branch_cycle", {branch}, "world_branch_acyclic")
                    break
                seen.add(cursor)
                cursor = branches.get(cursor)

        graph: dict[str, list[str]] = defaultdict(list)
        for edge in lineage:
            if edge.source_mind_instance_id and edge.destination_mind_instance_id:
                graph[edge.source_mind_instance_id].append(edge.destination_mind_instance_id)
        for start in graph:
            stack = [(start, frozenset())]
            while stack:
                node, path = stack.pop()
                if node in path:
                    add("lineage_cycle", {start}, "lineage_acyclic")
                    break
                for child in graph.get(node, []):
                    stack.append((child, path | {node}))

        for event in events:
            if event.event_type == "evidence" and event.actor_mind_instance_id:
                expected = principal_by_mind.get(event.actor_mind_instance_id)
                if expected and event.actor_principal_id and expected != event.actor_principal_id:
                    add("actor_principal_mind_mismatch", {event.event_id}, "actor_principal_matches_mind")

        for edge in lineage:
            source = edge.source_mind_instance_id
            destination = edge.destination_mind_instance_id
            if not source or not destination:
                continue
            same = principal_by_mind.get(source) == principal_by_mind.get(destination)
            if edge.lineage_kind == "operational_replica" and not same:
                add("operational_replica_principal_mismatch", {edge.event_id}, "operational_replica_same_principal")
            if edge.lineage_kind == "identity_fork" and same:
                add("identity_fork_principal_not_distinct", {edge.event_id}, "identity_fork_distinct_principal")

        def authorization_active(exposure: CommonEvent) -> bool:
            if not exposure.authorization_id:
                return False
            candidates = sorted(
                (
                    event
                    for event in authorizations
                    if event.object_id == exposure.authorization_id
                    and event.system_time <= exposure.system_time
                ),
                key=lambda event: (event.system_time, event.event_id),
            )
            return bool(candidates and candidates[-1].policy_operation == "grant")

        acquired: set[tuple[str, str]] = set()
        for event in sorted(events, key=lambda value: (value.system_time, value.event_id)):
            if event.event_type == "evidence" and event.object_id and event.actor_mind_instance_id:
                acquired.add((event.actor_mind_instance_id, event.object_id))
            if event.event_type != "exposure" or not event.destination_mind_instance_id or not event.object_id:
                continue
            if event.transfer_kind == "state_replication":
                source = event.source_mind_instance_id
                destination = event.destination_mind_instance_id
                same = bool(source) and principal_by_mind.get(source) == principal_by_mind.get(destination)
                edge_ok = any(
                    edge.source_mind_instance_id == source
                    and edge.destination_mind_instance_id == destination
                    and edge.lineage_kind in {"operational_replica", "checkpoint_branch"}
                    and edge.system_time <= event.system_time
                    for edge in lineage
                )
                if not (same and edge_ok and authorization_active(event)):
                    add("invalid_state_replication", {event.event_id}, "state_replication_authorized")
                    continue
            if event.source_mind_instance_id and (event.source_mind_instance_id, event.object_id) not in acquired:
                add("source_not_exposed", {event.event_id}, "transfer_source_exposed")
                continue
            if event.transfer_kind != "forget_active":
                acquired.add((event.destination_mind_instance_id, event.object_id))

        for attitude in (event for event in events if event.event_type == "attitude"):
            source_evidence = attrs[attitude.event_id].get("source_evidence_id")
            if source_evidence and attitude.destination_mind_instance_id:
                if (attitude.destination_mind_instance_id, source_evidence) not in acquired:
                    add("attitude_without_declared_exposure", {attitude.event_id}, "declared_adoption_requires_exposure")

        # Snapshot membership is checked after all source objects are indexed.
        snapshot_cutoffs = {
            edge.snapshot_id: edge.snapshot_cutoff
            for edge in lineage
            if edge.snapshot_id and edge.snapshot_cutoff is not None
        }
        for member in (event for event in events if event.event_type == "snapshot_member"):
            source = evidence_by_id.get(member.object_id) if member.object_kind == "evidence" else None
            cutoff = snapshot_cutoffs.get(member.snapshot_id)
            if source is not None and cutoff is not None and source.system_time > cutoff:
                add("snapshot_member_post_cutoff", {member.event_id, source.event_id}, "snapshot_member_before_cutoff")

        # Provenance checks are two-pass and independent of event append order.
        for evidence in evidence_by_id.values():
            parent_id = attrs[evidence.event_id].get("derived_from") or evidence.raw_evidence_ref
            if not parent_id:
                continue
            parent = evidence_by_id.get(parent_id)
            if parent is None:
                add("derived_evidence_missing_parent", {evidence.event_id}, "derivation_parent_exists")
                continue
            declassified = any(
                policy.object_id == parent_id
                and policy.policy_operation == "declassify"
                and policy.system_time <= evidence.system_time
                for policy in policies
            )
            if parent.policy_label not in {None, "public"} and evidence.policy_label == "public" and not declassified:
                add("policy_laundering", {evidence.event_id, parent.event_id}, "derived_policy_not_weaker")
            if evidence.source_family_id != parent.source_family_id:
                add("origin_family_laundering", {evidence.event_id, parent.event_id}, "derived_origin_family_preserved")

        for support in justifications:
            members = [evidence_by_id.get(member) for member in support.derivation_members]
            if any(member is None for member in members):
                continue
            minimum = int(attrs[support.event_id].get("min_independent_sources", "1"))
            families = {member.source_family_id for member in members if member is not None}
            if len(families) < minimum:
                add("non_independent_support", {support.event_id, *support.derivation_members}, "minimum_independent_sources")

        return alerts

    @staticmethod
    def _commitment_alerts(
        events: tuple[CommonEvent, ...],
        commitment: JournalCommitment | None,
    ) -> list[Alert]:
        if commitment is None:
            return [
                Alert(
                    "missing_external_journal_commitment",
                    constraint_ids=frozenset({"journal_commitment_required"}),
                    surface=ObserverSurface.EXTERNAL_COMMITMENT,
                )
            ]
        alerts: list[Alert] = []
        actual_ids = tuple(event.event_id for event in events)
        expected_hashes = dict(commitment.event_hashes)
        if actual_ids != commitment.ordered_event_ids:
            candidates = set(actual_ids) ^ set(commitment.ordered_event_ids)
            alerts.append(
                Alert(
                    "journal_sequence_or_membership_mismatch",
                    candidate_event_ids=frozenset(candidates),
                    constraint_ids=frozenset({"journal_sequence_committed"}),
                    surface=ObserverSurface.EXTERNAL_COMMITMENT,
                )
            )
        for event in events:
            expected = expected_hashes.get(event.event_id)
            if expected is not None and event_hash(event) != expected:
                alerts.append(
                    Alert(
                        "journal_event_hash_mismatch",
                        candidate_event_ids=frozenset({event.event_id}),
                        constraint_ids=frozenset({"journal_event_hash_committed"}),
                        surface=ObserverSurface.EXTERNAL_COMMITMENT,
                    )
                )
        if journal_head(events, commitment.previous_head_hash) != commitment.head_hash:
            alerts.append(
                Alert(
                    "journal_head_mismatch",
                    constraint_ids=frozenset({"journal_head_committed"}),
                    surface=ObserverSurface.EXTERNAL_COMMITMENT,
                )
            )
        return alerts

    @staticmethod
    def _projection_alerts(
        events: tuple[CommonEvent, ...],
        journal_commitment: JournalCommitment | None,
        projection_commitment: ProjectionCommitment | None,
        projection_rows: tuple[tuple[str, str], ...],
    ) -> list[Alert]:
        if journal_commitment is None or projection_commitment is None:
            return [
                Alert(
                    "missing_projection_commitment",
                    constraint_ids=frozenset({"projection_commitment_required"}),
                    surface=ObserverSurface.PROJECTION_COMMITMENT,
                )
            ]
        alerts: list[Alert] = []
        if projection_commitment.journal_head_hash != journal_commitment.head_hash:
            alerts.append(
                Alert(
                    "projection_bound_to_wrong_journal_head",
                    constraint_ids=frozenset({"projection_journal_head_binding"}),
                    surface=ObserverSurface.PROJECTION_COMMITMENT,
                )
            )
        if projection_hash(projection_rows) != projection_commitment.projection_hash:
            alerts.append(
                Alert(
                    "projection_content_mismatch",
                    constraint_ids=frozenset({"projection_content_committed"}),
                    surface=ObserverSurface.PROJECTION_COMMITMENT,
                )
            )
        return alerts
