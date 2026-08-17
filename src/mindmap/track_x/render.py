from __future__ import annotations

from mindmap.canonical.model import CommonEvent

from .model import RenderingFamily


def _show(value: object | None) -> str:
    return "-" if value is None else str(value)


def _valid_to(event: CommonEvent) -> str:
    return _show(event.valid_to)


def render_event(event: CommonEvent, family: RenderingFamily) -> str:
    """Render raw evidence from the gold event before candidate mutation.

    The templates are deliberately small and auditable. They are a fixed
    synthetic parser ceiling, not a claim about unrestricted natural language.
    """

    if event.event_type == "world_claim":
        value = dict(event.attributes).get("value", "unknown")
        if family is RenderingFamily.EXPLICIT:
            return (
                f"Event {event.event_id} was recorded at system time {event.system_time}. "
                f"It says that in world {event.about_world_branch_id}, proposition "
                f"{event.proposition_id} had value '{value}' from valid time "
                f"{event.valid_from} until {_valid_to(event)}."
            )
        if family is RenderingFamily.CONVERSATIONAL:
            return (
                f"'In {event.about_world_branch_id}, {event.proposition_id} is {value} "
                f"from {event.valid_from} to {_valid_to(event)},' says record "
                f"{event.event_id}, entered at system time {event.system_time}."
            )
        return (
            f"{event.event_id} @system {event.system_time}: "
            f"{event.about_world_branch_id}/{event.proposition_id} = {value}; "
            f"valid {event.valid_from}..{_valid_to(event)}."
        )

    if event.event_type == "attitude":
        if family is RenderingFamily.EXPLICIT:
            return (
                f"Event {event.event_id} was recorded at system time {event.system_time}. "
                f"Mind {event.destination_mind_instance_id} set attitude "
                f"{event.attitude_transition} toward proposition {event.proposition_id} "
                f"about world {event.about_world_branch_id}, valid from "
                f"{event.valid_from} until {_valid_to(event)}."
            )
        if family is RenderingFamily.CONVERSATIONAL:
            return (
                f"'I {event.attitude_transition} {event.proposition_id} about "
                f"{event.about_world_branch_id}, from {event.valid_from} to "
                f"{_valid_to(event)},' states mind {event.destination_mind_instance_id}; "
                f"record {event.event_id}, system time {event.system_time}."
            )
        return (
            f"{event.event_id} @system {event.system_time}: "
            f"{event.destination_mind_instance_id} -> {event.attitude_transition}"
            f"({event.proposition_id}@{event.about_world_branch_id}); "
            f"valid {event.valid_from}..{_valid_to(event)}."
        )

    if event.event_type == "exposure":
        source = _show(event.source_mind_instance_id)
        attribution = _show(event.attribution_kind)
        authorization = _show(event.authorization_id)
        if family is RenderingFamily.EXPLICIT:
            return (
                f"Event {event.event_id} was recorded at system time {event.system_time}. "
                f"Mind {event.destination_mind_instance_id} performed "
                f"{event.transfer_kind} on evidence {event.object_id}; source mind "
                f"{source}; attribution {attribution}; authorization {authorization}."
            )
        if family is RenderingFamily.CONVERSATIONAL:
            return (
                f"'{event.destination_mind_instance_id} {event.transfer_kind} "
                f"{event.object_id} from {source},' says record {event.event_id} at "
                f"system time {event.system_time}; attribution {attribution}, "
                f"authorization {authorization}."
            )
        return (
            f"{event.event_id} @system {event.system_time}: {source} -> "
            f"{event.destination_mind_instance_id} : {event.transfer_kind} "
            f"{event.object_id} [attribution={attribution}; "
            f"authorization={authorization}]."
        )

    if event.event_type == "policy":
        destination = _show(event.destination_mind_instance_id)
        label = _show(event.policy_label)
        if family is RenderingFamily.EXPLICIT:
            return (
                f"Event {event.event_id} was recorded at system time {event.system_time}. "
                f"Policy operation {event.policy_operation} applies to object "
                f"{event.object_id}; destination mind {destination}; label {label}; "
                f"valid from {event.valid_from}."
            )
        if family is RenderingFamily.CONVERSATIONAL:
            return (
                f"'Apply {event.policy_operation} to {event.object_id} for "
                f"{destination}, label {label},' says policy record {event.event_id}, "
                f"system time {event.system_time}, valid from {event.valid_from}."
            )
        return (
            f"{event.event_id} @system {event.system_time}: policy "
            f"{event.policy_operation} {event.object_id} -> {destination} "
            f"[label={label}; valid_from={event.valid_from}]."
        )

    if event.event_type == "lineage":
        source = _show(event.source_mind_instance_id)
        snapshot = _show(event.snapshot_id)
        cutoff = _show(event.snapshot_cutoff)
        authorization = _show(event.authorization_id)
        if family is RenderingFamily.EXPLICIT:
            return (
                f"Event {event.event_id} was recorded at system time {event.system_time}. "
                f"Lineage operation {event.lineage_kind} links source mind {source} "
                f"to destination mind {event.destination_mind_instance_id}; snapshot "
                f"{snapshot}; cutoff {cutoff}; authorization {authorization}."
            )
        if family is RenderingFamily.CONVERSATIONAL:
            return (
                f"'Create {event.destination_mind_instance_id} by "
                f"{event.lineage_kind} from {source}, snapshot {snapshot} at cutoff "
                f"{cutoff}, authorization {authorization},' says lineage record "
                f"{event.event_id}, system time {event.system_time}."
            )
        return (
            f"{event.event_id} @system {event.system_time}: lineage "
            f"{event.lineage_kind} {source} -> {event.destination_mind_instance_id} "
            f"[snapshot={snapshot}; cutoff={cutoff}; authorization={authorization}]."
        )

    if event.event_type == "evidence":
        principal = _show(event.actor_principal_id)
        mind = _show(event.actor_mind_instance_id)
        placement = _show(event.source_placement_id)
        source_family = _show(event.source_family_id)
        policy = _show(event.policy_label)
        if family is RenderingFamily.EXPLICIT:
            return (
                f"Event {event.event_id} was recorded at system time {event.system_time}. "
                f"Evidence object {event.object_id} supports proposition "
                f"{event.proposition_id} about world {event.about_world_branch_id}; "
                f"actor principal {principal}; actor mind {mind}; placement "
                f"{placement}; source family {source_family}; policy {policy}; "
                f"valid from {event.valid_from} until {_valid_to(event)}."
            )
        if family is RenderingFamily.CONVERSATIONAL:
            return (
                f"'{mind} for principal {principal} records {event.object_id}: "
                f"{event.proposition_id} about {event.about_world_branch_id}, source "
                f"family {source_family}, policy {policy}, placement {placement}, "
                f"valid {event.valid_from} to {_valid_to(event)},' says evidence "
                f"record {event.event_id} at system time {event.system_time}."
            )
        return (
            f"{event.event_id} @system {event.system_time}: evidence {event.object_id} "
            f"=> {event.proposition_id}@{event.about_world_branch_id} "
            f"[principal={principal}; mind={mind}; placement={placement}; "
            f"source_family={source_family}; policy={policy}; "
            f"valid={event.valid_from}..{_valid_to(event)}]."
        )

    raise ValueError(f"unsupported raw rendering event type: {event.event_type}")
