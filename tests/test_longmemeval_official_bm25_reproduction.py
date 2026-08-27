import importlib.util
from pathlib import Path

import pytest


pytest.importorskip("rank_bm25")


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "longmemeval_official_bm25_reproduction",
    ROOT / "experiments" / "longmemeval_official_bm25_reproduction.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_official_metric_retrieves_target_at_one():
    rankings = MODULE.np.array([1, 0, 2])
    recall_any, recall_all, ndcg_any = MODULE.evaluate_retrieval(
        rankings, ["answer_b"], ["filler_a", "answer_b", "filler_c"], 1
    )
    assert (recall_any, recall_all, ndcg_any) == (1.0, 1.0, 1.0)


def test_session_processing_marks_answer_free_decoy():
    text, corpus_id = MODULE.process_session(
        [{"role": "user", "content": "decoy", "has_answer": False}],
        "answer_example",
    )
    assert text == "decoy"
    assert corpus_id == "noans_example"


def test_target_detection_uses_user_turns_only():
    entry = {
        "haystack_sessions": [
            [
                {"role": "user", "content": "question", "has_answer": False},
                {"role": "assistant", "content": "answer", "has_answer": True},
            ]
        ]
    }
    assert MODULE.has_target_user_turn(entry) is False
