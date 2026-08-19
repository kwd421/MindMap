from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import hmac
import json
import secrets
from typing import Final


_ID_HEX_LENGTH: Final = 32
_ALLOWED_NAMESPACES: Final = frozenset({"episode", "principal", "turn"})


class OpaqueIdError(ValueError):
    pass


@dataclass(slots=True)
class GateMemOpaqueIds:
    """Evaluator-owned one-way source-to-method identifier mapping.

    The secret and mapping object must never cross into the method subprocess,
    prompt, method audit, or scorer-facing prediction. Method IDs are scoped and
    non-sequential so public GateMem source IDs cannot reveal episode templates,
    principal identity, or turn position. Checkpoint IDs are not method
    capabilities at all; the evaluator rejoins them only after method return.
    """

    _secret: bytes = field(repr=False)
    _source_to_method: dict[tuple[str, str, str], str] = field(
        default_factory=dict, repr=False
    )
    _method_to_source: dict[str, tuple[str, str, str]] = field(
        default_factory=dict, repr=False
    )

    def __post_init__(self) -> None:
        if not isinstance(self._secret, bytes) or len(self._secret) < 16:
            raise OpaqueIdError("opaque-ID secret must contain at least 128 bits")

    @classmethod
    def random(cls) -> GateMemOpaqueIds:
        return cls(secrets.token_bytes(32))

    @classmethod
    def from_secret(cls, secret: bytes) -> GateMemOpaqueIds:
        return cls(bytes(secret))

    @property
    def key_commitment_sha256(self) -> str:
        return sha256(self._secret).hexdigest()

    @property
    def mapping_count(self) -> int:
        return len(self._source_to_method)

    def _digest(
        self,
        namespace: str,
        scope: str,
        source_id: str,
        counter: int,
    ) -> str:
        payload = json.dumps(
            [namespace, scope, source_id, counter],
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        return hmac.new(self._secret, payload, sha256).hexdigest()[:_ID_HEX_LENGTH]

    def method_id(
        self,
        namespace: str,
        source_id: str,
        *,
        scope: str = "global",
    ) -> str:
        if namespace not in _ALLOWED_NAMESPACES:
            raise OpaqueIdError(f"unsupported opaque-ID namespace: {namespace}")
        if not isinstance(source_id, str) or not source_id.strip():
            raise OpaqueIdError("source identifier must be a non-empty string")
        if not isinstance(scope, str) or not scope.strip():
            raise OpaqueIdError("opaque-ID scope must be a non-empty string")
        source_id = source_id.strip()
        scope = scope.strip()
        key = (namespace, scope, source_id)
        existing = self._source_to_method.get(key)
        if existing is not None:
            return existing

        counter = 0
        while True:
            candidate = f"{namespace}_{self._digest(namespace, scope, source_id, counter)}"
            # Avoid even accidental inclusion of meaningful source identifiers.
            # Very short source strings are excluded because any random digest
            # will commonly contain one-character substrings.
            contains_source = (
                len(source_id) >= 4
                and source_id.casefold() in candidate.casefold()
            )
            collision = self._method_to_source.get(candidate)
            if not contains_source and (collision is None or collision == key):
                break
            counter += 1
            if counter > 10_000:  # pragma: no cover - cryptographically implausible
                raise OpaqueIdError("failed to allocate a collision-free opaque ID")

        self._source_to_method[key] = candidate
        self._method_to_source[candidate] = key
        return candidate

    def episode(self, source_episode_id: str) -> str:
        return self.method_id("episode", source_episode_id)

    def principal(self, source_episode_id: str, source_principal_id: str) -> str:
        return self.method_id(
            "principal", source_principal_id, scope=source_episode_id
        )

    def turn(self, source_episode_id: str, source_turn_id: str) -> str:
        return self.method_id("turn", source_turn_id, scope=source_episode_id)

    def mapping_commitment_sha256(self) -> str:
        """Commit to the mapping without serializing source↔method pairs."""

        rows = [
            [namespace, scope, source_id, method_id]
            for (namespace, scope, source_id), method_id in sorted(
                self._source_to_method.items()
            )
        ]
        payload = json.dumps(
            rows,
            ensure_ascii=False,
            sort_keys=False,
            separators=(",", ":"),
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def source_identity_for_evaluator(
        self, method_id: str
    ) -> tuple[str, str, str] | None:
        """Evaluator-only reverse lookup; never serialize or pass to methods."""

        return self._method_to_source.get(method_id)
