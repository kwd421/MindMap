from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Final, TypeAlias

PathComponent: TypeAlias = str | int
JSONPath: TypeAlias = tuple[PathComponent, ...]
_WILDCARD: Final[str] = "*"
_REMOVED: Final[object] = object()


@dataclass(frozen=True, slots=True)
class HiddenPathRule:
    """A small, auditable JSON-path subset used at benchmark boundaries.

    Each token is either an exact mapping key or ``"*"``. A wildcard matches
    one mapping key or one sequence index. Recursive descent is deliberately
    unsupported: benchmark adapters must enumerate the paths they hide.
    """

    pattern: tuple[str, ...]
    label: str

    def __post_init__(self) -> None:
        if not self.pattern:
            raise ValueError("hidden-path patterns must not be empty")
        if any(not isinstance(token, str) or not token for token in self.pattern):
            raise ValueError("hidden-path tokens must be non-empty strings")
        if not self.label.strip():
            raise ValueError("hidden-path labels must not be empty")

    def matches(self, path: JSONPath) -> bool:
        if len(path) != len(self.pattern):
            return False
        return all(
            token == _WILDCARD or (isinstance(component, str) and token == component)
            for token, component in zip(self.pattern, path, strict=True)
        )


@dataclass(frozen=True, slots=True)
class HiddenPathHit:
    path: str
    labels: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RedactionResult:
    payload: Any
    hits: tuple[HiddenPathHit, ...]
    source_sha256: str
    payload_sha256: str

    @property
    def removed_paths(self) -> tuple[str, ...]:
        return tuple(hit.path for hit in self.hits)


@dataclass(frozen=True, slots=True)
class PredictionCoverage:
    expected_count: int
    observed_count: int
    unique_observed_count: int
    missing_ids: tuple[str, ...]
    unexpected_ids: tuple[str, ...]
    duplicate_ids: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return not (self.missing_ids or self.unexpected_ids or self.duplicate_ids)


class HiddenAnnotationError(ValueError):
    pass


class PredictionCoverageError(ValueError):
    pass


def canonical_json_sha256(value: Any) -> str:
    """Hash a JSON value with a stable, UTF-8 canonical serialization."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _format_path(path: JSONPath) -> str:
    rendered = "$"
    for component in path:
        if isinstance(component, int):
            rendered += f"[{component}]"
        elif component.isidentifier():
            rendered += f".{component}"
        else:
            rendered += "[" + json.dumps(component, ensure_ascii=False) + "]"
    return rendered


def _matching_labels(path: JSONPath, rules: Sequence[HiddenPathRule]) -> tuple[str, ...]:
    return tuple(sorted({rule.label for rule in rules if rule.matches(path)}))


def scan_hidden_annotations(
    payload: Any,
    rules: Sequence[HiddenPathRule],
) -> tuple[HiddenPathHit, ...]:
    """Return every hidden annotation path still present in ``payload``."""

    hits: list[HiddenPathHit] = []

    def visit(node: Any, path: JSONPath) -> None:
        labels = _matching_labels(path, rules)
        if labels:
            hits.append(HiddenPathHit(_format_path(path), labels))
            return
        if isinstance(node, Mapping):
            for key, value in node.items():
                if not isinstance(key, str):
                    raise TypeError("benchmark JSON objects must use string keys")
                visit(value, path + (key,))
        elif isinstance(node, (list, tuple)):
            for index, value in enumerate(node):
                visit(value, path + (index,))

    visit(payload, ())
    return tuple(sorted(hits, key=lambda hit: hit.path))


def strip_hidden_annotations(
    payload: Any,
    rules: Sequence[HiddenPathRule],
) -> RedactionResult:
    """Return a non-mutating redaction plus an auditable removal manifest."""

    source_digest = canonical_json_sha256(payload)
    hits: list[HiddenPathHit] = []

    def copy_without_hidden(node: Any, path: JSONPath) -> Any:
        labels = _matching_labels(path, rules)
        if labels:
            hits.append(HiddenPathHit(_format_path(path), labels))
            return _REMOVED

        if isinstance(node, Mapping):
            output: dict[str, Any] = {}
            for key, value in node.items():
                if not isinstance(key, str):
                    raise TypeError("benchmark JSON objects must use string keys")
                copied = copy_without_hidden(value, path + (key,))
                if copied is not _REMOVED:
                    output[key] = copied
            return output

        if isinstance(node, list):
            output_list: list[Any] = []
            for index, value in enumerate(node):
                copied = copy_without_hidden(value, path + (index,))
                if copied is not _REMOVED:
                    output_list.append(copied)
            return output_list

        if isinstance(node, tuple):
            output_tuple: list[Any] = []
            for index, value in enumerate(node):
                copied = copy_without_hidden(value, path + (index,))
                if copied is not _REMOVED:
                    output_tuple.append(copied)
            return tuple(output_tuple)

        return node

    clean = copy_without_hidden(payload, ())
    if clean is _REMOVED:
        raise ValueError("a benchmark adapter may not redact the document root")
    ordered_hits = tuple(sorted(hits, key=lambda hit: hit.path))
    return RedactionResult(
        payload=clean,
        hits=ordered_hits,
        source_sha256=source_digest,
        payload_sha256=canonical_json_sha256(clean),
    )


def assert_hidden_annotations_absent(
    payload: Any,
    rules: Sequence[HiddenPathRule],
) -> None:
    hits = scan_hidden_annotations(payload, rules)
    if not hits:
        return
    details = ", ".join(
        f"{hit.path} ({'/'.join(hit.labels)})" for hit in hits
    )
    raise HiddenAnnotationError(f"hidden benchmark annotations remain: {details}")


def prediction_coverage(
    expected_ids: Iterable[str],
    observed_ids: Iterable[str],
) -> PredictionCoverage:
    expected = tuple(expected_ids)
    observed = tuple(observed_ids)
    if any(not isinstance(value, str) or not value.strip() for value in expected + observed):
        raise ValueError("prediction identifiers must be non-empty strings")

    expected_counts = Counter(expected)
    duplicated_expected = sorted(key for key, count in expected_counts.items() if count > 1)
    if duplicated_expected:
        raise ValueError(
            "expected benchmark identifiers are not unique: "
            + ", ".join(duplicated_expected)
        )

    observed_counts = Counter(observed)
    expected_set = set(expected)
    observed_set = set(observed)
    return PredictionCoverage(
        expected_count=len(expected),
        observed_count=len(observed),
        unique_observed_count=len(observed_set),
        missing_ids=tuple(sorted(expected_set - observed_set)),
        unexpected_ids=tuple(sorted(observed_set - expected_set)),
        duplicate_ids=tuple(
            sorted(key for key, count in observed_counts.items() if count > 1)
        ),
    )


def assert_prediction_coverage_complete(
    expected_ids: Iterable[str],
    observed_ids: Iterable[str],
) -> PredictionCoverage:
    report = prediction_coverage(expected_ids, observed_ids)
    if report.complete:
        return report
    raise PredictionCoverageError(
        "incomplete prediction coverage: "
        f"missing={list(report.missing_ids)}, "
        f"unexpected={list(report.unexpected_ids)}, "
        f"duplicates={list(report.duplicate_ids)}"
    )
