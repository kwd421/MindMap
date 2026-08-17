from __future__ import annotations

from collections.abc import Iterable

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


class DeclarativeGold:
    """Independent declarative interpreter for the S-track fixtures.

    This module imports only the common event/query data contract. It does not
    import either implementation under comparison.
    """

    def __init__(self, events: Iterable[CommonEvent]):
        self.events = tuple(
            sorted(validate_event_log(events), key=lambda item: (item.system_time, item.event_id))
        )

    def answer(self, query: Query) -> Answer:
        match query.target:
            case QueryTarget.WORLD:
                value = self._world(query)
            case QueryTarget.EVER_EXPOSED:
                value = self._ever_exposed(
                    self._required(query.mind_instance_id, "mind_instance_id"),
                    self._required(query.evidence_id, "evidence_id"),
                    query.system_time,
                    frozenset(),
                )
            case QueryTarget.AVAILABLE:
                value = self._available(
                    self._required(query.mind_instance_id, "mind_instance_id"),
                    self._required(query.evidence_id, "evidence_id"),
                    query.system_time,
                )
            case QueryTarget.ATTITUDE:
                value = self._attitude(query)
            case QueryTarget.ATTRIBUTION:
                value = self._attribution(query)
            case QueryTarget.DISCLOSE:
                value = bool(self._admissible_justifications(query))
            case QueryTarget.JUSTIFICATION:
                value = self._admissible_justifications(query)
            case _:
                raise ValueError(f"unsupported target: {query.target}")
        return Answer(query.target, value)

    @staticmethod
    def _required(value: str | None, field_name: str) -> str:
        if value is None:
            raise ValueError(f"query requires {field_name}")
        return value

    def _visible(self, event: CommonEvent, system_time: int) -> bool:
        return event.system_time <= system_time

    def _mind_principal(self, mind_instance_id: str, system_time: int) -> str | None:
        candidates = [
            event
            for event in self.events
            if event.event_type is EventType.MIND_CREATED
            and event.destination_mind_instance_id == mind_instance_id
            and self._visible(event, system_time)
        ]
        if not candidates:
            return None
        return candidates[-1].actor_principal_id

    def _world(self, query: Query) -> bool | None:
        proposition = self._required(query.proposition_id, "proposition_id")
        branch = self._required(query.world_branch_id, "world_branch_id")
        candidates = [
            event
            for event in self.events
            if event.event_type is EventType.WORLD_FACT
            and event.proposition_id == proposition
            and event.world_branch_id == branch
            and self._visible(event, query.system_time)
            and event.valid_at(query.valid_time)
        ]
        if not candidates:
            return None
        return candidates[-1].truth_value

    def _lineage_events(self, destination: str, system_time: int) -> list[CommonEvent]:
        return [
            event
            for event in self.events
            if event.event_type is EventType.LINEAGE
            and event.destination_mind_instance_id == destination
            and self._visible(event, system_time)
        ]

    def _lineage_copy_allowed(self, event: CommonEvent, system_time: int) -> bool:
        if event.lineage_kind not in {"restore", "operational_replica", "checkpoint_branch"}:
            return False
        if event.lineage_kind in {"operational_replica", "checkpoint_branch"}:
            if event.authorized is not True or not event.authorization_id:
                return False
            source = self._required(event.source_mind_instance_id, "source_mind_instance_id")
            destination = self._required(
                event.destination_mind_instance_id, "destination_mind_instance_id"
            )
            if self._mind_principal(source, system_time) != self._mind_principal(
                destination, system_time
            ):
                return False
        return True

    def _ever_exposed(
        self,
        mind_instance_id: str,
        evidence_id: str,
        system_time: int,
        visited: frozenset[tuple[str, str, int]],
    ) -> bool:
        key = (mind_instance_id, evidence_id, system_time)
        if key in visited:
            return False
        visited = visited | {key}

        if any(
            event.event_type is EventType.EXPOSURE
            and event.destination_mind_instance_id == mind_instance_id
            and event.object_id == evidence_id
            and event.operation in ACQUISITION_OPERATIONS
            and self._visible(event, system_time)
            for event in self.events
        ):
            return True

        for lineage in self._lineage_events(mind_instance_id, system_time):
            if not self._lineage_copy_allowed(lineage, system_time):
                continue
            source = self._required(lineage.source_mind_instance_id, "source_mind_instance_id")
            cutoff = lineage.snapshot_cutoff
            if cutoff is None:
                cutoff = lineage.system_time
            if self._ever_exposed(source, evidence_id, cutoff, visited):
                return True
        return False

    def _available(self, mind_instance_id: str, evidence_id: str, system_time: int) -> bool:
        if not self._ever_exposed(mind_instance_id, evidence_id, system_time, frozenset()):
            return False

        retained = True
        for event in self.events:
            if not self._visible(event, system_time):
                break
            if event.event_type is EventType.EXPOSURE:
                if event.destination_mind_instance_id != mind_instance_id:
                    continue
                if event.object_id != evidence_id:
                    continue
                if event.operation == "forget_active":
                    retained = False
                elif event.operation in ACQUISITION_OPERATIONS:
                    retained = True

        if not retained:
            return False

        self_access = True
        for event in self.events:
            if not self._visible(event, system_time):
                break
            if event.event_type is not EventType.POLICY or event.object_id != evidence_id:
                continue
            if event.destination_mind_instance_id not in {None, mind_instance_id}:
                continue
            if event.operation in {"self_seal", "revoke", "evidence_delete", "quarantine"}:
                self_access = False
            elif event.operation in {"self_unseal", "grant", "reacquire"}:
                self_access = True
        return self_access

    def _attitude(self, query: Query) -> str | None:
        mind = self._required(query.mind_instance_id, "mind_instance_id")
        proposition = self._required(query.proposition_id, "proposition_id")
        branch = self._required(query.world_branch_id, "world_branch_id")
        candidates = [
            event
            for event in self.events
            if event.event_type is EventType.ATTITUDE
            and event.destination_mind_instance_id == mind
            and event.proposition_id == proposition
            and event.about_world_branch_id == branch
            and self._visible(event, query.system_time)
            and event.valid_at(query.valid_time)
        ]
        if not candidates:
            return None
        return candidates[-1].stance

    def _explicit_attributions(
        self, mind_instance_id: str, evidence_id: str, system_time: int
    ) -> list[str]:
        values: list[str] = []
        for event in self.events:
            if not self._visible(event, system_time):
                break
            if event.event_type is not EventType.EXPOSURE:
                continue
            if event.destination_mind_instance_id != mind_instance_id:
                continue
            if event.object_id != evidence_id:
                continue
            if event.operation not in ACQUISITION_OPERATIONS:
                continue
            if event.operation == "observe":
                values.append("direct_observation")
            elif event.operation == "state_replication":
                if event.authorized and event.authorization_id:
                    source = event.source_mind_instance_id
                    if source and self._mind_principal(source, system_time) == self._mind_principal(
                        mind_instance_id, system_time
                    ):
                        values.append("same_principal_state_replication")
                    else:
                        values.append("evidence_copy")
                else:
                    values.append("evidence_copy")
            elif event.operation == "restore":
                values.append("same_principal_snapshot_inheritance")
            elif event.operation == "evidence_copy":
                values.append("evidence_copy")
            elif event.operation in {"receive", "read"}:
                values.append(event.attribution_kind or "attributed_report")
            elif event.operation == "reacquire":
                values.append(event.attribution_kind or "reconstruction")
        return values

    def _attributions_for_evidence(
        self,
        mind_instance_id: str,
        evidence_id: str,
        system_time: int,
        visited: frozenset[tuple[str, str, int]],
    ) -> list[str]:
        key = (mind_instance_id, evidence_id, system_time)
        if key in visited:
            return []
        visited = visited | {key}

        values = self._explicit_attributions(mind_instance_id, evidence_id, system_time)
        for lineage in self._lineage_events(mind_instance_id, system_time):
            if not self._lineage_copy_allowed(lineage, system_time):
                continue
            source = self._required(lineage.source_mind_instance_id, "source_mind_instance_id")
            cutoff = lineage.snapshot_cutoff
            if cutoff is None:
                cutoff = lineage.system_time
            if not self._ever_exposed(source, evidence_id, cutoff, frozenset()):
                continue
            if lineage.lineage_kind == "restore":
                values.append("same_principal_snapshot_inheritance")
            else:
                values.append("same_principal_state_replication")
        return values

    def _attribution(self, query: Query) -> str:
        mind = self._required(query.mind_instance_id, "mind_instance_id")
        proposition = self._required(query.proposition_id, "proposition_id")
        branch = self._required(query.world_branch_id, "world_branch_id")

        evidence_ids = [
            event.object_id
            for event in self.events
            if event.event_type is EventType.EVIDENCE
            and event.proposition_id == proposition
            and event.about_world_branch_id == branch
            and self._visible(event, query.system_time)
            and event.object_id is not None
        ]
        values: list[str] = []
        for evidence_id in evidence_ids:
            values.extend(
                self._attributions_for_evidence(
                    mind, evidence_id, query.system_time, frozenset()
                )
            )
        if not values:
            return "unknown"
        return max(values, key=lambda value: ATTRIBUTION_PRECEDENCE[value])

    def _evidence_event(self, evidence_id: str, system_time: int) -> CommonEvent | None:
        candidates = [
            event
            for event in self.events
            if event.event_type is EventType.EVIDENCE
            and event.object_id == evidence_id
            and self._visible(event, system_time)
        ]
        return candidates[-1] if candidates else None

    def _policy_label(self, evidence_id: str, system_time: int) -> str | None:
        evidence = self._evidence_event(evidence_id, system_time)
        label = evidence.policy_label if evidence else None
        for event in self.events:
            if not self._visible(event, system_time):
                break
            if event.event_type is not EventType.POLICY or event.object_id != evidence_id:
                continue
            if event.operation in {"revoke", "evidence_delete", "quarantine"}:
                label = {
                    "revoke": "revoked",
                    "evidence_delete": "deleted",
                    "quarantine": "quarantined",
                }[event.operation]
            elif event.operation in {"grant", "declassify"}:
                label = event.policy_label
        return label

    def _admissible_justifications(self, query: Query) -> tuple[str, ...]:
        proposition = self._required(query.proposition_id, "proposition_id")
        requester = self._required(query.requester_id, "requester_id")
        branch = self._required(query.world_branch_id, "world_branch_id")
        accepted: list[str] = []

        for event in self.events:
            if event.event_type is not EventType.JUSTIFICATION:
                continue
            if not self._visible(event, query.system_time) or not event.valid_at(query.valid_time):
                continue
            if event.proposition_id != proposition or event.about_world_branch_id != branch:
                continue
            if event.operation in {"revoke", "invalidate", "delete"}:
                continue

            families: set[str] = set()
            all_members_allowed = True
            for evidence_id in event.support_member_ids:
                evidence = self._evidence_event(evidence_id, query.system_time)
                if evidence is None:
                    all_members_allowed = False
                    break
                label = self._policy_label(evidence_id, query.system_time)
                if not policy_allows(label, requester):
                    all_members_allowed = False
                    break
                if evidence.source_family_id:
                    families.add(evidence.source_family_id)
            if not all_members_allowed:
                continue
            if len(families) < event.required_independent_sources:
                continue
            accepted.append(self._required(event.support_set_id, "support_set_id"))

        return tuple(sorted(set(accepted)))
