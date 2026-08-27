from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


SCHEMA_VERSION = "gatemem-referent-absent-semantic-audit-v2"
CODEBOOK_VERSION = "GM-RA-CB-001-v0.1.0"
PLANNING_COMMIT = "c17d308ba10028ba20e2655a0597ea426bd32005"
SOURCE_RESULTS_SHA256 = (
    "5133fae854abb92cf3856f03efc346e2e6dcf1e13b3f7d86285ba3f3faf8f66d"
)


RowKey = tuple[str, str, str]
LABEL_FIELDS = (
    "domain",
    "episode_id",
    "turn_id",
    "text_sha256",
    "request_type",
    "target_grounding",
    "authorization_mixed",
    "coder_confidence",
    "note_code",
)
REQUEST_TYPES = frozenset(
    {
        "information_deletion",
        "authorization_revocation",
        "physical_domain_removal",
        "ambiguous_or_other",
    }
)
TARGET_GROUNDINGS = frozenset(
    {"explicit_current_turn", "deictic_prior_context", "ambiguous"}
)
BOOLEAN_VALUES = frozenset({"false", "true"})
CONFIDENCE_VALUES = frozenset({"high", "low"})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_manual_label(row: dict[str, str], *, row_number: int) -> None:
    for field, allowed in (
        ("request_type", REQUEST_TYPES),
        ("target_grounding", TARGET_GROUNDINGS),
        ("authorization_mixed", BOOLEAN_VALUES),
        ("coder_confidence", CONFIDENCE_VALUES),
    ):
        if row[field] not in allowed:
            raise RuntimeError(
                f"manual label row {row_number} has invalid {field}: {row[field]!r}"
            )
    if not row["note_code"] or any(
        character.isspace() for character in row["note_code"]
    ):
        raise RuntimeError(
            f"manual label row {row_number} has invalid note_code: {row['note_code']!r}"
        )


def load_manual_labels(
    *, labels_csv: Path, source_by_key: dict[RowKey, dict[str, str]]
) -> dict[RowKey, dict[str, str]]:
    with labels_csv.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != LABEL_FIELDS:
            raise RuntimeError("manual label manifest header mismatch")
        label_rows = list(reader)

    labels_by_key: dict[RowKey, dict[str, str]] = {}
    for row_number, row in enumerate(label_rows, start=1):
        validate_manual_label(row, row_number=row_number)
        key = (row["domain"], row["episode_id"], row["turn_id"])
        if key in labels_by_key:
            raise RuntimeError(f"duplicate manual label key: {key}")
        labels_by_key[key] = row

    source_keys = set(source_by_key)
    label_keys = set(labels_by_key)
    if label_keys != source_keys:
        missing = sorted(source_keys - label_keys)
        extra = sorted(label_keys - source_keys)
        raise RuntimeError(
            f"manual label manifest must cover source keys exactly; "
            f"missing={missing}, extra={extra}"
        )
    for key, label in labels_by_key.items():
        if label["text_sha256"] != source_by_key[key]["text_sha256"]:
            raise RuntimeError(f"manual label text hash mismatch for key: {key}")
    return labels_by_key


def annotate(
    *, source_csv: Path, labels_csv: Path, output_dir: Path
) -> dict[str, object]:
    if sha256_file(source_csv) != SOURCE_RESULTS_SHA256:
        raise RuntimeError("EXP-008 source CSV hash mismatch")

    with source_csv.open(encoding="utf-8", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    selected = [
        row for row in source_rows if row["information_referent_present"] == "False"
    ]
    if len(selected) != 57:
        raise RuntimeError(f"expected 57 referent-absent rows, found {len(selected)}")

    source_by_key = {
        (row["domain"], row["episode_id"], row["turn_id"]): row
        for row in selected
    }
    if len(source_by_key) != 57:
        raise RuntimeError("referent-absent row keys are not unique")
    labels_by_key = load_manual_labels(
        labels_csv=labels_csv, source_by_key=source_by_key
    )

    annotations: list[dict[str, object]] = []
    for source_row_number, row in enumerate(selected, start=1):
        key = (row["domain"], row["episode_id"], row["turn_id"])
        label = labels_by_key[key]
        annotations.append(
            {
                "source_row_number": source_row_number,
                "domain": row["domain"],
                "episode_id": row["episode_id"],
                "turn_id": row["turn_id"],
                "text_sha256": row["text_sha256"],
                "request_type": label["request_type"],
                "target_grounding": label["target_grounding"],
                "authorization_mixed": label["authorization_mixed"],
                "coder_confidence": label["coder_confidence"],
                "note_code": label["note_code"],
                "delete_signal_count": int(row["delete_signal_count"]),
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    annotations_path = output_dir / "annotations.csv"
    with annotations_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(annotations[0]))
        writer.writeheader()
        writer.writerows(annotations)

    request_counts = Counter(row["request_type"] for row in annotations)
    grounding_counts = Counter(row["target_grounding"] for row in annotations)
    delete_by_type = {
        request_type: {
            "numerator": sum(
                int(row["delete_signal_count"]) > 0
                for row in annotations
                if row["request_type"] == request_type
            ),
            "denominator": request_counts.get(request_type, 0),
        }
        for request_type in (
            "information_deletion",
            "authorization_revocation",
            "physical_domain_removal",
            "ambiguous_or_other",
        )
    }
    summary: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "study_class": "development",
        "post_hoc": True,
        "blinded": False,
        "independent_human_adjudication": False,
        "official_benchmark_score": False,
        "codebook_version": CODEBOOK_VERSION,
        "planning_commit": PLANNING_COMMIT,
        "source_csv_sha256": SOURCE_RESULTS_SHA256,
        "manual_label_manifest_sha256": sha256_file(labels_csv),
        "manual_label_manifest_rows": len(labels_by_key),
        "manual_label_manifest_complete": True,
        "population_rows": len(annotations),
        "request_type_counts": {
            name: request_counts.get(name, 0)
            for name in (
                "information_deletion",
                "authorization_revocation",
                "physical_domain_removal",
                "ambiguous_or_other",
            )
        },
        "target_grounding_counts": {
            name: grounding_counts.get(name, 0)
            for name in (
                "explicit_current_turn",
                "deictic_prior_context",
                "ambiguous",
            )
        },
        "authorization_mixed_count": sum(
            row["authorization_mixed"] == "true" for row in annotations
        ),
        "delete_signal_by_request_type": delete_by_type,
        "claim_boundary": (
            "Single model-assisted post-hoc coder over the frozen 57-row "
            "referent-absent development stratum; not semantic gold, an "
            "official GateMem score, or evidence of state-level forgetting."
        ),
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest_path = output_dir / "artifact_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "annotations.csv": sha256_file(annotations_path),
                "summary.json": sha256_file(summary_path),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-csv", type=Path, required=True)
    parser.add_argument("--labels-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = annotate(**vars(args))
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
