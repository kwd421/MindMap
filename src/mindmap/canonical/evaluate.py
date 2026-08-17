from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable

from .generic import GenericLedger
from .gold import GoldSemantics
from .model import EvaluationRow, Fixture
from .typed import TypedLedger


def evaluate_fixtures(fixtures: Iterable[Fixture]) -> list[EvaluationRow]:
    rows: list[EvaluationRow] = []
    for fixture in fixtures:
        gold = GoldSemantics(fixture.events)
        generic = GenericLedger(fixture.events)
        typed = TypedLedger(fixture.events)
        for case in fixture.cases:
            rows.append(
                EvaluationRow(
                    fixture_id=fixture.fixture_id,
                    family=fixture.family,
                    query_id=case.query.query_id,
                    target_space=case.query.target_space.value,
                    invariant=case.invariant,
                    expected=case.expected,
                    gold=gold.answer(case.query),
                    generic=generic.answer(case.query),
                    typed=typed.answer(case.query),
                )
            )
    return rows


def summarize(rows: Iterable[EvaluationRow]) -> dict[str, object]:
    materialized = list(rows)
    target_counts = Counter(row.target_space for row in materialized)
    failures = [row for row in materialized if not row.all_agree]
    by_implementation = {
        "gold": sum(row.gold_correct for row in materialized),
        "generic": sum(row.generic_correct for row in materialized),
        "typed": sum(row.typed_correct for row in materialized),
    }
    disagreement: dict[str, int] = defaultdict(int)
    for row in materialized:
        if row.gold != row.generic:
            disagreement["gold_vs_generic"] += 1
        if row.gold != row.typed:
            disagreement["gold_vs_typed"] += 1
        if row.generic != row.typed:
            disagreement["generic_vs_typed"] += 1
    return {
        "n_cases": len(materialized),
        "n_fixtures": len({row.fixture_id for row in materialized}),
        "target_counts": dict(sorted(target_counts.items())),
        "correct_counts": by_implementation,
        "disagreement_counts": dict(disagreement),
        "n_all_agree": sum(row.all_agree for row in materialized),
        "n_failures": len(failures),
        "failures": [
            {
                "fixture_id": row.fixture_id,
                "query_id": row.query_id,
                "target_space": row.target_space,
                "invariant": row.invariant,
                "expected": row.expected,
                "gold": row.gold,
                "generic": row.generic,
                "typed": row.typed,
            }
            for row in failures
        ],
    }
