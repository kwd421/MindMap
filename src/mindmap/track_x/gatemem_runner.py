from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import json
from time import perf_counter
from typing import Any

from .adapter_guard import (
    assert_prediction_coverage_complete,
    canonical_json_sha256,
)
from .gatemem_opaque import GateMemOpaqueIds
from .gatemem_public import (
    GateMemBoundaryError,
    PublicEpisode,
    PublicPrediction,
    public_checkpoint_from_raw,
    public_episode_from_raw,
    public_episode_json,
    public_prediction_json,
    public_turn_from_raw,
    public_turn_json,
)
from .gatemem_session import GateMemPublicSession, PublicGateMemAgent


@dataclass(frozen=True, slots=True)
class TurnBoundaryAudit:
    source_turn_id: str
    source_sha256: str
    public_sha256: str
    removed_root_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CheckpointBoundaryAudit:
    source_checkpoint_id: str
    source_episode_id: str
    source_as_of_turn_id: str
    source_sha256: str
    public_sha256: str
    removed_paths: tuple[str, ...]
    prediction_sha256: str
    turns_ingested_total: int
    new_turns_ingested: int
    ingest_seconds: float
    query_seconds: float


@dataclass(frozen=True, slots=True)
class EpisodeBoundaryAudit:
    source_episode_id: str
    source_sha256: str
    public_sha256: str
    turn_count: int
    checkpoint_count: int
    dropped_episode_root_fields: tuple[str, ...]
    dropped_entity_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProtectedEpisodeResult:
    predictions: tuple[dict[str, Any], ...]
    episode_audit: EpisodeBoundaryAudit
    turn_audits: tuple[TurnBoundaryAudit, ...]
    checkpoint_audits: tuple[CheckpointBoundaryAudit, ...]


@dataclass(frozen=True, slots=True)
class ProtectedBenchmarkResult:
    predictions: tuple[dict[str, Any], ...]
    episode_audits: tuple[EpisodeBoundaryAudit, ...]
    turn_audits: tuple[TurnBoundaryAudit, ...]
    checkpoint_audits: tuple[CheckpointBoundaryAudit, ...]
    opaque_key_commitment_sha256: str
    opaque_mapping_commitment_sha256: str
    opaque_mapping_count: int


AgentFactory = Callable[[], PublicGateMemAgent]

_EPISODE_PUBLIC_ROOT_FIELDS = frozenset({"episode_id", "domain", "entities"})
_TURN_PUBLIC_ROOT_FIELDS = frozenset(
    {"turn_id", "timestamp", "speaker", "turn_kind", "text"}
)


def _required_identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GateMemBoundaryError(f"{field} must be a non-empty string")
    return value.strip()


def _root_fields_removed(
    raw: Mapping[str, Any], allowed: frozenset[str]
) -> tuple[str, ...]:
    return tuple(sorted(f"$.{key}" for key in set(raw) - allowed))


def _external_prediction_row(
    source_checkpoint_id: str,
    prediction: PublicPrediction,
) -> dict[str, Any]:
    """Restore the official source checkpoint identity after method return."""

    return {
        "checkpoint_id": source_checkpoint_id,
        "output": public_prediction_json(prediction),
    }


def _assert_source_ids_absent_from_method_output(
    prediction: PublicPrediction,
    source_ids: Sequence[str],
) -> None:
    payload = json.dumps(
        public_prediction_json(prediction),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).casefold()
    leaked = sorted(
        {
            source_id
            for source_id in source_ids
            if len(source_id) >= 4 and source_id.casefold() in payload
        }
    )
    if leaked:
        raise GateMemBoundaryError(
            "method output leaked source dataset identifiers: "
            + ", ".join(leaked)
        )


def run_protected_episode(
    *,
    agent: PublicGateMemAgent,
    episode: Mapping[str, Any],
    checkpoints: Sequence[Mapping[str, Any]],
    opaque_ids: GateMemOpaqueIds,
) -> ProtectedEpisodeResult:
    """Run one episode through an opaque, capability-reduced method boundary."""

    raw_episode = dict(episode)
    source_episode_id = _required_identifier(
        raw_episode.get("episode_id"), "episode_id"
    )
    public_episode: PublicEpisode = public_episode_from_raw(
        raw_episode,
        opaque_ids=opaque_ids,
    )

    turns_raw_value = raw_episode.get("turns") or []
    if not isinstance(turns_raw_value, Sequence) or isinstance(
        turns_raw_value, (str, bytes)
    ):
        raise GateMemBoundaryError("episode.turns must be a list")
    source_turn_ids: list[str] = []
    turns_public = []
    turn_audits: list[TurnBoundaryAudit] = []
    seen_source_turn_ids: set[str] = set()
    seen_method_turn_ids: set[str] = set()

    for index, value in enumerate(turns_raw_value):
        if not isinstance(value, Mapping):
            raise GateMemBoundaryError(f"episode.turns[{index}] must be an object")
        raw_turn = dict(value)
        source_turn_id = _required_identifier(raw_turn.get("turn_id"), "turn_id")
        if source_turn_id in seen_source_turn_ids:
            raise GateMemBoundaryError(
                f"duplicate turn_id in episode {source_episode_id}: {source_turn_id}"
            )
        seen_source_turn_ids.add(source_turn_id)
        public_turn = public_turn_from_raw(
            raw_turn,
            source_episode_id=source_episode_id,
            opaque_ids=opaque_ids,
        )
        if public_turn.turn_id in seen_method_turn_ids:
            raise GateMemBoundaryError("opaque method turn identifier collision")
        seen_method_turn_ids.add(public_turn.turn_id)
        source_turn_ids.append(source_turn_id)
        turns_public.append(public_turn)
        turn_audits.append(
            TurnBoundaryAudit(
                source_turn_id=source_turn_id,
                source_sha256=canonical_json_sha256(raw_turn),
                public_sha256=canonical_json_sha256(public_turn_json(public_turn)),
                removed_root_fields=_root_fields_removed(
                    raw_turn, _TURN_PUBLIC_ROOT_FIELDS
                ),
            )
        )

    turn_position = {
        source_turn_id: index for index, source_turn_id in enumerate(source_turn_ids)
    }

    checkpoint_rows: list[tuple[int, int, str, Mapping[str, Any]]] = []
    local_checkpoint_ids: set[str] = set()
    source_asker_ids: set[str] = set()
    for index, value in enumerate(checkpoints):
        if not isinstance(value, Mapping):
            raise GateMemBoundaryError(f"checkpoints[{index}] must be an object")
        raw_checkpoint = dict(value)
        source_checkpoint_id = _required_identifier(
            raw_checkpoint.get("checkpoint_id"),
            f"checkpoints[{index}].checkpoint_id",
        )
        if source_checkpoint_id in local_checkpoint_ids:
            raise GateMemBoundaryError(
                "duplicate checkpoint_id in episode "
                f"{source_episode_id}: {source_checkpoint_id}"
            )
        local_checkpoint_ids.add(source_checkpoint_id)
        checkpoint_episode = _required_identifier(
            raw_checkpoint.get("episode_id"), f"checkpoints[{index}].episode_id"
        )
        if checkpoint_episode != source_episode_id:
            raise GateMemBoundaryError(
                f"checkpoint {source_checkpoint_id} belongs to {checkpoint_episode}, "
                f"not active episode {source_episode_id}"
            )
        source_as_of = _required_identifier(
            raw_checkpoint.get("as_of_turn_id"),
            f"checkpoints[{index}].as_of_turn_id",
        )
        if source_as_of not in turn_position:
            raise GateMemBoundaryError(
                f"checkpoint {source_checkpoint_id} references unknown "
                f"as_of_turn_id: {source_as_of}"
            )
        asker = raw_checkpoint.get("asker") or {}
        if isinstance(asker, Mapping) and isinstance(asker.get("principal_id"), str):
            source_asker_ids.add(str(asker["principal_id"]))
        checkpoint_rows.append(
            (
                turn_position[source_as_of],
                index,
                source_checkpoint_id,
                raw_checkpoint,
            )
        )

    # Preserve GateMem's stable order for checkpoints at the same source turn.
    checkpoint_rows.sort(key=lambda item: (item[0], item[1]))

    session = GateMemPublicSession(public_episode)
    session.reset_agent(agent)
    ingested_upto = -1
    predictions: list[dict[str, Any]] = []
    checkpoint_audits: list[CheckpointBoundaryAudit] = []

    source_method_forbidden = (
        [source_episode_id]
        + source_turn_ids
        + sorted(local_checkpoint_ids)
        + sorted(source_asker_ids)
    )

    for target, _source_index, source_checkpoint_id, raw_checkpoint in checkpoint_rows:
        ingest_started = perf_counter()
        new_turns = 0
        for turn_index in range(ingested_upto + 1, target + 1):
            session.ingest_agent(agent, turns_public[turn_index])
            ingested_upto = turn_index
            new_turns += 1
        ingest_seconds = perf_counter() - ingest_started
        if ingested_upto != target:  # pragma: no cover - loop invariant
            raise AssertionError("outer runner failed exact source chronology")

        public_bundle = public_checkpoint_from_raw(
            raw_checkpoint,
            opaque_ids=opaque_ids,
        )
        query_started = perf_counter()
        prediction = session.query_agent(agent, public_bundle.checkpoint)
        query_seconds = perf_counter() - query_started
        _assert_source_ids_absent_from_method_output(
            prediction,
            source_method_forbidden,
        )

        prediction_row = _external_prediction_row(source_checkpoint_id, prediction)
        predictions.append(prediction_row)
        checkpoint_audits.append(
            CheckpointBoundaryAudit(
                source_checkpoint_id=source_checkpoint_id,
                source_episode_id=source_episode_id,
                source_as_of_turn_id=_required_identifier(
                    raw_checkpoint.get("as_of_turn_id"), "as_of_turn_id"
                ),
                source_sha256=public_bundle.source_sha256,
                public_sha256=public_bundle.public_sha256,
                removed_paths=public_bundle.removed_paths,
                prediction_sha256=canonical_json_sha256(prediction_row),
                turns_ingested_total=ingested_upto + 1,
                new_turns_ingested=new_turns,
                ingest_seconds=ingest_seconds,
                query_seconds=query_seconds,
            )
        )

    assert_prediction_coverage_complete(
        local_checkpoint_ids,
        (row["checkpoint_id"] for row in predictions),
    )

    entities = raw_episode.get("entities") or {}
    relationships_present = (
        isinstance(entities, Mapping) and bool(entities.get("relationships"))
    )
    episode_audit = EpisodeBoundaryAudit(
        source_episode_id=source_episode_id,
        source_sha256=canonical_json_sha256(raw_episode),
        public_sha256=canonical_json_sha256(public_episode_json(public_episode)),
        turn_count=len(turns_public),
        checkpoint_count=len(checkpoint_rows),
        dropped_episode_root_fields=_root_fields_removed(
            raw_episode, _EPISODE_PUBLIC_ROOT_FIELDS
        ),
        dropped_entity_paths=("$.entities.relationships",)
        if relationships_present
        else (),
    )
    return ProtectedEpisodeResult(
        predictions=tuple(predictions),
        episode_audit=episode_audit,
        turn_audits=tuple(turn_audits),
        checkpoint_audits=tuple(checkpoint_audits),
    )


def run_protected_benchmark(
    *,
    agent_factory: AgentFactory,
    episodes: Sequence[Mapping[str, Any]],
    checkpoints: Sequence[Mapping[str, Any]],
    opaque_id_secret: bytes | None = None,
) -> ProtectedBenchmarkResult:
    """Run the complete benchmark with a fresh opaque-ID key and agent per episode."""

    opaque_ids = (
        GateMemOpaqueIds.random()
        if opaque_id_secret is None
        else GateMemOpaqueIds.from_secret(opaque_id_secret)
    )
    episode_by_id: dict[str, Mapping[str, Any]] = {}
    for index, episode in enumerate(episodes):
        if not isinstance(episode, Mapping):
            raise GateMemBoundaryError(f"episodes[{index}] must be an object")
        source_episode_id = _required_identifier(
            episode.get("episode_id"), f"episodes[{index}].episode_id"
        )
        if source_episode_id in episode_by_id:
            raise GateMemBoundaryError(
                f"duplicate episode_id: {source_episode_id}"
            )
        episode_by_id[source_episode_id] = episode

    checkpoints_by_episode: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    checkpoint_counts: Counter[str] = Counter()
    for index, checkpoint in enumerate(checkpoints):
        if not isinstance(checkpoint, Mapping):
            raise GateMemBoundaryError(f"checkpoints[{index}] must be an object")
        source_checkpoint_id = _required_identifier(
            checkpoint.get("checkpoint_id"),
            f"checkpoints[{index}].checkpoint_id",
        )
        source_episode_id = _required_identifier(
            checkpoint.get("episode_id"), f"checkpoints[{index}].episode_id"
        )
        checkpoint_counts[source_checkpoint_id] += 1
        if source_episode_id not in episode_by_id:
            raise GateMemBoundaryError(
                f"checkpoint {source_checkpoint_id} references unknown episode: "
                f"{source_episode_id}"
            )
        checkpoints_by_episode[source_episode_id].append(checkpoint)

    duplicate_checkpoint_ids = tuple(
        sorted(
            identifier
            for identifier, count in checkpoint_counts.items()
            if count > 1
        )
    )
    if duplicate_checkpoint_ids:
        raise GateMemBoundaryError(
            "checkpoint identifiers must be globally unique: "
            + ", ".join(duplicate_checkpoint_ids)
        )

    predictions: list[dict[str, Any]] = []
    episode_audits: list[EpisodeBoundaryAudit] = []
    turn_audits: list[TurnBoundaryAudit] = []
    checkpoint_audits: list[CheckpointBoundaryAudit] = []

    for source_episode_id, episode in episode_by_id.items():
        episode_checkpoints = checkpoints_by_episode.get(source_episode_id, [])
        if not episode_checkpoints:
            continue
        agent = agent_factory()
        try:
            result = run_protected_episode(
                agent=agent,
                episode=episode,
                checkpoints=episode_checkpoints,
                opaque_ids=opaque_ids,
            )
        finally:
            close = getattr(agent, "close", None)
            if callable(close):
                close()
        predictions.extend(result.predictions)
        episode_audits.append(result.episode_audit)
        turn_audits.extend(result.turn_audits)
        checkpoint_audits.extend(result.checkpoint_audits)

    expected_ids = tuple(checkpoint_counts)
    assert_prediction_coverage_complete(
        expected_ids,
        (row["checkpoint_id"] for row in predictions),
    )
    return ProtectedBenchmarkResult(
        predictions=tuple(predictions),
        episode_audits=tuple(episode_audits),
        turn_audits=tuple(turn_audits),
        checkpoint_audits=tuple(checkpoint_audits),
        opaque_key_commitment_sha256=opaque_ids.key_commitment_sha256,
        opaque_mapping_commitment_sha256=opaque_ids.mapping_commitment_sha256(),
        opaque_mapping_count=opaque_ids.mapping_count,
    )
