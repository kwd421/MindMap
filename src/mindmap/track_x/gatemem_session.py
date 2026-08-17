from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, Protocol

from .gatemem_public import (
    GateMemBoundaryError,
    PublicCheckpoint,
    PublicEpisode,
    PublicPrediction,
    PublicTurn,
    public_prediction_from_raw,
)


class PublicGateMemAgent(Protocol):
    """Method-side interface containing no evaluator-only checkpoint fields."""

    def reset(self, episode: PublicEpisode) -> None:
        ...

    def ingest(self, turn: PublicTurn) -> None:
        ...

    def query(self, checkpoint: PublicCheckpoint) -> Mapping[str, Any]:
        ...


def _clone_episode(value: PublicEpisode) -> PublicEpisode:
    return PublicEpisode(
        episode_id=value.episode_id,
        domain=value.domain,
        principals=tuple(value.principals),
        relationships=tuple(deepcopy(item) for item in value.relationships),
    )


class GateMemPublicSession:
    """Chronology and identity guard storing public objects only."""

    def __init__(self, episode: PublicEpisode) -> None:
        self.episode = _clone_episode(episode)
        self._turns: list[PublicTurn] = []
        self._turn_ids: set[str] = set()
        self._principal_roles = {
            principal.principal_id: principal.role for principal in self.episode.principals
        }

    @property
    def turns(self) -> tuple[PublicTurn, ...]:
        return tuple(self._turns)

    @property
    def last_turn_id(self) -> str | None:
        return self._turns[-1].turn_id if self._turns else None

    def ingest(self, turn: PublicTurn) -> None:
        if turn.turn_id in self._turn_ids:
            raise GateMemBoundaryError(f"duplicate ingested turn_id: {turn.turn_id}")
        known_role = self._principal_roles.get(turn.speaker_principal_id)
        if known_role is not None and known_role != turn.speaker_role:
            raise GateMemBoundaryError(
                "speaker role disagrees with episode principal metadata: "
                f"{turn.speaker_principal_id}"
            )
        self._turn_ids.add(turn.turn_id)
        self._turns.append(turn)

    def validate_checkpoint(self, checkpoint: PublicCheckpoint) -> None:
        if checkpoint.episode_id != self.episode.episode_id:
            raise GateMemBoundaryError("checkpoint belongs to a different episode")
        if self.last_turn_id != checkpoint.as_of_turn_id:
            raise GateMemBoundaryError(
                "checkpoint must be queried exactly after its as-of turn; "
                f"last={self.last_turn_id}, as_of={checkpoint.as_of_turn_id}"
            )
        known_role = self._principal_roles.get(checkpoint.asker_principal_id)
        if known_role is not None and known_role != checkpoint.asker_role:
            raise GateMemBoundaryError(
                "asker role disagrees with episode principal metadata: "
                f"{checkpoint.asker_principal_id}"
            )

    def requester_relationships(
        self, checkpoint: PublicCheckpoint
    ) -> tuple[dict[str, Any], ...]:
        self.validate_checkpoint(checkpoint)
        principal_id = checkpoint.asker_principal_id
        selected: list[dict[str, Any]] = []
        for relationship in self.episode.relationships:
            if any(
                key.endswith("_id") and value == principal_id
                for key, value in relationship.items()
                if isinstance(value, str)
            ):
                selected.append(deepcopy(relationship))
        return tuple(selected)

    def reset_agent(self, agent: PublicGateMemAgent) -> None:
        agent.reset(_clone_episode(self.episode))

    def ingest_agent(self, agent: PublicGateMemAgent, turn: PublicTurn) -> None:
        self.ingest(turn)
        agent.ingest(turn)

    def query_agent(
        self,
        agent: PublicGateMemAgent,
        checkpoint: PublicCheckpoint,
    ) -> PublicPrediction:
        self.validate_checkpoint(checkpoint)
        raw = agent.query(checkpoint)
        if not isinstance(raw, Mapping):
            raise GateMemBoundaryError("agent query output must be an object")
        return public_prediction_from_raw(raw)
