from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable

from .v02_model import (
    ACQUISITION_OPERATIONS,
    ATTRIBUTION_PRECEDENCE,
    Answer,
    CommonEvent,
    Query,
    QueryTarget,
    policy_allows,
    validate_event_log,
)


class GenericEventLedger:
    """Complete equal-information generic event relation.

    The implementation intentionally keeps one generic row shape and derives all
    target states at read time. It does not import the typed projector or gold
    interpreter.
    """

    def __init__(self, events: Iterable[CommonEvent]):
        checked = validate_event_log(events)
        self.rows: tuple[dict[str, Any], ...] = tuple(
            sorted(
                (self._normalize(asdict(event)) for event in checked),
                key=lambda row: (row["system_time"], row["event_id"]),
            )
        )

    @staticmethod
    def _normalize(row: dict[str, Any]) -> dict[str, Any]:
        event_type = row["event_type"]
        row["event_type"] = event_type.value if hasattr(event_type, "value") else str(event_type)
        return row

    def answer(self, query: Query) -> Answer:
        handlers = {
            QueryTarget.WORLD: self._answer_world,
            QueryTarget.EVER_EXPOSED: self._answer_exposed,
            QueryTarget.AVAILABLE: self._answer_available,
            QueryTarget.ATTITUDE: self._answer_attitude,
            QueryTarget.ATTRIBUTION: self._answer_attribution,
            QueryTarget.DISCLOSE: self._answer_disclose,
            QueryTarget.JUSTIFICATION: self._answer_justification,
        }
        return Answer(query.target, handlers[query.target](query))

    @staticmethod
    def _need(value: str | None, field: str) -> str:
        if value is None:
            raise ValueError(f"query requires {field}")
        return value

    @staticmethod
    def _row_valid(row: dict[str, Any], valid_time: int) -> bool:
        return row["valid_from"] <= valid_time and (
            row["valid_to"] is None or valid_time < row["valid_to"]
        )

    def _rows(self, event_type: str, system_time: int) -> list[dict[str, Any]]:
        return [
            row
            for row in self.rows
            if row["event_type"] == event_type and row["system_time"] <= system_time
        ]

    def _principal_of(self, mind: str, system_time: int) -> str | None:
        principal: str | None = None
        for row in self._rows("mind_created", system_time):
            if row["destination_mind_instance_id"] == mind:
                principal = row["actor_principal_id"]
        return principal

    def _answer_world(self, query: Query) -> bool | None:
        proposition = self._need(query.proposition_id, "proposition_id")
        branch = self._need(query.world_branch_id, "world_branch_id")
        result: bool | None = None
        for row in self._rows("world_fact", query.system_time):
            if row["proposition_id"] != proposition:
                continue
            if row["world_branch_id"] != branch:
                continue
            if self._row_valid(row, query.valid_time):
                result = row["truth_value"]
        return result

    def _copy_edges(self, destination: str, system_time: int) -> list[dict[str, Any]]:
        edges: list[dict[str, Any]] = []
        for row in self._rows("lineage", system_time):
            if row["destination_mind_instance_id"] != destination:
                continue
            kind = row["lineage_kind"]
            if kind == "restore":
                edges.append(row)
                continue
            if kind not in {"operational_replica", "checkpoint_branch"}:
                continue
            source = row["source_mind_instance_id"]
            if not source:
                continue
            if row["authorized"] is not True or not row["authorization_id"]:
                continue
            if self._principal_of(source, system_time) != self._principal_of(
                destination, system_time
            ):
                continue
            edges.append(row)
        return edges

    def _has_exposure(
        self,
        mind: str,
        evidence: str,
        system_time: int,
        seen: set[tuple[str, str, int]] | None = None,
    ) -> bool:
        seen = set() if seen is None else seen
        token = (mind, evidence, system_time)
        if token in seen:
            return False
        seen.add(token)

        for row in self._rows("exposure", system_time):
            if row["destination_mind_instance_id"] != mind:
                continue
            if row["object_id"] == evidence and row["operation"] in ACQUISITION_OPERATIONS:
                return True

        for edge in self._copy_edges(mind, system_time):
            source = edge["source_mind_instance_id"]
            cutoff = edge["snapshot_cutoff"]
            if cutoff is None:
                cutoff = edge["system_time"]
            if source and self._has_exposure(source, evidence, cutoff, seen):
                return True
        return False

    def _answer_exposed(self, query: Query) -> bool:
        return self._has_exposure(
            self._need(query.mind_instance_id, "mind_instance_id"),
            self._need(query.evidence_id, "evidence_id"),
            query.system_time,
        )

    def _answer_available(self, query: Query) -> bool:
        mind = self._need(query.mind_instance_id, "mind_instance_id")
        evidence = self._need(query.evidence_id, "evidence_id")
        if not self._has_exposure(mind, evidence, query.system_time):
            return False

        retained = True
        for row in self._rows("exposure", query.system_time):
            if row["destination_mind_instance_id"] != mind or row["object_id"] != evidence:
                continue
            if row["operation"] == "forget_active":
                retained = False
            elif row["operation"] in ACQUISITION_OPERATIONS:
                retained = True
        if not retained:
            return False

        allowed = True
        for row in self._rows("policy", query.system_time):
            if row["object_id"] != evidence:
                continue
            target = row["destination_mind_instance_id"]
            if target not in {None, mind}:
                continue
            op = row["operation"]
            if op in {"self_seal", "revoke", "evidence_delete", "quarantine"}:
                allowed = False
            elif op in {"self_unseal", "grant", "reacquire"}:
                allowed = True
        return allowed

    def _answer_attitude(self, query: Query) -> str | None:
        mind = self._need(query.mind_instance_id, "mind_instance_id")
        proposition = self._need(query.proposition_id, "proposition_id")
        branch = self._need(query.world_branch_id, "world_branch_id")
        value: str | None = None
        for row in self._rows("attitude", query.system_time):
            if row["destination_mind_instance_id"] != mind:
                continue
            if row["proposition_id"] != proposition:
                continue
            if row["about_world_branch_id"] != branch:
                continue
            if self._row_valid(row, query.valid_time):
                value = row["stance"]
        return value

    def _direct_attribution_values(
        self, mind: str, evidence: str, system_time: int
    ) -> list[str]:
        values: list[str] = []
        for row in self._rows("exposure", system_time):
            if row["destination_mind_instance_id"] != mind or row["object_id"] != evidence:
                continue
            operation = row["operation"]
            if operation not in ACQUISITION_OPERATIONS:
                continue
            match operation:
                case "observe":
                    values.append("direct_observation")
                case "restore":
                    values.append("same_principal_snapshot_inheritance")
                case "state_replication":
                    source = row["source_mind_instance_id"]
                    same_principal = bool(source) and self._principal_of(
                        source, system_time
                    ) == self._principal_of(mind, system_time)
                    if row["authorized"] and row["authorization_id"] and same_principal:
                        values.append("same_principal_state_replication")
                    else:
                        values.append("evidence_copy")
                case "evidence_copy":
                    values.append("evidence_copy")
                case "receive" | "read":
                    values.append(row["attribution_kind"] or "attributed_report")
                case "reacquire":
                    values.append(row["attribution_kind"] or "reconstruction")
        return values

    def _evidence_attribution(
        self,
        mind: str,
        evidence: str,
        system_time: int,
        seen: set[tuple[str, str, int]] | None = None,
    ) -> list[str]:
        seen = set() if seen is None else seen
        token = (mind, evidence, system_time)
        if token in seen:
            return []
        seen.add(token)
        values = self._direct_attribution_values(mind, evidence, system_time)
        for edge in self._copy_edges(mind, system_time):
            source = edge["source_mind_instance_id"]
            cutoff = edge["snapshot_cutoff"]
            if cutoff is None:
                cutoff = edge["system_time"]
            if source and self._has_exposure(source, evidence, cutoff):
                if edge["lineage_kind"] == "restore":
                    values.append("same_principal_snapshot_inheritance")
                else:
                    values.append("same_principal_state_replication")
        return values

    def _answer_attribution(self, query: Query) -> str:
        mind = self._need(query.mind_instance_id, "mind_instance_id")
        proposition = self._need(query.proposition_id, "proposition_id")
        branch = self._need(query.world_branch_id, "world_branch_id")
        evidence_ids = {
            row["object_id"]
            for row in self._rows("evidence", query.system_time)
            if row["proposition_id"] == proposition
            and row["about_world_branch_id"] == branch
            and row["object_id"]
        }
        values: list[str] = []
        for evidence in evidence_ids:
            values.extend(self._evidence_attribution(mind, evidence, query.system_time))
        if not values:
            return "unknown"
        return max(values, key=ATTRIBUTION_PRECEDENCE.__getitem__)

    def _evidence_row(self, evidence: str, system_time: int) -> dict[str, Any] | None:
        value: dict[str, Any] | None = None
        for row in self._rows("evidence", system_time):
            if row["object_id"] == evidence:
                value = row
        return value

    def _disclosure_label(self, evidence: str, system_time: int) -> str | None:
        base = self._evidence_row(evidence, system_time)
        label = base["policy_label"] if base else None
        for row in self._rows("policy", system_time):
            if row["object_id"] != evidence:
                continue
            match row["operation"]:
                case "revoke":
                    label = "revoked"
                case "evidence_delete":
                    label = "deleted"
                case "quarantine":
                    label = "quarantined"
                case "grant" | "declassify":
                    label = row["policy_label"]
        return label

    def _justifications(self, query: Query) -> tuple[str, ...]:
        proposition = self._need(query.proposition_id, "proposition_id")
        requester = self._need(query.requester_id, "requester_id")
        branch = self._need(query.world_branch_id, "world_branch_id")
        accepted: set[str] = set()

        for row in self._rows("justification", query.system_time):
            if row["proposition_id"] != proposition:
                continue
            if row["about_world_branch_id"] != branch:
                continue
            if not self._row_valid(row, query.valid_time):
                continue
            if row["operation"] in {"revoke", "invalidate", "delete"}:
                continue

            families: set[str] = set()
            admissible = True
            for evidence in row["support_member_ids"]:
                evidence_row = self._evidence_row(evidence, query.system_time)
                if evidence_row is None:
                    admissible = False
                    break
                if not policy_allows(
                    self._disclosure_label(evidence, query.system_time), requester
                ):
                    admissible = False
                    break
                family = evidence_row["source_family_id"]
                if family:
                    families.add(family)
            if admissible and len(families) >= row["required_independent_sources"]:
                support_id = row["support_set_id"]
                if support_id:
                    accepted.add(support_id)
        return tuple(sorted(accepted))

    def _answer_disclose(self, query: Query) -> bool:
        return bool(self._justifications(query))

    def _answer_justification(self, query: Query) -> tuple[str, ...]:
        return self._justifications(query)
