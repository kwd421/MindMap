from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from .v02_model import (
    ACQUISITION_OPERATIONS,
    ATTRIBUTION_PRECEDENCE,
    Answer,
    CommonEvent,
    EventType,
    Query,
    QueryTarget,
    policy_allows,
    validate_event_log,
)


@dataclass(frozen=True, slots=True)
class _Lineage:
    source: str
    destination: str
    kind: str
    cutoff: int
    system_time: int
    authorization_id: str | None
    authorized: bool


@dataclass(frozen=True, slots=True)
class _Exposure:
    destination: str
    evidence: str
    operation: str
    system_time: int
    source: str | None
    authorization_id: str | None
    authorized: bool
    attribution_kind: str | None


@dataclass(frozen=True, slots=True)
class _Policy:
    object_id: str
    operation: str
    system_time: int
    target_mind: str | None
    policy_label: str | None


class TypedV02Ledger:
    """Typed v0.2 projection over the same CommonEventLog as the generic ledger."""

    def __init__(self, events: Iterable[CommonEvent]):
        ordered = sorted(
            validate_event_log(events), key=lambda item: (item.system_time, item.event_id)
        )
        self.mind_principals: dict[str, str] = {}
        self.world_facts: defaultdict[tuple[str, str], list[CommonEvent]] = defaultdict(list)
        self.evidence: defaultdict[str, list[CommonEvent]] = defaultdict(list)
        self.evidence_by_proposition: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
        self.exposures: defaultdict[tuple[str, str], list[_Exposure]] = defaultdict(list)
        self.lineage: defaultdict[str, list[_Lineage]] = defaultdict(list)
        self.attitudes: defaultdict[tuple[str, str, str], list[CommonEvent]] = defaultdict(list)
        self.policies: defaultdict[str, list[_Policy]] = defaultdict(list)
        self.justifications: defaultdict[tuple[str, str], list[CommonEvent]] = defaultdict(list)

        for event in ordered:
            match event.event_type:
                case EventType.MIND_CREATED:
                    assert event.destination_mind_instance_id is not None
                    assert event.actor_principal_id is not None
                    self.mind_principals[event.destination_mind_instance_id] = event.actor_principal_id
                case EventType.WORLD_FACT:
                    assert event.proposition_id is not None
                    assert event.world_branch_id is not None
                    self.world_facts[(event.proposition_id, event.world_branch_id)].append(event)
                case EventType.EVIDENCE:
                    assert event.object_id is not None
                    assert event.proposition_id is not None
                    self.evidence[event.object_id].append(event)
                    if event.about_world_branch_id:
                        self.evidence_by_proposition[(event.proposition_id, event.about_world_branch_id)].add(event.object_id)
                case EventType.EXPOSURE:
                    assert event.destination_mind_instance_id is not None
                    assert event.object_id is not None
                    assert event.operation is not None
                    self.exposures[(event.destination_mind_instance_id, event.object_id)].append(
                        _Exposure(
                            destination=event.destination_mind_instance_id,
                            evidence=event.object_id,
                            operation=event.operation,
                            system_time=event.system_time,
                            source=event.source_mind_instance_id,
                            authorization_id=event.authorization_id,
                            authorized=event.authorized is True,
                            attribution_kind=event.attribution_kind,
                        )
                    )
                case EventType.LINEAGE:
                    assert event.source_mind_instance_id is not None
                    assert event.destination_mind_instance_id is not None
                    assert event.lineage_kind is not None
                    cutoff = event.snapshot_cutoff if event.snapshot_cutoff is not None else event.system_time
                    self.lineage[event.destination_mind_instance_id].append(
                        _Lineage(
                            source=event.source_mind_instance_id,
                            destination=event.destination_mind_instance_id,
                            kind=event.lineage_kind,
                            cutoff=cutoff,
                            system_time=event.system_time,
                            authorization_id=event.authorization_id,
                            authorized=event.authorized is True,
                        )
                    )
                case EventType.ATTITUDE:
                    assert event.destination_mind_instance_id is not None
                    assert event.proposition_id is not None
                    assert event.about_world_branch_id is not None
                    self.attitudes[(event.destination_mind_instance_id, event.proposition_id, event.about_world_branch_id)].append(event)
                case EventType.POLICY:
                    assert event.object_id is not None
                    assert event.operation is not None
                    self.policies[event.object_id].append(
                        _Policy(
                            object_id=event.object_id,
                            operation=event.operation,
                            system_time=event.system_time,
                            target_mind=event.destination_mind_instance_id,
                            policy_label=event.policy_label,
                        )
                    )
                case EventType.JUSTIFICATION:
                    assert event.proposition_id is not None
                    assert event.about_world_branch_id is not None
                    self.justifications[(event.proposition_id, event.about_world_branch_id)].append(event)

    def answer(self, query: Query) -> Answer:
        match query.target:
            case QueryTarget.WORLD:
                value = self._world(query)
            case QueryTarget.EVER_EXPOSED:
                value = self._ever_exposed(
                    self._need(query.mind_instance_id, "mind_instance_id"),
                    self._need(query.evidence_id, "evidence_id"),
                    query.system_time,
                    set(),
                )
            case QueryTarget.AVAILABLE:
                value = self._available(query)
            case QueryTarget.ATTITUDE:
                value = self._attitude(query)
            case QueryTarget.ATTRIBUTION:
                value = self._attribution(query)
            case QueryTarget.DISCLOSE:
                value = bool(self._justification_ids(query))
            case QueryTarget.JUSTIFICATION:
                value = self._justification_ids(query)
            case _:
                raise ValueError(f"unsupported target: {query.target}")
        return Answer(query.target, value)

    @staticmethod
    def _need(value: str | None, field: str) -> str:
        if value is None:
            raise ValueError(f"query requires {field}")
        return value

    def _world(self, query: Query) -> bool | None:
        proposition = self._need(query.proposition_id, "proposition_id")
        branch = self._need(query.world_branch_id, "world_branch_id")
        value: bool | None = None
        for event in self.world_facts[(proposition, branch)]:
            if event.system_time <= query.system_time and event.valid_at(query.valid_time):
                value = event.truth_value
        return value

    def _copy_eligible(self, edge: _Lineage, system_time: int) -> bool:
        if edge.kind == "restore":
            return True
        if edge.kind not in {"operational_replica", "checkpoint_branch"}:
            return False
        return (
            edge.authorized
            and edge.authorization_id is not None
            and self.mind_principals.get(edge.source) == self.mind_principals.get(edge.destination)
            and edge.system_time <= system_time
        )

    def _ever_exposed(self, mind: str, evidence: str, system_time: int, visited: set[tuple[str, str, int]]) -> bool:
        marker = (mind, evidence, system_time)
        if marker in visited:
            return False
        visited.add(marker)
        if any(
            exposure.system_time <= system_time and exposure.operation in ACQUISITION_OPERATIONS
            for exposure in self.exposures[(mind, evidence)]
        ):
            return True
        for edge in self.lineage[mind]:
            if edge.system_time > system_time or not self._copy_eligible(edge, system_time):
                continue
            if self._ever_exposed(edge.source, evidence, edge.cutoff, visited):
                return True
        return False

    def _available(self, query: Query) -> bool:
        mind = self._need(query.mind_instance_id, "mind_instance_id")
        evidence = self._need(query.evidence_id, "evidence_id")
        if not self._ever_exposed(mind, evidence, query.system_time, set()):
            return False
        retained = True
        for exposure in self.exposures[(mind, evidence)]:
            if exposure.system_time > query.system_time:
                continue
            if exposure.operation == "forget_active":
                retained = False
            elif exposure.operation in ACQUISITION_OPERATIONS:
                retained = True
        if not retained:
            return False
        self_access = True
        for policy in self.policies[evidence]:
            if policy.system_time > query.system_time or policy.target_mind not in {None, mind}:
                continue
            if policy.operation in {"self_seal", "revoke", "evidence_delete", "quarantine"}:
                self_access = False
            elif policy.operation in {"self_unseal", "grant", "reacquire"}:
                self_access = True
        return self_access

    def _attitude(self, query: Query) -> str | None:
        key = (
            self._need(query.mind_instance_id, "mind_instance_id"),
            self._need(query.proposition_id, "proposition_id"),
            self._need(query.world_branch_id, "world_branch_id"),
        )
        value: str | None = None
        for event in self.attitudes[key]:
            if event.system_time <= query.system_time and event.valid_at(query.valid_time):
                value = event.stance
        return value

    def _exposure_attributions(self, mind: str, evidence: str, system_time: int) -> list[str]:
        values: list[str] = []
        for exposure in self.exposures[(mind, evidence)]:
            if exposure.system_time > system_time:
                continue
            match exposure.operation:
                case "observe":
                    values.append("direct_observation")
                case "restore":
                    values.append("same_principal_snapshot_inheritance")
                case "state_replication":
                    same_principal = bool(exposure.source) and self.mind_principals.get(exposure.source) == self.mind_principals.get(mind)
                    if exposure.authorized and exposure.authorization_id and same_principal:
                        values.append("same_principal_state_replication")
                    else:
                        values.append("evidence_copy")
                case "evidence_copy":
                    values.append("evidence_copy")
                case "receive" | "read":
                    values.append(exposure.attribution_kind or "attributed_report")
                case "reacquire":
                    values.append(exposure.attribution_kind or "reconstruction")
        return values

    def _attribution(self, query: Query) -> str:
        mind = self._need(query.mind_instance_id, "mind_instance_id")
        proposition = self._need(query.proposition_id, "proposition_id")
        branch = self._need(query.world_branch_id, "world_branch_id")
        values: list[str] = []
        for evidence in self.evidence_by_proposition[(proposition, branch)]:
            values.extend(self._exposure_attributions(mind, evidence, query.system_time))
            for edge in self.lineage[mind]:
                if edge.system_time > query.system_time or not self._copy_eligible(edge, query.system_time):
                    continue
                if not self._ever_exposed(edge.source, evidence, edge.cutoff, set()):
                    continue
                values.append(
                    "same_principal_snapshot_inheritance"
                    if edge.kind == "restore"
                    else "same_principal_state_replication"
                )
        if not values:
            return "unknown"
        return max(values, key=ATTRIBUTION_PRECEDENCE.__getitem__)

    def _evidence_at(self, evidence: str, system_time: int) -> CommonEvent | None:
        value: CommonEvent | None = None
        for event in self.evidence[evidence]:
            if event.system_time <= system_time:
                value = event
        return value

    def _policy_label(self, evidence: str, system_time: int) -> str | None:
        base = self._evidence_at(evidence, system_time)
        label = base.policy_label if base else None
        for policy in self.policies[evidence]:
            if policy.system_time > system_time:
                continue
            if policy.operation == "revoke":
                label = "revoked"
            elif policy.operation == "evidence_delete":
                label = "deleted"
            elif policy.operation == "quarantine":
                label = "quarantined"
            elif policy.operation in {"grant", "declassify"}:
                label = policy.policy_label
        return label

    def _justification_ids(self, query: Query) -> tuple[str, ...]:
        proposition = self._need(query.proposition_id, "proposition_id")
        branch = self._need(query.world_branch_id, "world_branch_id")
        requester = self._need(query.requester_id, "requester_id")
        accepted: set[str] = set()
        for support in self.justifications[(proposition, branch)]:
            if support.system_time > query.system_time or not support.valid_at(query.valid_time):
                continue
            if support.operation in {"revoke", "invalidate", "delete"}:
                continue
            families: set[str] = set()
            for evidence_id in support.support_member_ids:
                evidence = self._evidence_at(evidence_id, query.system_time)
                if evidence is None:
                    break
                if not policy_allows(self._policy_label(evidence_id, query.system_time), requester):
                    break
                if evidence.source_family_id:
                    families.add(evidence.source_family_id)
            else:
                if len(families) >= support.required_independent_sources and support.support_set_id:
                    accepted.add(support.support_set_id)
        return tuple(sorted(accepted))
