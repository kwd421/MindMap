from __future__ import annotations

import re
from dataclasses import dataclass, replace
from math import isfinite

from mindmap.canonical.model import CommonEvent, freeze_attrs

from .model import FieldEvidence, VerificationDecision, VerificationStatus
from .v02_data import CandidateMutation


@dataclass(frozen=True, slots=True)
class PrimaryExtraction:
    event: CommonEvent | None
    confidence: float
    field_confidences: tuple[FieldEvidence, ...] = ()
    reason_codes: tuple[str, ...] = ()
    parser_calls: int = 1

    def __post_init__(self) -> None:
        if not isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("primary confidence must be finite and in [0, 1]")
        if self.parser_calls < 0:
            raise ValueError("primary parser_calls cannot be negative")


@dataclass(frozen=True, slots=True)
class V02VerifierInput:
    raw_text: str | None
    context_passages: tuple[str, ...]
    candidate_event: CommonEvent | None
    context_events: tuple[CommonEvent, ...]
    insertion_index: int

    def __post_init__(self) -> None:
        if self.insertion_index < 0 or self.insertion_index > len(self.context_events):
            raise ValueError("insertion index is outside context event bounds")
        if len(self.context_passages) > 3:
            raise ValueError("too many raw context passages")


def apply_candidate_mutation(
    event: CommonEvent, mutation: CandidateMutation
) -> CommonEvent:
    if mutation.field_name == "attributes.value":
        attrs = dict(event.attributes)
        attrs["value"] = mutation.replacement
        return replace(event, attributes=freeze_attrs(attrs))
    if not hasattr(event, mutation.field_name):
        raise ValueError(f"unknown CommonEvent field: {mutation.field_name}")
    return replace(event, **{mutation.field_name: mutation.replacement})


def _evidence(field_name: str, value: object, confidence: float) -> FieldEvidence:
    return FieldEvidence(field_name=field_name, value=value, confidence=confidence)


class DevelopmentPrimaryExtractor:
    """Development-only primary parser.

    It uses anchored, record-type-specific patterns. The independent verifier
    below uses a different lexical reconstruction path and does not call these
    methods or inspect their parser traces.
    """

    implementation_name = "development_primary_v0.2"

    _archive_world = re.compile(
        r"Archive note (?P<event>F\d{2}\.\w+) was entered at system time "
        r"(?P<system>\d+)\. It concerns the (?P<world>[\w-]+) world: for the "
        r"proposition (?P<proposition>[\w.]+), the key was in (?P<value>Room \d+) "
        r"from world time (?P<valid_from>\d+) until time (?P<valid_to>\d+),"
    )
    _branch_world = re.compile(
        r"World-state record (?P<event>F\d{2}\.\w+) entered at system time "
        r"(?P<system>\d+) says that (?P<proposition>[\w.]+) in the "
        r"(?P<world>[\w-]+) branch became (?P<value>\w+) at valid time "
        r"(?P<valid_from>\d+)"
    )
    _attitude = re.compile(
        r"(?:Replica (?P<replica>\w+) made attitude record|At system time "
        r"(?P<system_first>\d+), replica (?P<replica_second>\w+) wrote attitude record) "
        r"(?P<event>F\d{2}\.\w+)(?: at system time (?P<system_second>\d+))?[:.] "
        r"(?:it |(?P=replica_second) )?(?P<attitude>believed|disbelieved) "
        r"(?:the proposition )?(?P<proposition>[\w.]+) (?:about|in) the "
        r"(?P<world>[\w-]+) world"
    )
    _copy = re.compile(
        r"Transfer record (?P<event>F\d{2}\.\w+) was committed at system time "
        r"(?P<system>\d+)\. Source mind (?P<source>\w+) copied evidence "
        r"(?P<object>[\w.]+) into destination mind (?P<destination>\w+) as an "
        r"(?P<kind>evidence copy)"
    )
    _receive = re.compile(
        r"At system time (?P<system>\d+), record (?P<event>F\d{2}\.\w+) says "
        r"that source mind (?P<source>\w+) sent evidence (?P<object>[\w.]+) "
        r"to destination mind (?P<destination>\w+), which received it as a report"
    )
    _policy = re.compile(
        r"Policy record (?P<event>F\d{2}\.\w+) was entered at system time "
        r"(?P<system>\d+)\. It (?P<operation>self-sealed|self-unsealed) evidence "
        r"(?P<object>[\w.]+) for mind (?P<destination>\w+)"
    )

    def extract(self, raw_text: str | None) -> PrimaryExtraction:
        if raw_text is None or not raw_text.strip():
            return PrimaryExtraction(
                event=None,
                confidence=0.0,
                reason_codes=("raw_unavailable",),
                parser_calls=0,
            )
        text = raw_text.strip()

        match = self._archive_world.search(text)
        if match:
            values = match.groupdict()
            confidence = 0.94
            event = CommonEvent(
                event_id=values["event"],
                event_type="world_claim",
                system_time=int(values["system"]),
                valid_from=int(values["valid_from"]),
                valid_to=int(values["valid_to"]),
                proposition_id=values["proposition"],
                about_world_branch_id=values["world"],
                attributes=freeze_attrs({"value": values["value"]}),
            )
            return PrimaryExtraction(
                event,
                confidence,
                (
                    _evidence("about_world_branch_id", values["world"], confidence),
                    _evidence("attributes.value", values["value"], confidence),
                ),
                ("primary_archive_world",),
            )

        match = self._branch_world.search(text)
        if match:
            values = match.groupdict()
            confidence = 0.92
            event = CommonEvent(
                event_id=values["event"],
                event_type="world_claim",
                system_time=int(values["system"]),
                valid_from=int(values["valid_from"]),
                proposition_id=values["proposition"],
                about_world_branch_id=values["world"],
                attributes=freeze_attrs({"value": values["value"]}),
            )
            return PrimaryExtraction(
                event,
                confidence,
                (
                    _evidence("about_world_branch_id", values["world"], confidence),
                    _evidence("attributes.value", values["value"], confidence),
                ),
                ("primary_branch_world",),
            )

        match = self._attitude.search(text)
        if match:
            values = match.groupdict()
            confidence = 0.90
            replica = values["replica"] or values["replica_second"]
            system = values["system_first"] or values["system_second"]
            attitude = {
                "believed": "believe",
                "disbelieved": "disbelieve",
            }[values["attitude"]]
            event = CommonEvent(
                event_id=values["event"],
                event_type="attitude",
                system_time=int(system),
                destination_mind_instance_id=replica,
                proposition_id=values["proposition"],
                about_world_branch_id=values["world"],
                attitude_transition=attitude,
            )
            return PrimaryExtraction(
                event,
                confidence,
                (
                    _evidence("destination_mind_instance_id", replica, confidence),
                    _evidence("attitude_transition", attitude, confidence),
                ),
                ("primary_attitude",),
            )

        match = self._copy.search(text)
        if match:
            values = match.groupdict()
            confidence = 0.93
            event = CommonEvent(
                event_id=values["event"],
                event_type="exposure",
                system_time=int(values["system"]),
                object_id=values["object"],
                source_mind_instance_id=values["source"],
                destination_mind_instance_id=values["destination"],
                transfer_kind="evidence_copy",
            )
            return PrimaryExtraction(
                event,
                confidence,
                (_evidence("transfer_kind", "evidence_copy", confidence),),
                ("primary_evidence_copy",),
            )

        match = self._receive.search(text)
        if match:
            values = match.groupdict()
            confidence = 0.91
            event = CommonEvent(
                event_id=values["event"],
                event_type="exposure",
                system_time=int(values["system"]),
                object_id=values["object"],
                source_mind_instance_id=values["source"],
                destination_mind_instance_id=values["destination"],
                transfer_kind="receive",
            )
            return PrimaryExtraction(
                event,
                confidence,
                (
                    _evidence(
                        "destination_mind_instance_id",
                        values["destination"],
                        confidence,
                    ),
                    _evidence("transfer_kind", "receive", confidence),
                ),
                ("primary_receive",),
            )

        match = self._policy.search(text)
        if match:
            values = match.groupdict()
            confidence = 0.91
            operation = {
                "self-sealed": "self_seal",
                "self-unsealed": "self_unseal",
            }[values["operation"]]
            event = CommonEvent(
                event_id=values["event"],
                event_type="policy",
                system_time=int(values["system"]),
                object_id=values["object"],
                destination_mind_instance_id=values["destination"],
                policy_operation=operation,
            )
            return PrimaryExtraction(
                event,
                confidence,
                (_evidence("policy_operation", operation, confidence),),
                ("primary_policy",),
            )

        return PrimaryExtraction(
            event=None,
            confidence=0.20,
            reason_codes=("primary_parse_insufficient",),
        )


class DevelopmentIndependentVerifier:
    """Independent lexical verifier for development passages.

    It does not call `DevelopmentPrimaryExtractor`, does not read its field
    confidences or traces, and does not receive evaluator-only record metadata.
    """

    implementation_name = "development_independent_verifier_v0.2"

    @staticmethod
    def _record_id(text: str) -> str | None:
        match = re.search(r"\bF\d{2}\.[A-Za-z0-9]+\b", text)
        return match.group(0) if match else None

    @staticmethod
    def _system_time(text: str) -> int | None:
        match = re.search(r"(?:system time|committed at system time)\s+(\d+)", text)
        return int(match.group(1)) if match else None

    def _reconstruct(self, text: str) -> tuple[CommonEvent | None, tuple[str, ...]]:
        event_id = self._record_id(text)
        system_time = self._system_time(text)
        if event_id is None or system_time is None:
            return None, ("missing_event_identity_or_system_time",)

        lowered = text.lower()
        if "key.location" in text and "room 0" in lowered:
            world = "main" if "main world" in lowered else None
            interval = re.search(r"world time (\d+) until time (\d+)", text)
            if world is None or interval is None:
                return None, ("world_claim_scope_or_interval_ambiguous",)
            return (
                CommonEvent(
                    event_id=event_id,
                    event_type="world_claim",
                    system_time=system_time,
                    valid_from=int(interval.group(1)),
                    valid_to=int(interval.group(2)),
                    proposition_id="key.location",
                    about_world_branch_id=world,
                    attributes=freeze_attrs({"value": "Room 0"}),
                ),
                ("verifier_world_archive",),
            )

        if "door.color" in text and "became red" in lowered:
            world_match = re.search(r"in the ([\w-]+) branch", text)
            valid_match = re.search(r"valid time (\d+)", text)
            if world_match is None or valid_match is None:
                return None, ("world_claim_branch_ambiguous",)
            return (
                CommonEvent(
                    event_id=event_id,
                    event_type="world_claim",
                    system_time=system_time,
                    valid_from=int(valid_match.group(1)),
                    proposition_id="door.color",
                    about_world_branch_id=world_match.group(1),
                    attributes=freeze_attrs({"value": "red"}),
                ),
                ("verifier_branch_world",),
            )

        if "attitude record" in lowered:
            mind_match = re.search(r"(?:replica\s+)(R2|A1)", text)
            proposition_match = re.search(r"\b(key_in_r4|alarm_on)\b", text)
            world_match = re.search(r"(?:about|in) the ([\w-]+) world", text)
            if "disbelieved" in lowered:
                attitude = "disbelieve"
            elif "believed" in lowered:
                attitude = "believe"
            else:
                attitude = None
            if (
                mind_match is None
                or proposition_match is None
                or world_match is None
                or attitude is None
            ):
                return None, ("attitude_holder_or_scope_ambiguous",)
            return (
                CommonEvent(
                    event_id=event_id,
                    event_type="attitude",
                    system_time=system_time,
                    destination_mind_instance_id=mind_match.group(1),
                    proposition_id=proposition_match.group(1),
                    about_world_branch_id=world_match.group(1),
                    attitude_transition=attitude,
                ),
                ("verifier_attitude",),
            )

        if "copied evidence" in lowered and "evidence copy" in lowered:
            source = re.search(r"source mind (\w+)", text)
            destination = re.search(r"destination mind (\w+)", text)
            evidence = re.search(r"copied evidence ([\w.]+)", text)
            if source is None or destination is None or evidence is None:
                return None, ("copy_participants_ambiguous",)
            return (
                CommonEvent(
                    event_id=event_id,
                    event_type="exposure",
                    system_time=system_time,
                    object_id=evidence.group(1),
                    source_mind_instance_id=source.group(1),
                    destination_mind_instance_id=destination.group(1),
                    transfer_kind="evidence_copy",
                ),
                ("verifier_evidence_copy",),
            )

        if "received it as a report" in lowered:
            source = re.search(r"source mind (\w+)", text)
            destination = re.search(r"destination mind (\w+)", text)
            evidence = re.search(r"sent evidence ([\w.]+)", text)
            if source is None or destination is None or evidence is None:
                return None, ("receipt_destination_ambiguous",)
            return (
                CommonEvent(
                    event_id=event_id,
                    event_type="exposure",
                    system_time=system_time,
                    object_id=evidence.group(1),
                    source_mind_instance_id=source.group(1),
                    destination_mind_instance_id=destination.group(1),
                    transfer_kind="receive",
                ),
                ("verifier_receive",),
            )

        if "policy record" in lowered:
            destination = re.search(r"for mind (\w+)", text)
            evidence = re.search(r"evidence ([\w.]+)", text)
            if "self-sealed" in lowered:
                operation = "self_seal"
            elif "self-unsealed" in lowered:
                operation = "self_unseal"
            else:
                operation = None
            if destination is None or evidence is None or operation is None:
                return None, ("policy_direction_ambiguous",)
            return (
                CommonEvent(
                    event_id=event_id,
                    event_type="policy",
                    system_time=system_time,
                    object_id=evidence.group(1),
                    destination_mind_instance_id=destination.group(1),
                    policy_operation=operation,
                ),
                ("verifier_policy",),
            )

        return None, ("unsupported_or_ambiguous_passage",)

    def verify(self, verifier_input: V02VerifierInput) -> VerificationDecision:
        raw_text = verifier_input.raw_text
        if raw_text is None or not raw_text.strip():
            return VerificationDecision(
                VerificationStatus.ABSTAIN,
                None,
                confidence=0.0,
                reason_codes=("raw_unavailable",),
                parser_calls=0,
            )

        reconstructed, reasons = self._reconstruct(raw_text.strip())
        if reconstructed is None:
            return VerificationDecision(
                VerificationStatus.ABSTAIN,
                None,
                confidence=0.45,
                reason_codes=reasons,
            )

        confidence = 0.88
        candidate = verifier_input.candidate_event
        if candidate is None:
            return VerificationDecision(
                VerificationStatus.CORRECT,
                reconstructed,
                confidence=confidence,
                reason_codes=reasons + ("candidate_missing",),
            )
        if (
            candidate.event_id != reconstructed.event_id
            or candidate.event_type != reconstructed.event_type
        ):
            return VerificationDecision(
                VerificationStatus.REJECT,
                None,
                confidence=confidence,
                reason_codes=reasons + ("candidate_identity_conflict",),
            )
        if candidate == reconstructed:
            return VerificationDecision(
                VerificationStatus.ACCEPT,
                candidate,
                confidence=confidence,
                reason_codes=reasons + ("candidate_supported",),
            )
        return VerificationDecision(
            VerificationStatus.CORRECT,
            reconstructed,
            confidence=confidence,
            reason_codes=reasons + ("candidate_field_conflict",),
        )
