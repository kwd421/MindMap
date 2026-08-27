"""Canonical NCM-Ψ v0.2 S-track semantics.

The package contains three intentionally separate evaluators:

- :mod:`gold` — independent declarative reference semantics;
- :mod:`generic` — complete equal-information generic event ledger (G);
- :mod:`typed` — normalized typed projection (T).

Clean fixtures are expected to satisfy Gold = G = T exactly.
"""

from .model import (
    Answer,
    Attitude,
    Attribution,
    CommonEvent,
    EvaluationRow,
    ExpectedCase,
    Fixture,
    TargetQuery,
    TargetSpace,
    freeze_attrs,
    validate_temporal_references,
)

__all__ = [
    "Answer",
    "Attitude",
    "Attribution",
    "CommonEvent",
    "EvaluationRow",
    "ExpectedCase",
    "Fixture",
    "TargetQuery",
    "TargetSpace",
    "freeze_attrs",
    "validate_temporal_references",
]
