from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "longmemeval_deepseek_pilot", ROOT / "experiments" / "longmemeval_deepseek_pilot.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def row(question_id: str, question_type: str) -> dict:
    return {
        "question_id": question_id,
        "question_type": question_type,
        "question": "Where is the blue notebook?",
        "question_date": "2026-01-02",
        "answer": "on the desk",
        "haystack_dates": ["2026-01-01", "2026-01-02"],
        "haystack_session_ids": ["s1", "s2"],
        "haystack_sessions": [
            [{"role": "user", "content": "I bought a red pen."}],
            [{"role": "user", "content": "The blue notebook is on the desk."}],
        ],
    }


def test_bm25_ranks_matching_session_first() -> None:
    fixture = row("q", "single-session-user")
    ranked = MODULE.bm25_rank_sessions(
        fixture["question"], fixture["haystack_sessions"], top_k=1
    )
    assert ranked == [1]


def test_sample_selection_is_deterministic_and_stratified() -> None:
    rows = []
    for question_type in MODULE.QUESTION_TYPES:
        rows.append(row(f"{question_type}-a", question_type))
        rows.append(row(f"{question_type}-b", question_type))
    rows.append(row("knowledge-update-1_abs", "knowledge-update"))
    rows.append(row("multi-session-1_abs", "multi-session"))
    selected_a = MODULE.select_sample(rows, "seed")
    selected_b = MODULE.select_sample(list(reversed(rows)), "seed")
    assert [item["question_id"] for item in selected_a] == [
        item["question_id"] for item in selected_b
    ]
    assert len(selected_a) == 8
    assert sum("_abs" in item["question_id"] for item in selected_a) == 2


def test_usage_cost_separates_cache_hit_and_miss() -> None:
    usage = {
        "prompt_tokens": 150,
        "prompt_cache_hit_tokens": 100,
        "prompt_cache_miss_tokens": 50,
        "completion_tokens": 20,
    }
    expected = (100 * 0.007 + 50 * 0.22 + 20 * 0.66) / 1_000_000
    assert MODULE.usage_cost(usage, 0.007, 0.22, 0.66) == expected
