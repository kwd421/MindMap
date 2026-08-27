#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

from mindmap.track_x.gatemem_opaque import GateMemOpaqueIds
from mindmap.track_x.gatemem_selective import audit_gate_mem_scores


FORBIDDEN_PUBLISHABLE_KEYS = frozenset(
    {
        "checkpoint_id",
        "episode_id",
        "turn_id",
        "principal_id",
        "asker",
        "query_text",
        "prompt_context",
        "prompt_items",
        "retrieval_items",
        "governance_items",
        "relationships",
        "records",
        "record_refs",
        "memory_ops",
        "judge_spec",
        "leak_targets",
        "as_of_turn_id",
    }
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _prediction_map(root: Path) -> dict[str, dict[str, Any]]:
    rows = _load_jsonl(root / "predictions.jsonl")
    output: dict[str, dict[str, Any]] = {}
    for row in rows:
        checkpoint_id = str(row["checkpoint_id"])
        if checkpoint_id in output:
            raise ValueError(f"duplicate prediction checkpoint: {checkpoint_id}")
        output[checkpoint_id] = row
    return output


def _regex_present(pattern: str, text: str) -> bool:
    try:
        return re.search(pattern, text, flags=re.IGNORECASE) is not None
    except re.error:
        return pattern.casefold() in text.casefold()


def _pattern_counts(patterns: Iterable[str], text: str) -> tuple[int, int]:
    materialized = tuple(str(pattern) for pattern in patterns)
    return len(materialized), sum(
        _regex_present(pattern, text) for pattern in materialized
    )


def _audit_text(row: Mapping[str, Any]) -> str:
    return str(row["output"]["memory_audit"]["prompt_context"]["text"])


def _retrieval_signature(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    return list(row["output"]["memory_audit"]["retrieval_items"])


def _prompt_turn_ids(row: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(
        str(item["turn_id"])
        for item in row["output"]["memory_audit"]["prompt_items"]
    )


def _governance_summary(row: Mapping[str, Any]) -> Mapping[str, Any]:
    return row["output"]["answer_structured"]["governance"]


def _walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _reader_runtime(root: Path) -> dict[str, Any]:
    payload = _load_json(root / "reader_runtime.json")
    return {
        "config": payload["config"],
        "stats": payload["stats"],
        "packages": payload["packages"],
        "sha256": _sha256(root / "reader_runtime.json"),
    }


def _method_summary(root: Path) -> dict[str, Any]:
    metadata = _load_json(root / "run_metadata.json")
    scores = _load_jsonl(root / "official_score" / "scores.jsonl")
    return {
        "official_summary": _load_json(
            root / "official_score" / "summary.json"
        ),
        "supplemental_selective": audit_gate_mem_scores(scores).to_json(),
        "method_config": metadata["method"]["config"],
        "artifact_sha256": metadata["artifact_sha256"],
        "run_metadata_sha256": _sha256(root / "run_metadata.json"),
        "official_summary_sha256": _sha256(
            root / "official_score" / "summary.json"
        ),
        "counts": metadata["counts"],
    }


def _expected_opaque_queries(
    checkpoints: Iterable[Mapping[str, Any]],
    secret: bytes,
) -> dict[str, Mapping[str, Any]]:
    opaque = GateMemOpaqueIds.from_secret(secret)
    output: dict[str, Mapping[str, Any]] = {}
    for checkpoint in checkpoints:
        method_id = opaque.query(
            str(checkpoint["episode_id"]),
            str(checkpoint["checkpoint_id"]),
        )
        output[method_id] = checkpoint
    return output


def build_publishable(
    *,
    checkout: Path,
    domain: str,
    secret: bytes,
    b1a_root: Path,
    b1b_root: Path,
    b2_root: Path,
) -> dict[str, Any]:
    checkpoints_path = (
        checkout / "bench" / "data" / domain / "checkpoints.jsonl"
    )
    checkpoints = _load_jsonl(checkpoints_path)
    hidden_by_opaque = _expected_opaque_queries(checkpoints, secret)
    predictions = {
        "B1a": _prediction_map(b1a_root),
        "B1b": _prediction_map(b1b_root),
        "B2": _prediction_map(b2_root),
    }
    expected_ids = set(hidden_by_opaque)
    for method, rows in predictions.items():
        if set(rows) != expected_ids:
            missing = len(expected_ids - set(rows))
            extra = len(set(rows) - expected_ids)
            raise ValueError(
                f"{method} checkpoint set mismatch: missing={missing}, extra={extra}"
            )

    retrieval_mismatches_b1b = 0
    retrieval_mismatches_b2 = 0
    prompt_mismatches_b1b = 0
    b2_prompt_subset_violations = 0
    governance_count_violations = 0

    utility_checkpoints = 0
    utility_required_patterns = 0
    b1a_required_patterns_present = 0
    b2_required_patterns_present = 0
    b1a_full_required_recall = 0
    b2_full_required_recall = 0
    false_blocking_checkpoints = 0

    privacy_checkpoints = 0
    deletion_checkpoints = 0
    privacy_leak_patterns = 0
    deletion_leak_patterns = 0
    b1a_privacy_prompt_exposure = 0
    b2_privacy_prompt_exposure = 0
    b1a_deletion_prompt_exposure = 0
    b2_deletion_prompt_exposure = 0
    b1a_privacy_exposed_checkpoints = 0
    b2_privacy_exposed_checkpoints = 0
    b1a_deletion_exposed_checkpoints = 0
    b2_deletion_exposed_checkpoints = 0

    candidate_count = 0
    admitted_count = 0
    blocked_count = 0
    b2_matched_signal_checkpoint_count = 0
    reason_counts: Counter[str] = Counter()

    for checkpoint_id, hidden in hidden_by_opaque.items():
        b1a = predictions["B1a"][checkpoint_id]
        b1b = predictions["B1b"][checkpoint_id]
        b2 = predictions["B2"][checkpoint_id]

        b1a_retrieval = _retrieval_signature(b1a)
        if b1a_retrieval != _retrieval_signature(b1b):
            retrieval_mismatches_b1b += 1
        if b1a_retrieval != _retrieval_signature(b2):
            retrieval_mismatches_b2 += 1

        b1a_text = _audit_text(b1a)
        if b1a_text != _audit_text(b1b):
            prompt_mismatches_b1b += 1
        b2_text = _audit_text(b2)

        b1a_candidate_ids = {
            str(item["turn_id"]) for item in b1a_retrieval
        }
        b2_prompt_ids = set(_prompt_turn_ids(b2))
        if not b2_prompt_ids.issubset(b1a_candidate_ids):
            b2_prompt_subset_violations += 1

        governance = _governance_summary(b2)
        candidate_count += int(governance["candidate_count"])
        admitted_count += int(governance["admitted_count"])
        blocked_count += int(governance["blocked_count"])
        if int(governance["admitted_count"]) + int(
            governance["blocked_count"]
        ) != int(governance["candidate_count"]):
            governance_count_violations += 1

        matched_signal = False
        for item in b2["output"]["memory_audit"]["governance_items"]:
            for reason in item["reason_codes"]:
                reason_counts[str(reason)] += 1
            if item["matched_signal_ids"]:
                matched_signal = True
        if matched_signal:
            b2_matched_signal_checkpoint_count += 1

        query_type = str(hidden["query_type"])
        if query_type == "utility":
            utility_checkpoints += 1
            patterns = hidden.get("judge_spec", {}).get("include", [])
            total, b1a_present = _pattern_counts(patterns, b1a_text)
            _, b2_present = _pattern_counts(patterns, b2_text)
            utility_required_patterns += total
            b1a_required_patterns_present += b1a_present
            b2_required_patterns_present += b2_present
            if total > 0 and b1a_present == total:
                b1a_full_required_recall += 1
            if total > 0 and b2_present == total:
                b2_full_required_recall += 1
            if total > 0 and b1a_present == total and b2_present < total:
                false_blocking_checkpoints += 1
        elif query_type in {"privacy", "safety", "deletion"}:
            patterns = hidden.get("leak_targets", [])
            total, b1a_present = _pattern_counts(patterns, b1a_text)
            _, b2_present = _pattern_counts(patterns, b2_text)
            if query_type == "privacy":
                privacy_checkpoints += 1
                privacy_leak_patterns += total
                b1a_privacy_prompt_exposure += b1a_present
                b2_privacy_prompt_exposure += b2_present
                b1a_privacy_exposed_checkpoints += b1a_present > 0
                b2_privacy_exposed_checkpoints += b2_present > 0
            else:
                deletion_checkpoints += 1
                deletion_leak_patterns += total
                b1a_deletion_prompt_exposure += b1a_present
                b2_deletion_prompt_exposure += b2_present
                b1a_deletion_exposed_checkpoints += b1a_present > 0
                b2_deletion_exposed_checkpoints += b2_present > 0

    if retrieval_mismatches_b1b or retrieval_mismatches_b2:
        raise ValueError("B1a/B1b/B2 retrieval candidates are not identical")
    if prompt_mismatches_b1b:
        raise ValueError("B1a/B1b prompts are not identical")
    if b2_prompt_subset_violations:
        raise ValueError("B2 prompt contains a turn outside the B1a top-k set")
    if governance_count_violations:
        raise ValueError("B2 governance counts are inconsistent")

    b1a_metadata = _load_json(b1a_root / "run_metadata.json")
    b1b_metadata = _load_json(b1b_root / "run_metadata.json")
    b2_metadata = _load_json(b2_root / "run_metadata.json")
    checkout_identity = b1a_metadata["checkout"]
    if (
        checkout_identity != b1b_metadata["checkout"]
        or checkout_identity != b2_metadata["checkout"]
    ):
        raise ValueError("paired methods used different GateMem checkout identities")

    publishable = {
        "schema_version": "track-x-gatemem-b2-paired-result-v0.1",
        "classification": (
            "official deterministic B1a/B1b/B2 endpoint mechanism comparison; "
            "not a MindMap, typed-ledger, leaderboard, or production result"
        ),
        "domain": domain,
        "gatemem_revision": checkout_identity["observed_commit"],
        "scorer_sha256": checkout_identity["scorer_sha256"],
        "episodes_sha256": checkout_identity["episodes_sha256"],
        "checkpoints_sha256": checkout_identity["checkpoints_sha256"],
        "checkpoint_count": len(checkpoints),
        "pairing": {
            "retrieval_mismatches_B1a_B1b": retrieval_mismatches_b1b,
            "retrieval_mismatches_B1a_B2": retrieval_mismatches_b2,
            "prompt_mismatches_B1a_B1b": prompt_mismatches_b1b,
            "B2_prompt_subset_violations": b2_prompt_subset_violations,
            "governance_count_violations": governance_count_violations,
        },
        "stage_metrics": {
            "utility": {
                "checkpoint_count": utility_checkpoints,
                "required_pattern_count": utility_required_patterns,
                "B1a_required_patterns_present": b1a_required_patterns_present,
                "B2_required_patterns_present": b2_required_patterns_present,
                "B1a_full_required_recall_checkpoints": (
                    b1a_full_required_recall
                ),
                "B2_full_required_recall_checkpoints": b2_full_required_recall,
                "false_blocking_checkpoints": false_blocking_checkpoints,
            },
            "privacy": {
                "checkpoint_count": privacy_checkpoints,
                "leak_pattern_count": privacy_leak_patterns,
                "B1a_prompt_exposed_patterns": b1a_privacy_prompt_exposure,
                "B2_prompt_exposed_patterns": b2_privacy_prompt_exposure,
                "B1a_prompt_exposed_checkpoints": (
                    b1a_privacy_exposed_checkpoints
                ),
                "B2_prompt_exposed_checkpoints": (
                    b2_privacy_exposed_checkpoints
                ),
            },
            "deletion": {
                "checkpoint_count": deletion_checkpoints,
                "leak_pattern_count": deletion_leak_patterns,
                "B1a_prompt_exposed_patterns": b1a_deletion_prompt_exposure,
                "B2_prompt_exposed_patterns": b2_deletion_prompt_exposure,
                "B1a_prompt_exposed_checkpoints": (
                    b1a_deletion_exposed_checkpoints
                ),
                "B2_prompt_exposed_checkpoints": (
                    b2_deletion_exposed_checkpoints
                ),
            },
            "governance": {
                "candidate_count": candidate_count,
                "admitted_count": admitted_count,
                "blocked_count": blocked_count,
                "B2_matched_signal_checkpoint_count": (
                    b2_matched_signal_checkpoint_count
                ),
                "reason_counts": dict(sorted(reason_counts.items())),
            },
        },
        "methods": {
            "B1a_raw_lexical_context_echo": _method_summary(b1a_root),
            "B1b_raw_lexical_shared_reader": {
                **_method_summary(b1b_root),
                "reader_runtime": _reader_runtime(b1b_root),
            },
            "B2_public_text_governed_reader": {
                **_method_summary(b2_root),
                "reader_runtime": _reader_runtime(b2_root),
            },
        },
        "metric_namespaces": {
            "official_summary": (
                "Unmodified pinned GateMem deterministic scorer."
            ),
            "supplemental_selective": (
                "MindMap answered-denominator audit; does not replace official metrics."
            ),
            "stage_metrics": (
                "Evaluator-side aggregate join using hidden labels after method "
                "execution; hidden inputs never cross the method boundary."
            ),
        },
        "interpretation_boundary": (
            "B2 uses a retrospective same-speaker public-text heuristic with "
            "unknown-admit, no relationships or authenticated policy capability, "
            "no candidate backfill, and whole-turn directive exclusion. "
            "B2_matched_signal_checkpoint_count is method-dependent coverage, "
            "not a method-independent identifiability estimand."
        ),
    }
    leaked = set(_walk_keys(publishable)) & FORBIDDEN_PUBLISHABLE_KEYS
    if leaked:
        raise ValueError(
            f"publishable B2 aggregate contains forbidden keys: {sorted(leaked)}"
        )
    return publishable


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gatemem-checkout", type=Path, required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--opaque-id-secret-file", type=Path, required=True)
    parser.add_argument("--b1a-dir", type=Path, required=True)
    parser.add_argument("--b1b-dir", type=Path, required=True)
    parser.add_argument("--b2-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    secret = args.opaque_id_secret_file.read_bytes()
    if len(secret) < 16:
        raise ValueError("opaque-ID secret file must contain at least 128 bits")
    publishable = build_publishable(
        checkout=args.gatemem_checkout.resolve(),
        domain=args.domain,
        secret=secret,
        b1a_root=args.b1a_dir.resolve(),
        b1b_root=args.b1b_dir.resolve(),
        b2_root=args.b2_dir.resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(publishable, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"output={args.output}")
    print(f"checkpoint_count={publishable['checkpoint_count']}")
    print(
        "B2_blocked_count="
        f"{publishable['stage_metrics']['governance']['blocked_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
