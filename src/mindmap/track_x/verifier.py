from __future__ import annotations

import re
from dataclasses import fields

from mindmap.canonical.model import CommonEvent, freeze_attrs

from .model import (
    FieldEvidence,
    RenderingFamily,
    VerificationDecision,
    VerificationStatus,
    VerifierInput,
)


def _optional(value: str) -> str | None:
    return None if value == "-" else value


def _optional_int(value: str) -> int | None:
    return None if value == "-" else int(value)


def _event(
    *,
    event_id: str,
    event_type: str,
    system_time: str,
    valid_from: str = "0",
    valid_to: str = "-",
    attributes: dict[str, object] | None = None,
    **kwargs: object,
) -> CommonEvent:
    return CommonEvent(
        event_id=event_id,
        event_type=event_type,
        system_time=int(system_time),
        valid_from=int(valid_from),
        valid_to=_optional_int(valid_to),
        attributes=freeze_attrs(attributes or {}),
        **kwargs,
    )


_WORLD_PATTERNS = (
    (
        RenderingFamily.EXPLICIT,
        re.compile(
            r"^Event (?P<event_id>\S+) was recorded at system time (?P<system_time>\d+)\. "
            r"It says that in world (?P<world>[^,]+), proposition (?P<proposition>\S+) "
            r"had value '(?P<value>.*?)' from valid time (?P<valid_from>-?\d+) "
            r"until (?P<valid_to>[^.]+)\.$"
        ),
    ),
    (
        RenderingFamily.CONVERSATIONAL,
        re.compile(
            r"^'In (?P<world>[^,]+), (?P<proposition>\S+) is (?P<value>.*?) "
            r"from (?P<valid_from>-?\d+) to (?P<valid_to>[^,]+),' says record "
            r"(?P<event_id>\S+), entered at system time (?P<system_time>\d+)\.$"
        ),
    ),
    (
        RenderingFamily.ELLIPTICAL,
        re.compile(
            r"^(?P<event_id>\S+) @system (?P<system_time>\d+): "
            r"(?P<world>[^/]+)/(?P<proposition>\S+) = (?P<value>.*?); "
            r"valid (?P<valid_from>-?\d+)\.\.(?P<valid_to>[^.]+)\.$"
        ),
    ),
)

_ATTITUDE_PATTERNS = (
    (
        RenderingFamily.EXPLICIT,
        re.compile(
            r"^Event (?P<event_id>\S+) was recorded at system time (?P<system_time>\d+)\. "
            r"Mind (?P<destination>\S+) set attitude (?P<attitude>\S+) toward "
            r"proposition (?P<proposition>\S+) about world (?P<world>[^,]+), "
            r"valid from (?P<valid_from>-?\d+) until (?P<valid_to>[^.]+)\.$"
        ),
    ),
    (
        RenderingFamily.CONVERSATIONAL,
        re.compile(
            r"^'I (?P<attitude>\S+) (?P<proposition>\S+) about (?P<world>[^,]+), "
            r"from (?P<valid_from>-?\d+) to (?P<valid_to>[^,]+),' states mind "
            r"(?P<destination>\S+); record (?P<event_id>\S+), system time "
            r"(?P<system_time>\d+)\.$"
        ),
    ),
    (
        RenderingFamily.ELLIPTICAL,
        re.compile(
            r"^(?P<event_id>\S+) @system (?P<system_time>\d+): "
            r"(?P<destination>\S+) -> (?P<attitude>\S+)\("
            r"(?P<proposition>[^@]+)@(?P<world>[^)]+)\); valid "
            r"(?P<valid_from>-?\d+)\.\.(?P<valid_to>[^.]+)\.$"
        ),
    ),
)

_EXPOSURE_PATTERNS = (
    (
        RenderingFamily.EXPLICIT,
        re.compile(
            r"^Event (?P<event_id>\S+) was recorded at system time (?P<system_time>\d+)\. "
            r"Mind (?P<destination>\S+) performed (?P<transfer>\S+) on evidence "
            r"(?P<object>\S+); source mind (?P<source>\S+); attribution "
            r"(?P<attribution>\S+); authorization (?P<authorization>[^.]+)\.$"
        ),
    ),
    (
        RenderingFamily.CONVERSATIONAL,
        re.compile(
            r"^'(?P<destination>\S+) (?P<transfer>\S+) (?P<object>\S+) from "
            r"(?P<source>\S+),' says record (?P<event_id>\S+) at system time "
            r"(?P<system_time>\d+); attribution (?P<attribution>[^,]+), "
            r"authorization (?P<authorization>[^.]+)\.$"
        ),
    ),
    (
        RenderingFamily.ELLIPTICAL,
        re.compile(
            r"^(?P<event_id>\S+) @system (?P<system_time>\d+): "
            r"(?P<source>\S+) -> (?P<destination>\S+) : (?P<transfer>\S+) "
            r"(?P<object>\S+) \[attribution=(?P<attribution>[^;]+); "
            r"authorization=(?P<authorization>[^]]+)\]\.$"
        ),
    ),
)

_POLICY_PATTERNS = (
    (
        RenderingFamily.EXPLICIT,
        re.compile(
            r"^Event (?P<event_id>\S+) was recorded at system time (?P<system_time>\d+)\. "
            r"Policy operation (?P<operation>\S+) applies to object (?P<object>\S+); "
            r"destination mind (?P<destination>\S+); label (?P<label>\S+); "
            r"valid from (?P<valid_from>-?\d+)\.$"
        ),
    ),
    (
        RenderingFamily.CONVERSATIONAL,
        re.compile(
            r"^'Apply (?P<operation>\S+) to (?P<object>\S+) for "
            r"(?P<destination>\S+), label (?P<label>\S+),' says policy record "
            r"(?P<event_id>\S+), system time (?P<system_time>\d+), valid from "
            r"(?P<valid_from>-?\d+)\.$"
        ),
    ),
    (
        RenderingFamily.ELLIPTICAL,
        re.compile(
            r"^(?P<event_id>\S+) @system (?P<system_time>\d+): policy "
            r"(?P<operation>\S+) (?P<object>\S+) -> (?P<destination>\S+) "
            r"\[label=(?P<label>[^;]+); valid_from=(?P<valid_from>-?\d+)\]\.$"
        ),
    ),
)

_LINEAGE_PATTERNS = (
    (
        RenderingFamily.EXPLICIT,
        re.compile(
            r"^Event (?P<event_id>\S+) was recorded at system time (?P<system_time>\d+)\. "
            r"Lineage operation (?P<kind>\S+) links source mind (?P<source>\S+) "
            r"to destination mind (?P<destination>\S+); snapshot (?P<snapshot>\S+); "
            r"cutoff (?P<cutoff>\S+); authorization (?P<authorization>[^.]+)\.$"
        ),
    ),
    (
        RenderingFamily.CONVERSATIONAL,
        re.compile(
            r"^'Create (?P<destination>\S+) by (?P<kind>\S+) from (?P<source>\S+), "
            r"snapshot (?P<snapshot>\S+) at cutoff (?P<cutoff>\S+), authorization "
            r"(?P<authorization>\S+),' says lineage record (?P<event_id>\S+), "
            r"system time (?P<system_time>\d+)\.$"
        ),
    ),
    (
        RenderingFamily.ELLIPTICAL,
        re.compile(
            r"^(?P<event_id>\S+) @system (?P<system_time>\d+): lineage "
            r"(?P<kind>\S+) (?P<source>\S+) -> (?P<destination>\S+) "
            r"\[snapshot=(?P<snapshot>[^;]+); cutoff=(?P<cutoff>[^;]+); "
            r"authorization=(?P<authorization>[^]]+)\]\.$"
        ),
    ),
)

_EVIDENCE_PATTERNS = (
    (
        RenderingFamily.EXPLICIT,
        re.compile(
            r"^Event (?P<event_id>\S+) was recorded at system time (?P<system_time>\d+)\. "
            r"Evidence object (?P<object>\S+) supports proposition (?P<proposition>\S+) "
            r"about world (?P<world>\S+); actor principal (?P<principal>\S+); actor mind "
            r"(?P<mind>\S+); placement (?P<placement>\S+); source family "
            r"(?P<source_family>\S+); policy (?P<policy>\S+); valid from "
            r"(?P<valid_from>-?\d+) until (?P<valid_to>[^.]+)\.$"
        ),
    ),
    (
        RenderingFamily.CONVERSATIONAL,
        re.compile(
            r"^'(?P<mind>\S+) for principal (?P<principal>\S+) records "
            r"(?P<object>\S+): (?P<proposition>\S+) about (?P<world>\S+), source "
            r"family (?P<source_family>\S+), policy (?P<policy>\S+), placement "
            r"(?P<placement>\S+), valid (?P<valid_from>-?\d+) to "
            r"(?P<valid_to>[^,]+),' says evidence record (?P<event_id>\S+) at "
            r"system time (?P<system_time>\d+)\.$"
        ),
    ),
    (
        RenderingFamily.ELLIPTICAL,
        re.compile(
            r"^(?P<event_id>\S+) @system (?P<system_time>\d+): evidence "
            r"(?P<object>\S+) => (?P<proposition>[^@]+)@(?P<world>\S+) "
            r"\[principal=(?P<principal>[^;]+); mind=(?P<mind>[^;]+); "
            r"placement=(?P<placement>[^;]+); source_family=(?P<source_family>[^;]+); "
            r"policy=(?P<policy>[^;]+); valid=(?P<valid_from>-?\d+)\.\."
            r"(?P<valid_to>[^]]+)\]\.$"
        ),
    ),
)


def _parse(raw_text: str) -> tuple[CommonEvent, RenderingFamily]:
    for family, pattern in _WORLD_PATTERNS:
        match = pattern.fullmatch(raw_text)
        if match:
            values = match.groupdict()
            return (
                _event(
                    event_id=values["event_id"],
                    event_type="world_claim",
                    system_time=values["system_time"],
                    valid_from=values["valid_from"],
                    valid_to=values["valid_to"],
                    proposition_id=values["proposition"],
                    about_world_branch_id=values["world"],
                    attributes={"value": values["value"]},
                ),
                family,
            )

    for family, pattern in _ATTITUDE_PATTERNS:
        match = pattern.fullmatch(raw_text)
        if match:
            values = match.groupdict()
            return (
                _event(
                    event_id=values["event_id"],
                    event_type="attitude",
                    system_time=values["system_time"],
                    valid_from=values["valid_from"],
                    valid_to=values["valid_to"],
                    destination_mind_instance_id=values["destination"],
                    proposition_id=values["proposition"],
                    about_world_branch_id=values["world"],
                    attitude_transition=values["attitude"],
                ),
                family,
            )

    for family, pattern in _EXPOSURE_PATTERNS:
        match = pattern.fullmatch(raw_text)
        if match:
            values = match.groupdict()
            return (
                _event(
                    event_id=values["event_id"],
                    event_type="exposure",
                    system_time=values["system_time"],
                    object_id=values["object"],
                    source_mind_instance_id=_optional(values["source"]),
                    destination_mind_instance_id=values["destination"],
                    transfer_kind=values["transfer"],
                    attribution_kind=_optional(values["attribution"]),
                    authorization_id=_optional(values["authorization"]),
                ),
                family,
            )

    for family, pattern in _POLICY_PATTERNS:
        match = pattern.fullmatch(raw_text)
        if match:
            values = match.groupdict()
            return (
                _event(
                    event_id=values["event_id"],
                    event_type="policy",
                    system_time=values["system_time"],
                    valid_from=values["valid_from"],
                    object_id=values["object"],
                    destination_mind_instance_id=_optional(values["destination"]),
                    policy_operation=values["operation"],
                    policy_label=_optional(values["label"]),
                ),
                family,
            )

    for family, pattern in _LINEAGE_PATTERNS:
        match = pattern.fullmatch(raw_text)
        if match:
            values = match.groupdict()
            return (
                _event(
                    event_id=values["event_id"],
                    event_type="lineage",
                    system_time=values["system_time"],
                    lineage_kind=values["kind"],
                    source_mind_instance_id=_optional(values["source"]),
                    destination_mind_instance_id=values["destination"],
                    snapshot_id=_optional(values["snapshot"]),
                    snapshot_cutoff=_optional_int(values["cutoff"]),
                    authorization_id=_optional(values["authorization"]),
                ),
                family,
            )

    for family, pattern in _EVIDENCE_PATTERNS:
        match = pattern.fullmatch(raw_text)
        if match:
            values = match.groupdict()
            return (
                _event(
                    event_id=values["event_id"],
                    event_type="evidence",
                    system_time=values["system_time"],
                    valid_from=values["valid_from"],
                    valid_to=values["valid_to"],
                    object_id=values["object"],
                    proposition_id=values["proposition"],
                    actor_principal_id=_optional(values["principal"]),
                    actor_mind_instance_id=_optional(values["mind"]),
                    source_placement_id=_optional(values["placement"]),
                    about_world_branch_id=values["world"],
                    source_family_id=_optional(values["source_family"]),
                    policy_label=_optional(values["policy"]),
                ),
                family,
            )

    raise ValueError("raw evidence did not match a frozen v0.1 rendering")


def _confidence(family: RenderingFamily) -> float:
    return {
        RenderingFamily.EXPLICIT: 0.98,
        RenderingFamily.CONVERSATIONAL: 0.90,
        RenderingFamily.ELLIPTICAL: 0.84,
    }[family]


def _field_evidence(event: CommonEvent, confidence: float) -> tuple[FieldEvidence, ...]:
    evidence: list[FieldEvidence] = []
    for definition in fields(CommonEvent):
        value = getattr(event, definition.name)
        if value is None or value == ():
            continue
        evidence.append(FieldEvidence(definition.name, value, confidence))
    return tuple(evidence)


class RawEvidenceVerifier:
    """Fixed deterministic raw-evidence verifier with no evaluator metadata.

    This implementation establishes an information-firewall and metric P0. It
    is intentionally not presented as a learned natural-language verifier.
    """

    implementation_name = "raw_evidence_verifier_v0.1"

    def verify(self, verifier_input: VerifierInput) -> VerificationDecision:
        raw_text = verifier_input.raw_text
        if raw_text is None or not raw_text.strip():
            return VerificationDecision(
                VerificationStatus.ABSTAIN,
                None,
                confidence=0.0,
                reason_codes=("raw_unavailable",),
                parser_calls=0,
            )

        try:
            parsed, family = _parse(raw_text.strip())
        except (ValueError, TypeError):
            return VerificationDecision(
                VerificationStatus.ABSTAIN,
                None,
                confidence=0.20,
                reason_codes=("raw_parse_failure",),
            )

        confidence = _confidence(family)
        evidence = _field_evidence(parsed, confidence)
        candidate = verifier_input.candidate_event
        if candidate is None:
            return VerificationDecision(
                VerificationStatus.CORRECT,
                parsed,
                confidence=confidence,
                field_evidence=evidence,
                reason_codes=("candidate_missing_raw_reconstruction",),
            )

        if candidate.event_id != parsed.event_id or candidate.event_type != parsed.event_type:
            return VerificationDecision(
                VerificationStatus.REJECT,
                None,
                confidence=confidence,
                field_evidence=evidence,
                reason_codes=("candidate_identity_conflict",),
            )

        if candidate == parsed:
            return VerificationDecision(
                VerificationStatus.ACCEPT,
                candidate,
                confidence=confidence,
                field_evidence=evidence,
                reason_codes=("raw_candidate_agree",),
            )

        return VerificationDecision(
            VerificationStatus.CORRECT,
            parsed,
            confidence=confidence,
            field_evidence=evidence,
            reason_codes=("raw_candidate_field_conflict",),
        )
