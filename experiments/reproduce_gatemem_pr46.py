#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable


DOMAINS = ("education", "household", "medical", "office")
METHODS = ("always_no_memory", "raw_lexical")
EXPECTED_GATEMEM_COMMIT = (
    "603f9f4b4ba4b77f043c20f85687fa016fd720b0"
)
EXPECTED_SCORER_SHA256 = (
    "3d546a21778202959a9df12bac44c196a7f20a248cf5a2cb34f0d9b9c2623d8a"
)
EXPECTED_REFERENCE_ROWS_SHA256 = (
    "8d17aa6915f02e6abbc2f1c7b50410996ca354c2f177cec46c2cc5cfcd789212"
)
EXPECTED_DATA_HASHES = {
    "education": {
        "episodes_sha256": (
            "5971478a96553c2eb18a9f1e079987275da0cddf6175e40abda8a58525e65862"
        ),
        "checkpoints_sha256": (
            "2a372a5017a99108c83324d2fed25dbfb7797a2fb25a20fc066ed5b2d05739b5"
        ),
    },
    "household": {
        "episodes_sha256": (
            "e2bb506cc1bdc8dc7b16d4a57610147365798d03eb1c326f9197b6c6221efb6f"
        ),
        "checkpoints_sha256": (
            "4692c3e1ea91be63debd7b39ccc5fc425bc1a83155c1bfb5c197ba68cefd93ae"
        ),
    },
    "medical": {
        "episodes_sha256": (
            "d4b01f62cbd3457715b5958cf2d07d496c6e59280d28041927e2b3ab8a444b9f"
        ),
        "checkpoints_sha256": (
            "2447f5905081e6002f16ad14f7f7dc19e14b7181e5ac8ebd08144d68da6437a0"
        ),
    },
    "office": {
        "episodes_sha256": (
            "e15797cc0ab778067e0235377a09811c73182b5e1aa28e2221adc5ef9638a409"
        ),
        "checkpoints_sha256": (
            "7186bc1dd66b493f994b802bad8817d7aa5e7a91f498d67f87410a98f8116d0c"
        ),
    },
}
INTEGER_FIELDS = (
    "n_checkpoints",
    "n_utility",
    "n_privacy",
    "n_safety",
    "opaque_mapping_count",
)
FLOAT_FIELDS = (
    "action_accuracy",
    "utility_accuracy",
    "privacy_answer_leakage_rate",
    "privacy_context_leakage_rate",
    "privacy_e2e_leakage_rate",
    "deletion_answer_leakage_rate",
    "deletion_context_leakage_rate",
    "deletion_e2e_leakage_rate",
    "over_refusal_rate",
    "compliance_utility_score",
    "compliance_utility_e2e_score",
)
BOOLEAN_FIELDS = ("gated_by_action",)
ROW_FIELDS = (
    "domain",
    "method",
    *INTEGER_FIELDS[:-1],
    *FLOAT_FIELDS,
    *BOOLEAN_FIELDS,
    "opaque_mapping_count",
)
FALSE_BOUNDARY_FIELDS = (
    "hidden_checkpoint_fields_passed_to_method",
    "memory_ops_passed_to_method",
    "official_scorer_modified",
    "record_refs_passed_to_method",
    "relationships_passed_to_method",
    "source_as_of_turn_id_passed_to_method",
    "source_identifiers_passed_to_method",
)
OFFICIAL_SCORE_FILES = (
    "predictions.normalized.jsonl",
    "scores.jsonl",
    "summary.json",
)


@dataclass(frozen=True, slots=True)
class RunRecord:
    replicate: int
    domain: str
    method: str
    row: dict[str, Any]
    official_summary: dict[str, Any]
    predictions_sha256: str
    opaque_key_commitment_sha256: str
    opaque_mapping_commitment_sha256: str
    repository_revision: str | None
    run_metadata_sha256: str
    official_summary_sha256: str
    episodes_sha256: str
    checkpoints_sha256: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout.strip()


def _count_jsonl(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                json.loads(line)
                count += 1
    return count


def _bool_from_csv(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    raise ValueError(f"invalid boolean value: {value!r}")


def _read_reference_rows(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    if _sha256(path) != EXPECTED_REFERENCE_ROWS_SHA256:
        raise RuntimeError(
            "reference rows hash mismatch: "
            f"{_sha256(path)} != {EXPECTED_REFERENCE_ROWS_SHA256}"
        )
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != ROW_FIELDS:
            raise RuntimeError(
                "reference row columns changed: "
                f"{reader.fieldnames!r} != {ROW_FIELDS!r}"
            )
        for raw in reader:
            key = (raw["domain"], raw["method"])
            if key in rows:
                raise RuntimeError(f"duplicate reference row: {key}")
            row: dict[str, Any] = {
                "domain": raw["domain"],
                "method": raw["method"],
            }
            for field in INTEGER_FIELDS:
                row[field] = int(raw[field])
            for field in FLOAT_FIELDS:
                row[field] = Decimal(raw[field])
            for field in BOOLEAN_FIELDS:
                row[field] = _bool_from_csv(raw[field])
            rows[key] = row
    expected_keys = {
        (domain, method)
        for domain in DOMAINS
        for method in METHODS
    }
    if set(rows) != expected_keys:
        raise RuntimeError(
            f"reference row keys changed: {sorted(rows)} != {sorted(expected_keys)}"
        )
    return rows


def _actual_row(
    *,
    domain: str,
    method: str,
    metadata: dict[str, Any],
    summary: dict[str, Any],
) -> dict[str, Any]:
    opaque = metadata.get("opaque_identity_firewall") or {}
    row: dict[str, Any] = {
        "domain": domain,
        "method": method,
        "opaque_mapping_count": int(opaque["mapping_count"]),
    }
    for field in INTEGER_FIELDS[:-1]:
        row[field] = int(summary[field])
    for field in FLOAT_FIELDS:
        row[field] = Decimal(str(summary[field]))
    for field in BOOLEAN_FIELDS:
        row[field] = bool(summary[field])
    return row


def _assert_row_matches(
    actual: dict[str, Any],
    reference: dict[str, Any],
) -> None:
    mismatches: list[str] = []
    for field in ROW_FIELDS:
        if actual[field] != reference[field]:
            mismatches.append(
                f"{field}: actual={actual[field]!r} "
                f"reference={reference[field]!r}"
            )
    if mismatches:
        raise RuntimeError(
            "official endpoint row mismatch for "
            f"{actual['domain']}/{actual['method']}:\n"
            + "\n".join(mismatches)
        )


def _json_safe_row(row: dict[str, Any]) -> dict[str, Any]:
    converted: dict[str, Any] = {}
    for field in ROW_FIELDS:
        value = row[field]
        converted[field] = float(value) if isinstance(value, Decimal) else value
    return converted


def _write_rows_csv(
    path: Path,
    rows: Iterable[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROW_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(_json_safe_row(row))


def _run_endpoint(
    *,
    replicate: int,
    domain: str,
    method: str,
    mindmap_root: Path,
    gatemem_root: Path,
    output_root: Path,
    reference: dict[str, Any],
) -> RunRecord:
    protected_dir = (
        output_root
        / "protected"
        / f"replicate-{replicate}"
        / domain
        / method
    )
    if protected_dir.exists():
        raise RuntimeError(f"output directory already exists: {protected_dir}")
    protected_dir.parent.mkdir(parents=True, exist_ok=True)

    log_dir = output_root / "logs" / f"replicate-{replicate}"
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = log_dir / f"{domain}-{method}.stdout.log"
    stderr_path = log_dir / f"{domain}-{method}.stderr.log"

    command = [
        sys.executable,
        str(mindmap_root / "experiments" / "gatemem_external.py"),
        "--gatemem-checkout",
        str(gatemem_root),
        "--domain",
        domain,
        "--method",
        method,
        "--output-dir",
        str(protected_dir),
        "--expected-gatemem-commit",
        EXPECTED_GATEMEM_COMMIT,
    ]
    completed = subprocess.run(
        command,
        cwd=mindmap_root,
        text=True,
        capture_output=True,
        env=os.environ.copy(),
    )
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(
            f"endpoint command failed ({completed.returncode}) for "
            f"replicate {replicate} {domain}/{method}; "
            f"see {stdout_path} and {stderr_path}"
        )

    metadata_path = protected_dir / "run_metadata.json"
    summary_path = protected_dir / "official_score" / "summary.json"
    predictions_path = protected_dir / "predictions.jsonl"
    for path in (metadata_path, summary_path, predictions_path):
        if not path.is_file():
            raise RuntimeError(f"missing endpoint artifact: {path}")
    for filename in OFFICIAL_SCORE_FILES:
        path = protected_dir / "official_score" / filename
        if not path.is_file():
            raise RuntimeError(f"missing official scorer artifact: {path}")
    if (protected_dir / "official_score" / "per_checkpoint.jsonl").exists():
        raise RuntimeError(
            "unexpected legacy scorer filename per_checkpoint.jsonl"
        )

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    observed_checkout = metadata["checkout"]["observed_commit"]
    if observed_checkout != EXPECTED_GATEMEM_COMMIT:
        raise RuntimeError(
            f"GateMem revision mismatch: {observed_checkout}"
        )
    observed_scorer = metadata["checkout"]["scorer_sha256"]
    if observed_scorer != EXPECTED_SCORER_SHA256:
        raise RuntimeError(
            f"official scorer hash mismatch: {observed_scorer}"
        )
    expected_hashes = EXPECTED_DATA_HASHES[domain]
    for field, expected in expected_hashes.items():
        observed = metadata["checkout"][field]
        if observed != expected:
            raise RuntimeError(
                f"{domain} {field} mismatch: {observed} != {expected}"
            )

    boundary = metadata["boundary"]
    bad_boundary = {
        field: boundary.get(field)
        for field in FALSE_BOUNDARY_FIELDS
        if boundary.get(field) is not False
    }
    if bad_boundary:
        raise RuntimeError(
            f"protected-boundary regression for {domain}/{method}: "
            f"{bad_boundary}"
        )
    opaque = metadata["opaque_identity_firewall"]
    if opaque.get("enabled") is not True:
        raise RuntimeError("opaque identity firewall is not enabled")
    if opaque.get("mapping_serialized") is not False:
        raise RuntimeError("opaque mapping was serialized")

    prediction_count = _count_jsonl(predictions_path)
    normalized_count = _count_jsonl(
        protected_dir
        / "official_score"
        / "predictions.normalized.jsonl"
    )
    score_count = _count_jsonl(
        protected_dir / "official_score" / "scores.jsonl"
    )
    checkpoint_count = int(summary["n_checkpoints"])
    if not (
        prediction_count
        == normalized_count
        == score_count
        == checkpoint_count
        == int(metadata["counts"]["predictions"])
        == int(metadata["counts"]["checkpoints"])
    ):
        raise RuntimeError(
            "checkpoint coverage mismatch for "
            f"{domain}/{method}: predictions={prediction_count}, "
            f"normalized={normalized_count}, scores={score_count}, "
            f"summary={checkpoint_count}, metadata={metadata['counts']}"
        )

    predictions_sha256 = _sha256(predictions_path)
    metadata_prediction_hash = metadata["artifact_sha256"][
        "predictions.jsonl"
    ]
    if predictions_sha256 != metadata_prediction_hash:
        raise RuntimeError(
            "prediction artifact hash mismatch: "
            f"{predictions_sha256} != {metadata_prediction_hash}"
        )

    actual = _actual_row(
        domain=domain,
        method=method,
        metadata=metadata,
        summary=summary,
    )
    _assert_row_matches(actual, reference)

    return RunRecord(
        replicate=replicate,
        domain=domain,
        method=method,
        row=actual,
        official_summary=summary,
        predictions_sha256=predictions_sha256,
        opaque_key_commitment_sha256=opaque[
            "key_commitment_sha256"
        ],
        opaque_mapping_commitment_sha256=opaque[
            "mapping_commitment_sha256"
        ],
        repository_revision=metadata.get("repository_revision"),
        run_metadata_sha256=_sha256(metadata_path),
        official_summary_sha256=_sha256(summary_path),
        episodes_sha256=metadata["checkout"]["episodes_sha256"],
        checkpoints_sha256=metadata["checkout"]["checkpoints_sha256"],
    )


def _repeatability(
    first: dict[tuple[str, str], RunRecord],
    second: dict[tuple[str, str], RunRecord],
) -> dict[str, Any]:
    comparisons: list[dict[str, Any]] = []
    for domain in DOMAINS:
        for method in METHODS:
            key = (domain, method)
            a = first[key]
            b = second[key]
            summary_equal = a.official_summary == b.official_summary
            key_changed = (
                a.opaque_key_commitment_sha256
                != b.opaque_key_commitment_sha256
            )
            mapping_changed = (
                a.opaque_mapping_commitment_sha256
                != b.opaque_mapping_commitment_sha256
            )
            predictions_equal = (
                a.predictions_sha256 == b.predictions_sha256
            )
            expected_predictions_equal = method == "always_no_memory"
            if not summary_equal:
                raise RuntimeError(
                    f"official summary changed across fresh keys: {key}"
                )
            if not key_changed or not mapping_changed:
                raise RuntimeError(
                    f"opaque key/mapping commitment did not change: {key}"
                )
            if predictions_equal != expected_predictions_equal:
                raise RuntimeError(
                    "unexpected prediction-hash repeatability for "
                    f"{key}: equal={predictions_equal}, "
                    f"expected={expected_predictions_equal}"
                )
            comparisons.append(
                {
                    "domain": domain,
                    "method": method,
                    "official_summary_equal": summary_equal,
                    "opaque_key_commitment_changed": key_changed,
                    "opaque_mapping_commitment_changed": mapping_changed,
                    "predictions_sha256_equal": predictions_equal,
                    "expected_predictions_sha256_equal": (
                        expected_predictions_equal
                    ),
                }
            )
    return {
        "comparisons": comparisons,
        "aggregate": {
            "official_summary_equal": "8/8",
            "opaque_key_commitment_changed": "8/8",
            "opaque_mapping_commitment_changed": "8/8",
            "raw_lexical_predictions_hash_changed": "4/4",
            "always_no_memory_predictions_hash_changed": "0/4",
        },
    }


def reproduce(
    *,
    mindmap_root: Path,
    gatemem_root: Path,
    reference_rows_path: Path,
    output_root: Path,
    expected_mindmap_commit: str,
    reference_manifest_commit: str,
    audit_source_commit: str | None,
) -> dict[str, Any]:
    if output_root.exists() and any(output_root.iterdir()):
        raise RuntimeError(
            f"output root must be absent or empty: {output_root}"
        )
    output_root.mkdir(parents=True, exist_ok=True)

    observed_mindmap = _git(mindmap_root, "rev-parse", "HEAD")
    observed_gatemem = _git(gatemem_root, "rev-parse", "HEAD")
    if observed_mindmap != expected_mindmap_commit:
        raise RuntimeError(
            f"MindMap producing commit mismatch: "
            f"{observed_mindmap} != {expected_mindmap_commit}"
        )
    if observed_gatemem != EXPECTED_GATEMEM_COMMIT:
        raise RuntimeError(
            f"GateMem commit mismatch: "
            f"{observed_gatemem} != {EXPECTED_GATEMEM_COMMIT}"
        )
    if _git(mindmap_root, "status", "--porcelain", "--untracked-files=all"):
        raise RuntimeError("MindMap producing checkout is dirty")
    if _git(gatemem_root, "status", "--porcelain", "--untracked-files=all"):
        raise RuntimeError("GateMem checkout is dirty")
    scorer_hash = _sha256(
        gatemem_root / "bench" / "eval" / "scorer.py"
    )
    if scorer_hash != EXPECTED_SCORER_SHA256:
        raise RuntimeError(
            f"official scorer hash mismatch: {scorer_hash}"
        )

    reference_rows = _read_reference_rows(reference_rows_path)
    by_replicate: dict[int, dict[tuple[str, str], RunRecord]] = {}
    for replicate in (1, 2):
        records: dict[tuple[str, str], RunRecord] = {}
        for domain in DOMAINS:
            for method in METHODS:
                key = (domain, method)
                records[key] = _run_endpoint(
                    replicate=replicate,
                    domain=domain,
                    method=method,
                    mindmap_root=mindmap_root,
                    gatemem_root=gatemem_root,
                    output_root=output_root,
                    reference=reference_rows[key],
                )
        by_replicate[replicate] = records

    repeatability = _repeatability(
        by_replicate[1],
        by_replicate[2],
    )
    publishable = output_root / "publishable"
    publishable.mkdir(parents=True, exist_ok=True)

    first_rows = [
        by_replicate[1][(domain, method)].row
        for domain in DOMAINS
        for method in METHODS
    ]
    second_rows = [
        by_replicate[2][(domain, method)].row
        for domain in DOMAINS
        for method in METHODS
    ]
    _write_rows_csv(publishable / "replicate_1_rows.csv", first_rows)
    _write_rows_csv(publishable / "replicate_2_rows.csv", second_rows)

    run_records = []
    for replicate in (1, 2):
        for domain in DOMAINS:
            for method in METHODS:
                record = by_replicate[replicate][(domain, method)]
                run_records.append(
                    {
                        "replicate": record.replicate,
                        "domain": record.domain,
                        "method": record.method,
                        "row": _json_safe_row(record.row),
                        "predictions_sha256": (
                            record.predictions_sha256
                        ),
                        "opaque_key_commitment_sha256": (
                            record.opaque_key_commitment_sha256
                        ),
                        "opaque_mapping_commitment_sha256": (
                            record.opaque_mapping_commitment_sha256
                        ),
                        "repository_revision": (
                            record.repository_revision
                        ),
                        "run_metadata_sha256": (
                            record.run_metadata_sha256
                        ),
                        "official_summary_sha256": (
                            record.official_summary_sha256
                        ),
                        "episodes_sha256": (
                            record.episodes_sha256
                        ),
                        "checkpoints_sha256": (
                            record.checkpoints_sha256
                        ),
                    }
                )

    n_checkpoints = sum(
        int(reference_rows[(domain, "always_no_memory")]["n_checkpoints"])
        for domain in DOMAINS
    )
    result = {
        "schema_version": (
            "track-x-gatemem-pr46-independent-reproduction-v0.1"
        ),
        "classification": (
            "independent reproduction of PR #46 deterministic B0/B1a "
            "official endpoint controls; not a MindMap effectiveness result"
        ),
        "official_endpoint_control_reproduction_accepted": True,
        "architecture_effectiveness_claim": False,
        "audit_source_commit": audit_source_commit,
        "mindmap_producing_commit": observed_mindmap,
        "reference_manifest_commit": reference_manifest_commit,
        "reference_rows_sha256": _sha256(reference_rows_path),
        "gatemem_commit": observed_gatemem,
        "official_scorer_sha256": scorer_hash,
        "domains": list(DOMAINS),
        "methods": list(METHODS),
        "replicates": 2,
        "official_checkpoint_count": n_checkpoints,
        "row_comparisons_equal": "16/16",
        "repeatability": repeatability,
        "run_records": run_records,
        "publishable_boundary": {
            "raw_predictions_uploaded": False,
            "raw_benchmark_text_uploaded": False,
            "uploaded_files": [
                "STATUS.md",
                "reproduction.json",
                "repeatability.json",
                "replicate_1_rows.csv",
                "replicate_2_rows.csv",
                "run_records.json",
            ],
        },
        "interpretation": [
            (
                "Always-no-memory reproduces the zero-utility, "
                "zero-leakage, full-over-refusal endpoint."
            ),
            (
                "Policy-unaware raw lexical context echo reproduces "
                "partial utility with severe privacy and deletion leakage."
            ),
            (
                "All official domain summaries are invariant to a "
                "fresh opaque identifier key in two independent replicates."
            ),
            (
                "These controls do not estimate G-flat, T-normalized, "
                "raw fallback, a shared answer reader, or MindMap effectiveness."
            ),
        ],
    }
    (publishable / "reproduction.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (publishable / "repeatability.json").write_text(
        json.dumps(repeatability, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (publishable / "run_records.json").write_text(
        json.dumps(run_records, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    status_lines = [
        "# GateMem PR #46 independent endpoint reproduction",
        "",
        (
            "> Accepted only as deterministic official B0/B1a endpoint "
            "reproduction; not an architecture-effect result."
        ),
        "",
        f"- Audit source commit: `{audit_source_commit}`",
        f"- MindMap producing commit: `{observed_mindmap}`",
        f"- Reference manifest commit: `{reference_manifest_commit}`",
        f"- GateMem commit: `{observed_gatemem}`",
        f"- Official scorer SHA-256: `{scorer_hash}`",
        f"- Official checkpoints: `{n_checkpoints}`",
        "- Domains × methods × replicates: `4 × 2 × 2 = 16`",
        "- Reference row comparisons: `16/16 equal`",
        "- Official summaries across fresh keys: `8/8 equal`",
        "- Opaque key commitments changed: `8/8`",
        "- Raw-lexical prediction hashes changed: `4/4`",
        "- Always-no-memory prediction hashes changed: `0/4`",
        "- Raw predictions/raw benchmark text uploaded: `false`",
        "",
        (
            "The result reproduces the two deterministic external "
            "endpoints only. It does not estimate MindMap, G-flat, "
            "T-normalized, raw fallback, or a shared-reader system."
        ),
    ]
    (publishable / "STATUS.md").write_text(
        "\n".join(status_lines) + "\n",
        encoding="utf-8",
    )

    # Protected prediction/context bundles contain benchmark text and opaque
    # audit identifiers. They are deliberately destroyed before artifact upload.
    shutil.rmtree(output_root / "protected")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mindmap-root", type=Path, required=True)
    parser.add_argument("--gatemem-root", type=Path, required=True)
    parser.add_argument("--reference-rows", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--expected-mindmap-commit", required=True)
    parser.add_argument("--reference-manifest-commit", required=True)
    parser.add_argument("--audit-source-commit")
    args = parser.parse_args()
    result = reproduce(
        mindmap_root=args.mindmap_root.resolve(),
        gatemem_root=args.gatemem_root.resolve(),
        reference_rows_path=args.reference_rows.resolve(),
        output_root=args.output_root.resolve(),
        expected_mindmap_commit=args.expected_mindmap_commit,
        reference_manifest_commit=args.reference_manifest_commit,
        audit_source_commit=args.audit_source_commit,
    )
    print(
        json.dumps(
            {
                "classification": result["classification"],
                "official_endpoint_control_reproduction_accepted": (
                    result[
                        "official_endpoint_control_reproduction_accepted"
                    ]
                ),
                "official_checkpoint_count": result[
                    "official_checkpoint_count"
                ],
                "row_comparisons_equal": result[
                    "row_comparisons_equal"
                ],
                "repeatability": result["repeatability"][
                    "aggregate"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
