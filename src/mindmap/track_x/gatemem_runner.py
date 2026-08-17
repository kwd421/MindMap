from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from .adapter_guard import (
    assert_prediction_coverage_complete,
    canonical_json_sha256,
)
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
    turn_id: str
    source_sha256: str
    public_sha256: str
    removed_root_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CheckpointBoundaryAudit:
    checkpoint_id: str
    episode_id: str
    as_of_turn_id: str
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
    episode_id: str
    source_sha256: str
    public_sha256: str
    turn_count: int
    checkpoint_count: int
    dropped_episode_root_fields: tuple[str, ...]


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


AgentFactory = Callable[[], PublicGateMemAgent]

_EPISODE_PUBLIC_ROOT_FIELDS = frozenset({"episode_id", "domain", "entities"})
_TURN_PUBLIC_ROOT_FIELDS = frozenset(
    {"turn_id", "timestamp", "speaker", "turn_kind", "text"}
)


def _required_identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GateMemBoundaryError(f"{field} must be a non-empty string")
    return value.strip()


def _root_fields_removed(raw: Mapping[str, Any], allowed: frozenset[str]) -> tuple[str, ...]:
    return tuple(sorted(f"$.{key}" for key in set(raw) - allowed))


def _external_prediction_row(
    checkpoint_id: str,
    prediction: PublicPrediction,
) -> dict[str, Any]:
    """Return GateMem's documented external-prediction shape.

    Hidden checkpoint annotations are deliberately not copied into this row.
    The official scorer joins them by ``checkpoint_id`` in its evaluator process.
    """

    return {
        "checkpoint_id": checkpoint_id,
        "output": public_prediction_json(prediction),
    }


def run_protected_episode(
    *,
    agent: PublicGateMemAgent,
    episode: Mapping[str, Any],
    checkpoints: Sequence[Mapping[str, Any]],
) -> ProtectedEpisodeResult:
    """Run one GateMem episode through capability-reduced public views.

    The method never receives the raw episode, raw checkpoint, future turns, gold
    record definitions, or scorer-only checkpoint attributes. Checkpoints are
    sorted by their as-of turn position, matching GateMem's native chronology.
    Unknown as-of turns are hard errors rather than silently skipped cases.
    """

    raw_episode = dict(episode)
    public_episode: PublicEpisode = public_episode_from_raw(raw_episode)
    episode_id = public_episode.episode_id

    turns_raw_value = raw_episode.get("turns") or []
    if not isinstance(turns_raw_value, Sequence) or isinstance(
        turns_raw_value, (str, bytes)
    ):
        raise GateMemBoundaryError("episode.turns must be a list")
    turns_raw: list[Mapping[str, Any]] = []
    turns_public = []
    turn_audits: list[TurnBoundaryAudit] = []
    seen_turn_ids: set[str] = set()

    for index, value in enumerate(turns_raw_value):
        if not isinstance(value, Mapping):
            raise GateMemBoundaryError(f"episode.turns[{index}] must be an object")
        raw_turn = dict(value)
        public_turn = public_turn_from_raw(raw_turn)
        if public_turn.turn_id in seen_turn_ids:
            raise GateMemBoundaryError(
                f"duplicate turn_id in episode {episode_id}: {public_turn.turn_id}"
            )
        seen_turn_ids.add(public_turn.turn_id)
        turns_raw.append(raw_turn)
        turns_public.append(public_turn)
        turn_audits.append(
            TurnBoundaryAudit(
                turn_id=public_turn.turn_id,
                source_sha256=canonical_json_sha256(raw_turn),
                public_sha256=canonical_json_sha256(public_turn_json(public_turn)),
                removed_root_fields=_root_fields_removed(
                    raw_turn, _TURN_PUBLIC_ROOT_FIELDS
                ),
            )
        )

    turn_position = {turn.turn_id: index for index, turn in enumerate(turns_public)}

    checkpoint_rows: list[tuple[int, str, Mapping[str, Any]]] = []
    local_checkpoint_ids: set[str] = set()
    for index, value in enumerate(checkpoints):
        if not isinstance(value, Mapping):
            raise GateMemBoundaryError(f"checkpoints[{index}] must be an object")
        raw_checkpoint = dict(value)
        checkpoint_id = _required_identifier(
            raw_checkpoint.get("checkpoint_id"), f"checkpoints[{index}].checkpoint_id"
        )
        if checkpoint_id in local_checkpoint_ids:
            raise GateMemBoundaryError(
                f"duplicate checkpoint_id in episode {episode_id}: {checkpoint_id}"
            )
        local_checkpoint_ids.add(checkpoint_id)
        checkpoint_episode = _required_identifier(
            raw_checkpoint.get("episode_id"), f"checkpoints[{index}].episode_id"
        )
        if checkpoint_episode != episode_id:
            raise GateMemBoundaryError(
                f"checkpoint {checkpoint_id} belongs to {checkpoint_episode}, "
                f"not active episode {episode_id}"
            )
        as_of = _required_identifier(
            raw_checkpoint.get("as_of_turn_id"),
            f"checkpoints[{index}].as_of_turn_id",
        )
        if as_of not in turn_position:
            raise GateMemBoundaryError(
                f"checkpoint {checkpoint_id} references unknown as_of_turn_id: {as_of}"
            )
        checkpoint_rows.append((turn_position[as_of], checkpoint_id, raw_checkpoint))

    checkpoint_rows.sort(key=lambda item: (item[0], item[1]))

    session = GateMemPublicSession(public_episode)
    session.reset_agent(agent)
    ingested_upto = -1
    predictions: list[dict[str, Any]] = []
    checkpoint_audits: list[CheckpointBoundaryAudit] = []

    for target, checkpoint_id, raw_checkpoint in checkpoint_rows:
        ingest_started = perf_counter()
        new_turns = 0
        for turn_index in range(ingested_upto + 1, target + 1):
            session.ingest_agent(agent, turns_public[turn_index])
            ingested_upto = turn_index
            new_turns += 1
        ingest_seconds = perf_counter() - ingest_started

        public_bundle = public_checkpoint_from_raw(raw_checkpoint)
        query_started = perf_counter()
        prediction = session.query_agent(agent, public_bundle.checkpoint)
        query_seconds = perf_counter() - query_started

        prediction_row = _external_prediction_row(checkpoint_id, prediction)
        predictions.append(prediction_row)
        checkpoint_audits.append(
            CheckpointBoundaryAudit(
                checkpoint_id=checkpoint_id,
                episode_id=episode_id,
                as_of_turn_id=public_bundle.checkpoint.as_of_turn_id,
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

    episode_audit = EpisodeBoundaryAudit(
        episode_id=episode_id,
        source_sha256=canonical_json_sha256(raw_episode),
        public_sha256=canonical_json_sha256(public_episode_json(public_episode)),
        turn_count=len(turns_public),
        checkpoint_count=len(checkpoint_rows),
        dropped_episode_root_fields=_root_fields_removed(
            raw_episode, _EPISODE_PUBLIC_ROOT_FIELDS
        ),
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
) -> ProtectedBenchmarkResult:
    """Run a complete GateMem-shaped benchmark with one fresh agent per episode."""

    episode_by_id: dict[str, Mapping[str, Any]] = {}
    for index, episode in enumerate(episodes):
        if not isinstance(episode, Mapping):
            raise GateMemBoundaryError(f"episodes[{index}] must be an object")
        episode_id = _required_identifier(
            episode.get("episode_id"), f"episodes[{index}].episode_id"
        )
        if episode_id in episode_by_id:
            raise GateMemBoundaryError(f"duplicate episode_id: {episode_id}")
        episode_by_id[episode_id] = episode

    checkpoints_by_episode: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    checkpoint_counts: Counter[str] = Counter()
    for index, checkpoint in enumerate(checkpoints):
        if not isinstance(checkpoint, Mapping):
            raise GateMemBoundaryError(f"checkpoints[{index}] must be an object")
        checkpoint_id = _required_identifier(
            checkpoint.get("checkpoint_id"), f"checkpoints[{index}].checkpoint_id"
        )
        episode_id = _required_identifier(
            checkpoint.get("episode_id"), f"checkpoints[{index}].episode_id"
        )
        checkpoint_counts[checkpoint_id] += 1
        if episode_id not in episode_by_id:
            raise GateMemBoundaryError(
                f"checkpoint {checkpoint_id} references unknown episode: {episode_id}"
            )
        checkpoints_by_episode[episode_id].append(checkpoint)

    duplicate_checkpoint_ids = tuple(
        sorted(identifier for identifier, count in checkpoint_counts.items() if count > 1)
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

    for episode_id, episode in episode_by_id.items():
        episode_checkpoints = checkpoints_by_episode.get(episode_id, [])
        if not episode_checkpoints:
            continue
        agent = agent_factory()
        result = run_protected_episode(
            agent=agent,
            episode=episode,
            checkpoints=episode_checkpoints,
        )
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
    )
