#!/usr/bin/env python3
"""Lightweight reproduction of LongMemEval's official flat-BM25 retrieval arm.

The official runner imports CUDA and dense-retrieval dependencies even for
BM25. This runner preserves the official session corpus construction, BM25
tokenization/ranking, target derivation, exclusion rules, k values, and metric
formulae while emitting a compact audit artifact. It is a source-aligned
reproduction, not an official leaderboard submission.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np
from rank_bm25 import BM25Okapi


OFFICIAL_REPOSITORY = "https://github.com/xiaowu0162/LongMemEval"
OFFICIAL_COMMIT = "9e0b455f4ef0e2ab8f2e582289761153549043fc"
OFFICIAL_RUNNER_SHA256 = (
    "efd7fc5969a904717741fadca3c7dc73611ddbb2aaf3ef33117ebb6943b3e346"
)
OFFICIAL_EVAL_SHA256 = (
    "c98b8d1096877a15aa755c9de44fe33c195298466a2eb6f3c0f9f6bde8c72349"
)
K_VALUES = (1, 3, 5, 10, 30, 50)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dcg(relevances: list[int], k: int) -> float:
    """Exact formula from the pinned official eval_utils.py."""
    values = np.asfarray(relevances)[:k]
    if values.size:
        return float(
            values[0]
            + np.sum(values[1:] / np.log2(np.arange(2, values.size + 1)))
        )
    return 0.0


def evaluate_retrieval(
    rankings: np.ndarray, correct_docs: list[str], corpus_ids: list[str], k: int
) -> tuple[float, float, float]:
    """Exact metric semantics from the pinned official eval_utils.py."""
    recalled_docs = {corpus_ids[index] for index in rankings[:k]}
    recall_any = float(any(doc in recalled_docs for doc in correct_docs))
    recall_all = float(all(doc in recalled_docs for doc in correct_docs))
    relevances = [1 if doc_id in correct_docs else 0 for doc_id in corpus_ids]
    sorted_relevances = [relevances[index] for index in rankings[:k]]
    ideal_relevance = sorted(relevances, reverse=True)
    ideal_dcg = dcg(ideal_relevance, k)
    actual_dcg = dcg(sorted_relevances, k)
    ndcg_any = 0.0 if ideal_dcg == 0 else actual_dcg / ideal_dcg
    return recall_any, recall_all, float(ndcg_any)


def process_session(
    turns: list[dict[str, Any]], session_id: str
) -> tuple[str, str]:
    """Mirror official process_item_flat_index(..., granularity='session')."""
    user_turns = [turn for turn in turns if turn["role"] == "user"]
    text = " ".join(turn["content"] for turn in user_turns)
    corpus_id = session_id
    if "answer" in session_id and all(not turn["has_answer"] for turn in user_turns):
        corpus_id = session_id.replace("answer", "noans")
    return text, corpus_id


def has_target_user_turn(entry: dict[str, Any]) -> bool:
    return any(
        turn.get("has_answer") is True
        for session in entry["haystack_sessions"]
        for turn in session
        if turn["role"] == "user"
    )


def evaluate_entry(entry: dict[str, Any]) -> dict[str, Any]:
    corpus: list[str] = []
    corpus_ids: list[str] = []
    for session_id, session in zip(
        entry["haystack_session_ids"], entry["haystack_sessions"], strict=True
    ):
        text, corpus_id = process_session(session, session_id)
        corpus.append(text)
        corpus_ids.append(corpus_id)

    correct_docs = sorted({doc_id for doc_id in corpus_ids if "answer" in doc_id})
    bm25 = BM25Okapi([document.split(" ") for document in corpus])
    scores = bm25.get_scores(entry["question"].split(" "))
    rankings = np.argsort(scores)[::-1]

    row: dict[str, Any] = {
        "question_id": entry["question_id"],
        "question_type": entry["question_type"],
        "n_sessions": len(corpus),
        "n_target_sessions": len(correct_docs),
    }
    for k in K_VALUES:
        recall_any, recall_all, ndcg_any = evaluate_retrieval(
            rankings, correct_docs, corpus_ids, k
        )
        row[f"recall_any@{k}"] = recall_any
        row[f"recall_all@{k}"] = recall_all
        row[f"ndcg_any@{k}"] = ndcg_any
    return row


def run(input_path: Path, output_dir: Path) -> dict[str, Any]:
    with input_path.open(encoding="utf-8") as handle:
        entries = json.load(handle)

    ignored_abstention = sorted(
        entry["question_id"] for entry in entries if "_abs" in entry["question_id"]
    )
    ignored_no_target = sorted(
        entry["question_id"]
        for entry in entries
        if "_abs" not in entry["question_id"] and not has_target_user_turn(entry)
    )
    eligible = [
        entry
        for entry in entries
        if "_abs" not in entry["question_id"] and has_target_user_turn(entry)
    ]
    rows = [evaluate_entry(entry) for entry in eligible]

    metrics: dict[str, dict[str, float | int]] = {}
    for k in K_VALUES:
        any_values = [row[f"recall_any@{k}"] for row in rows]
        all_values = [row[f"recall_all@{k}"] for row in rows]
        ndcg_values = [row[f"ndcg_any@{k}"] for row in rows]
        metrics[str(k)] = {
            "recall_any_count": int(sum(any_values)),
            "recall_any_denominator": len(any_values),
            "recall_any": float(np.mean(any_values)),
            "recall_all_count": int(sum(all_values)),
            "recall_all_denominator": len(all_values),
            "recall_all": float(np.mean(all_values)),
            "ndcg_any_mean": float(np.mean(ndcg_values)),
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    row_path = output_dir / "retrieval_rows.csv"
    with row_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "experiment_id": "EXP-20260828-006",
        "status": "completed",
        "claim_boundary": (
            "source-aligned reproduction on official cleaned data; not an "
            "official leaderboard submission and not an end-to-end QA score"
        ),
        "official_repository": OFFICIAL_REPOSITORY,
        "official_commit": OFFICIAL_COMMIT,
        "official_runner_sha256": OFFICIAL_RUNNER_SHA256,
        "official_eval_sha256": OFFICIAL_EVAL_SHA256,
        "input_path": str(input_path),
        "input_sha256": sha256_file(input_path),
        "input_rows": len(entries),
        "eligible_rows": len(rows),
        "ignored_abstention_count": len(ignored_abstention),
        "ignored_no_target_count": len(ignored_no_target),
        "ignored_abstention_ids": ignored_abstention,
        "ignored_no_target_ids": ignored_no_target,
        "retriever": "flat-bm25",
        "granularity": "session",
        "tokenization": "Python str.split(' ') for corpus and query",
        "ranking": "numpy.argsort(scores)[::-1]",
        "rank_bm25_version": __import__("rank_bm25").__version__
        if hasattr(__import__("rank_bm25"), "__version__")
        else "0.2.2-pinned-environment",
        "numpy_version": np.__version__,
        "python_version": sys.version,
        "platform": platform.platform(),
        "metrics": metrics,
        "rows_path": str(row_path),
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    summary["rows_sha256"] = sha256_file(row_path)
    summary["summary_path"] = str(summary_path)
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output_dir), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
