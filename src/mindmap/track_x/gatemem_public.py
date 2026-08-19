from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
import json
from typing import Any, Literal, cast

from .adapter_guard import assert_hidden_annotations_absent, strip_hidden_annotations
from .benchmark_specs import GATEMEM
from .gatemem_opaque import GateMemOpaqueIds

GateMemAction = Literal["answer", "answer_redacted", "refuse", "no_memory"]
_ALLOWED_ACTIONS = frozenset({"answer", "answer_redacted", "refuse", "no_memory"})
_SOURCE_CHECKPOINT_KEYS = frozenset(
    {"checkpoint_id", "episode_id", "as_of_turn_id", "asker", "query_text"}
)


class GateMemBoundaryError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PublicPrincipal:
    """Method-facing principal with an evaluator-generated opaque identity."""

    principal_id: str
    role: str
    display_name: str | None = None


@dataclass(frozen=True, slots=True)
class PublicEpisode:
    """Raw-language reset view.

    Relationships are intentionally absent because the pinned GateMem objects
    contain answer-defining policy and authorization annotations. Policy must be
    inferred from the incrementally ingested public dialogue in this condition.
    """

    episode_id: str
    domain: str
    principals: tuple[PublicPrincipal, ...]


@dataclass(frozen=True, slots=True)
class PublicTurn:
    turn_id: str
    timestamp: str | None
    speaker_principal_id: str
    speaker_role: str
    turn_kind: str
    text: str


@dataclass(frozen=True, slots=True)
class PublicCheckpoint:
    """Method-facing query capability with no source chronology identifier."""

    checkpoint_id: str
    episode_id: str
    asker_principal_id: str
    asker_role: str
    query_text: str


@dataclass(frozen=True, slots=True)
class PublicCheckpointBundle:
    checkpoint: PublicCheckpoint
    source_sha256: str
    public_sha256: str
    removed_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PublicPrediction:
    action: GateMemAction
    answer: str
    answer_structured: dict[str, Any]
    used_record_ids: tuple[str, ...]
    memory_audit: dict[str, Any] | None = None


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GateMemBoundaryError(f"{field} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise GateMemBoundaryError(f"{field} must be a string or null")
    return value


def _json_clone(value: Any) -> Any:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise GateMemBoundaryError("public GateMem data must be strict JSON") from exc
    return json.loads(encoded)


def public_episode_from_raw(
    raw: Mapping[str, Any],
    *,
    opaque_ids: GateMemOpaqueIds,
) -> PublicEpisode:
    """Build a reset view without future turns, records, or policy relationships."""

    source_episode_id = _required_text(raw.get("episode_id"), "episode_id")
    domain = _required_text(raw.get("domain"), "domain")
    entities = raw.get("entities") or {}
    if not isinstance(entities, Mapping):
        raise GateMemBoundaryError("entities must be an object")

    principals_raw = entities.get("principals") or []
    relationships_raw = entities.get("relationships") or []
    if not isinstance(principals_raw, Sequence) or isinstance(
        principals_raw, (str, bytes)
    ):
        raise GateMemBoundaryError("entities.principals must be a list")
    if not isinstance(relationships_raw, Sequence) or isinstance(
        relationships_raw, (str, bytes)
    ):
        raise GateMemBoundaryError("entities.relationships must be a list")

    principals: list[PublicPrincipal] = []
    seen_source: set[str] = set()
    seen_method: set[str] = set()
    for index, item in enumerate(principals_raw):
        if not isinstance(item, Mapping):
            raise GateMemBoundaryError(
                f"entities.principals[{index}] must be an object"
            )
        source_principal_id = _required_text(
            item.get("principal_id"), f"entities.principals[{index}].principal_id"
        )
        if source_principal_id in seen_source:
            raise GateMemBoundaryError(
                f"duplicate source principal_id: {source_principal_id}"
            )
        seen_source.add(source_principal_id)
        method_principal_id = opaque_ids.principal(
            source_episode_id, source_principal_id
        )
        if method_principal_id in seen_method:  # pragma: no cover - HMAC collision guard
            raise GateMemBoundaryError("opaque principal identifier collision")
        seen_method.add(method_principal_id)
        principals.append(
            PublicPrincipal(
                principal_id=method_principal_id,
                role=_required_text(
                    item.get("role"), f"entities.principals[{index}].role"
                ),
                display_name=_optional_text(
                    item.get("display_name"),
                    f"entities.principals[{index}].display_name",
                ),
            )
        )

    # `entities.relationships` is validated as a list above but deliberately not
    # copied. It contains source-dataset policy labels such as access levels.
    return PublicEpisode(
        episode_id=opaque_ids.episode(source_episode_id),
        domain=domain,
        principals=tuple(principals),
    )


def public_turn_from_raw(
    raw: Mapping[str, Any],
    *,
    source_episode_id: str,
    opaque_ids: GateMemOpaqueIds,
) -> PublicTurn:
    """Build a raw-language turn view without source IDs or gold record metadata."""

    source_episode_id = _required_text(source_episode_id, "source_episode_id")
    source_turn_id = _required_text(raw.get("turn_id"), "turn_id")
    speaker = raw.get("speaker") or {}
    if not isinstance(speaker, Mapping):
        raise GateMemBoundaryError("turn speaker must be an object")
    source_principal_id = _required_text(
        speaker.get("principal_id"), "speaker.principal_id"
    )
    return PublicTurn(
        turn_id=opaque_ids.turn(source_episode_id, source_turn_id),
        timestamp=_optional_text(raw.get("timestamp"), "timestamp"),
        speaker_principal_id=opaque_ids.principal(
            source_episode_id, source_principal_id
        ),
        speaker_role=_required_text(speaker.get("role"), "speaker.role"),
        turn_kind=_required_text(raw.get("turn_kind", "dialogue"), "turn_kind"),
        text=_required_text(raw.get("text"), "text"),
    )


def public_checkpoint_from_raw(
    raw: Mapping[str, Any],
    *,
    opaque_ids: GateMemOpaqueIds,
) -> PublicCheckpointBundle:
    """Redact scorer fields and replace every dataset identity with a surrogate."""

    redaction = strip_hidden_annotations(dict(raw), GATEMEM.hidden_paths)
    assert_hidden_annotations_absent(redaction.payload, GATEMEM.hidden_paths)
    if not isinstance(redaction.payload, Mapping):
        raise GateMemBoundaryError("checkpoint must be an object")

    unexpected = sorted(set(redaction.payload) - _SOURCE_CHECKPOINT_KEYS)
    if unexpected:
        raise GateMemBoundaryError(
            "unreviewed GateMem checkpoint fields crossed the source boundary: "
            + ", ".join(unexpected)
        )

    source_checkpoint_id = _required_text(
        redaction.payload.get("checkpoint_id"), "checkpoint_id"
    )
    source_episode_id = _required_text(
        redaction.payload.get("episode_id"), "episode_id"
    )
    # The source as-of identifier is validated and consumed only by the outer
    # runner. It is intentionally absent from PublicCheckpoint.
    _required_text(redaction.payload.get("as_of_turn_id"), "as_of_turn_id")

    asker = redaction.payload.get("asker") or {}
    if not isinstance(asker, Mapping):
        raise GateMemBoundaryError("checkpoint asker must be an object")
    source_asker_id = _required_text(
        asker.get("principal_id"), "asker.principal_id"
    )
    checkpoint = PublicCheckpoint(
        checkpoint_id=opaque_ids.query(source_episode_id, source_checkpoint_id),
        episode_id=opaque_ids.episode(source_episode_id),
        asker_principal_id=opaque_ids.principal(
            source_episode_id, source_asker_id
        ),
        asker_role=_required_text(asker.get("role"), "asker.role"),
        query_text=_required_text(redaction.payload.get("query_text"), "query_text"),
    )
    removed_paths = tuple(
        sorted(set(redaction.removed_paths) | {"$.as_of_turn_id"})
    )
    return PublicCheckpointBundle(
        checkpoint=checkpoint,
        source_sha256=redaction.source_sha256,
        public_sha256=canonical_public_sha256(checkpoint),
        removed_paths=removed_paths,
    )


def canonical_public_sha256(value: Any) -> str:
    from hashlib import sha256

    payload = json.dumps(
        _json_clone(asdict(value)),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def public_prediction_from_raw(raw: Mapping[str, Any]) -> PublicPrediction:
    action_value = _required_text(raw.get("action"), "action")
    if action_value not in _ALLOWED_ACTIONS:
        raise GateMemBoundaryError(f"unsupported GateMem action: {action_value}")

    answer = raw.get("answer", "")
    if not isinstance(answer, str):
        raise GateMemBoundaryError("answer must be a string")

    structured_raw = raw.get("answer_structured") or {}
    if not isinstance(structured_raw, Mapping):
        raise GateMemBoundaryError("answer_structured must be an object")
    structured = _json_clone(dict(structured_raw))

    used_raw = raw.get("used_record_ids") or []
    if not isinstance(used_raw, Sequence) or isinstance(used_raw, (str, bytes)):
        raise GateMemBoundaryError("used_record_ids must be a list")
    used = tuple(
        _required_text(value, f"used_record_ids[{index}]")
        for index, value in enumerate(used_raw)
    )
    if len(set(used)) != len(used):
        raise GateMemBoundaryError("used_record_ids must not contain duplicates")

    audit_raw = raw.get("memory_audit")
    audit: dict[str, Any] | None = None
    if audit_raw is not None:
        if not isinstance(audit_raw, Mapping):
            raise GateMemBoundaryError("memory_audit must be an object or null")
        audit = _json_clone(dict(audit_raw))

    return PublicPrediction(
        action=cast(GateMemAction, action_value),
        answer=answer,
        answer_structured=structured,
        used_record_ids=used,
        memory_audit=audit,
    )


def public_episode_json(value: PublicEpisode) -> dict[str, Any]:
    return _json_clone(asdict(value))


def public_turn_json(value: PublicTurn) -> dict[str, Any]:
    return _json_clone(asdict(value))


def public_checkpoint_json(value: PublicCheckpoint) -> dict[str, Any]:
    return _json_clone(asdict(value))


def public_prediction_json(value: PublicPrediction) -> dict[str, Any]:
    output = _json_clone(asdict(value))
    if output.get("memory_audit") is None:
        output.pop("memory_audit", None)
    return output
