from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from mindmap.canonical.model import CommonEvent
from mindmap.canonical.typed import TypedLedger

from .commitment import event_hash, journal_head, projection_hash
from .model import Alert, JournalCommitment, ObserverSurface, ProjectionCommitment


class TypedObserver:
    name = "T_typed_observer_v0.2"

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
        alerts.extend(self._duplicate_alerts(rows))

        ledger: TypedLedger | None = None
        if surface >= ObserverSurface.LOCAL_SCHEMA:
            try:
                ledger = TypedLedger(rows)
            except ValueError as exc:
                alerts.append(
                    Alert(
                        "typed_projection_rejected",
                        candidate_event_ids=self._candidate_ids_from_error(rows, str(exc)),
                        constraint_ids=frozenset({"typed_projection_integrity"}),
                        surface=ObserverSurface.LOCAL_SCHEMA,
                        detail=str(exc),
                    )
                )
        if surface >= ObserverSurface.SEMANTIC_JOURNAL and ledger is not None:
            alerts.extend(self._semantic_alerts(ledger))
        if surface >= ObserverSurface.EXTERNAL_COMMITMENT:
            alerts.extend(self._commitment_alerts(rows, journal_commitment))
        if surface >= ObserverSurface.PROJECTION_COMMITMENT:
            alerts.extend(
                self._projection_alerts(
                    journal_commitment,
                    projection_commitment,
                    tuple(projection_rows),
                )
            )
        return tuple(self._deduplicate(alerts))

    @staticmethod
    def _deduplicate(alerts: Iterable[Alert]) -> list[Alert]:
        output: list[Alert] = []
        seen: set[tuple[object, ...]] = set()
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
    def _duplicate_alerts(events: tuple[CommonEvent, ...]) -> list[Alert]:
        by_id: dict[str, str] = {}
        alerts: list[Alert] = []
        for event in events:
            digest = event_hash(event)
            prior = by_id.get(event.event_id)
            if prior is not None and prior != digest:
                alerts.append(
                    Alert(
                        "typed_duplicate_conflicting_event_id",
                        candidate_event_ids=frozenset({event.event_id}),
                        constraint_ids=frozenset({"typed_event_id_unique"}),
                        surface=ObserverSurface.BYTES,
                    )
                )
            by_id[event.event_id] = digest
        return alerts

    @staticmethod
    def _candidate_ids_from_error(
        events: tuple[CommonEvent, ...], message: str
    ) -> frozenset[str]:
        tokens = set(message.replace(":", " ").split())
        candidates = {
            event.event_id
            for event in events
            if event.event_id in tokens
            or (event.object_id is not None and event.object_id in tokens)
        }
        return frozenset(candidates)

    def _semantic_alerts(self, ledger: TypedLedger) -> list[Alert]:
        alerts: list[Alert] = []

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

        # Typed branch and lineage relations make cycle checks explicit.
        for branch_id in ledger.branches:
            cursor = branch_id
            seen: set[str] = set()
            while cursor is not None:
                if cursor in seen:
                    add("typed_world_branch_cycle", {branch_id}, "world_branch_acyclic")
                    break
                seen.add(cursor)
                branch = ledger.branches.get(cursor)
                cursor = branch.parent_world_branch_id if branch else None

        graph: dict[str, list[str]] = defaultdict(list)
        for edge in ledger.lineage:
            if edge.source_mind_instance_id:
                graph[edge.source_mind_instance_id].append(edge.destination_mind_instance_id)
        for start in graph:
            stack = [(start, frozenset())]
            while stack:
                node, path = stack.pop()
                if node in path:
                    add("typed_lineage_cycle", {start}, "lineage_acyclic")
                    break
                for child in graph.get(node, []):
                    stack.append((child, path | {node}))

        for edge in ledger.lineage:
            source = ledger.minds.get(edge.source_mind_instance_id or "")
            destination = ledger.minds.get(edge.destination_mind_instance_id)
            if source is None or destination is None:
                continue
            same = source.principal_id == destination.principal_id
            if edge.kind == "operational_replica" and not same:
                add(
                    "typed_operational_replica_principal_mismatch",
                    {edge.lineage_edge_id},
                    "operational_replica_same_principal",
                )
            if edge.kind == "identity_fork" and same:
                add(
                    "typed_identity_fork_principal_not_distinct",
                    {edge.lineage_edge_id},
                    "identity_fork_distinct_principal",
                )

        def authorization_active(auth_id: str | None, system_time: int) -> bool:
            if auth_id is None:
                return False
            candidates = sorted(
                (
                    row
                    for row in ledger.authorizations
                    if row.authorization_id == auth_id
                    and row.recorded_system_time <= system_time
                ),
                key=lambda row: (row.recorded_system_time, row.authorization_id),
            )
            return bool(candidates and candidates[-1].operation == "grant")

        acquired: set[tuple[str, str]] = set()
        for evidence in ledger.evidence.values():
            if evidence.actor_mind_instance_id:
                acquired.add((evidence.actor_mind_instance_id, evidence.evidence_id))

        for exposure in sorted(
            ledger.exposures,
            key=lambda row: (row.recorded_system_time, row.exposure_id),
        ):
            if exposure.operation == "state_replication":
                source = ledger.minds.get(exposure.source_mind_instance_id or "")
                destination = ledger.minds.get(exposure.destination_mind_instance_id)
                same = bool(source and destination and source.principal_id == destination.principal_id)
                edge_ok = any(
                    edge.source_mind_instance_id == exposure.source_mind_instance_id
                    and edge.destination_mind_instance_id
                    == exposure.destination_mind_instance_id
                    and edge.kind in {"operational_replica", "checkpoint_branch"}
                    and edge.created_system_time <= exposure.recorded_system_time
                    for edge in ledger.lineage
                )
                if not (
                    same
                    and edge_ok
                    and authorization_active(
                        exposure.authorization_id, exposure.recorded_system_time
                    )
                ):
                    add(
                        "typed_invalid_state_replication",
                        {exposure.exposure_id},
                        "state_replication_authorized",
                    )
                    continue
            if (
                exposure.source_mind_instance_id
                and (
                    exposure.source_mind_instance_id,
                    exposure.object_id,
                )
                not in acquired
            ):
                add(
                    "typed_source_not_exposed",
                    {exposure.exposure_id},
                    "transfer_source_exposed",
                )
                continue
            if exposure.operation != "forget_active":
                acquired.add(
                    (exposure.destination_mind_instance_id, exposure.object_id)
                )

        cutoff_by_snapshot = {
            edge.snapshot_id: edge.cutoff_system_time
            for edge in ledger.lineage
            if edge.snapshot_id and edge.cutoff_system_time is not None
        }
        for member in ledger.snapshot_manifest:
            if member.object_kind != "evidence":
                continue
            evidence = ledger.evidence.get(member.object_id)
            cutoff = cutoff_by_snapshot.get(member.snapshot_id)
            if evidence and cutoff is not None and evidence.recorded_system_time > cutoff:
                add(
                    "typed_snapshot_member_post_cutoff",
                    {member.manifest_entry_id, evidence.evidence_id},
                    "snapshot_member_before_cutoff",
                )

        # Typed justification rows are order-independent after projection.
        for support in ledger.justifications:
            members = [ledger.evidence.get(member) for member in support.members]
            if any(member is None for member in members):
                continue
            families = {member.origin_family_id for member in members if member}
            if len(families) < support.min_independent_sources:
                add(
                    "typed_non_independent_support",
                    {support.justification_id, *support.members},
                    "minimum_independent_sources",
                )

        # Provenance fields not represented in the current typed rows are still
        # checked from the canonical source events to avoid order-dependent loss.
        common_by_object = {
            event.object_id: event
            for event in ledger.common_events
            if event.event_type == "evidence" and event.object_id
        }
        policies = [
            event for event in ledger.common_events if event.event_type == "policy"
        ]
        for child_id, child in common_by_object.items():
            attrs = dict(child.attributes)
            parent_id = attrs.get("derived_from") or child.raw_evidence_ref
            if not parent_id:
                continue
            parent = common_by_object.get(parent_id)
            if parent is None:
                add(
                    "typed_derived_evidence_missing_parent",
                    {child.event_id},
                    "derivation_parent_exists",
                )
                continue
            declassified = any(
                policy.object_id == parent_id
                and policy.policy_operation == "declassify"
                and policy.system_time <= child.system_time
                for policy in policies
            )
            if (
                parent.policy_label not in {None, "public"}
                and child.policy_label == "public"
                and not declassified
            ):
                add(
                    "typed_policy_laundering",
                    {child.event_id, parent.event_id},
                    "derived_policy_not_weaker",
                )
            if child.source_family_id != parent.source_family_id:
                add(
                    "typed_origin_family_laundering",
                    {child.event_id, parent.event_id},
                    "derived_origin_family_preserved",
                )

        return alerts

    @staticmethod
    def _commitment_alerts(
        events: tuple[CommonEvent, ...],
        commitment: JournalCommitment | None,
    ) -> list[Alert]:
        if commitment is None:
            return [
                Alert(
                    "typed_missing_external_journal_commitment",
                    constraint_ids=frozenset({"journal_commitment_required"}),
                    surface=ObserverSurface.EXTERNAL_COMMITMENT,
                )
            ]
        alerts: list[Alert] = []
        actual_ids = tuple(event.event_id for event in events)
        expected_hashes = dict(commitment.event_hashes)
        if actual_ids != commitment.ordered_event_ids:
            alerts.append(
                Alert(
                    "typed_journal_sequence_or_membership_mismatch",
                    candidate_event_ids=frozenset(
                        set(actual_ids) ^ set(commitment.ordered_event_ids)
                    ),
                    constraint_ids=frozenset({"journal_sequence_committed"}),
                    surface=ObserverSurface.EXTERNAL_COMMITMENT,
                )
            )
        for event in events:
            expected = expected_hashes.get(event.event_id)
            if expected is not None and event_hash(event) != expected:
                alerts.append(
                    Alert(
                        "typed_journal_event_hash_mismatch",
                        candidate_event_ids=frozenset({event.event_id}),
                        constraint_ids=frozenset({"journal_event_hash_committed"}),
                        surface=ObserverSurface.EXTERNAL_COMMITMENT,
                    )
                )
        if journal_head(events, commitment.previous_head_hash) != commitment.head_hash:
            alerts.append(
                Alert(
                    "typed_journal_head_mismatch",
                    constraint_ids=frozenset({"journal_head_committed"}),
                    surface=ObserverSurface.EXTERNAL_COMMITMENT,
                )
            )
        return alerts

    @staticmethod
    def _projection_alerts(
        journal_commitment: JournalCommitment | None,
        projection_commitment: ProjectionCommitment | None,
        rows: tuple[tuple[str, str], ...],
    ) -> list[Alert]:
        if journal_commitment is None or projection_commitment is None:
            return [
                Alert(
                    "typed_missing_projection_commitment",
                    constraint_ids=frozenset({"projection_commitment_required"}),
                    surface=ObserverSurface.PROJECTION_COMMITMENT,
                )
            ]
        alerts: list[Alert] = []
        if projection_commitment.journal_head_hash != journal_commitment.head_hash:
            alerts.append(
                Alert(
                    "typed_projection_bound_to_wrong_journal_head",
                    constraint_ids=frozenset({"projection_journal_head_binding"}),
                    surface=ObserverSurface.PROJECTION_COMMITMENT,
                )
            )
        if projection_hash(rows) != projection_commitment.projection_hash:
            alerts.append(
                Alert(
                    "typed_projection_content_mismatch",
                    constraint_ids=frozenset({"projection_content_committed"}),
                    surface=ObserverSurface.PROJECTION_COMMITMENT,
                )
            )
        return alerts
