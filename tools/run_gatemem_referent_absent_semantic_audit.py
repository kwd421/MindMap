from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


SCHEMA_VERSION = "gatemem-referent-absent-semantic-audit-v1"
CODEBOOK_VERSION = "GM-RA-CB-001-v0.1.0"
PLANNING_COMMIT = "c17d308ba10028ba20e2655a0597ea426bd32005"
SOURCE_RESULTS_SHA256 = (
    "5133fae854abb92cf3856f03efc346e2e6dcf1e13b3f7d86285ba3f3faf8f66d"
)


RowKey = tuple[str, str, str]


AUTHORIZATION_REVOCATION_KEYS: frozenset[RowKey] = frozenset(
    {
        (
            "medical",
            "med_episode_rewrite_en_007_thyroid_biopsy_deleted_rose_lodge_contact",
            "t068",
        ),
        (
            "medical",
            "med_episode_rewrite_en_012_new_hiv_deleted_harbor_light_line",
            "t084",
        ),
        (
            "medical",
            "med_episode_rewrite_en_016_early_pregnancy_deleted_haven_house_line",
            "t073",
        ),
        (
            "medical",
            "med_episode_rewrite_en_018_hematuria_deleted_harbor_house_line",
            "t069",
        ),
    }
)


DEICTIC_PRIOR_CONTEXT_KEYS: frozenset[RowKey] = frozenset(
    {
        (
            "household",
            "household_episode_custom_en_007_juniper_paws_juniper_parcel_pet_courier",
            "t149",
        ),
        (
            "household",
            "household_episode_custom_en_016_laurel_lift_laurel_locker_gym_supply_private_note",
            "t152",
        ),
        (
            "household",
            "household_episode_custom_en_017_apricot_archive_apricot_adapter_media_backup_private_note",
            "t152",
        ),
        (
            "household",
            "household_episode_custom_en_018_slate_sweep_slate_soap_robot_supply_private_note",
            "t152",
        ),
    }
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def annotate(*, source_csv: Path, output_dir: Path) -> dict[str, object]:
    if sha256_file(source_csv) != SOURCE_RESULTS_SHA256:
        raise RuntimeError("EXP-008 source CSV hash mismatch")

    with source_csv.open(encoding="utf-8", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    selected = [
        row for row in source_rows if row["information_referent_present"] == "False"
    ]
    if len(selected) != 57:
        raise RuntimeError(f"expected 57 referent-absent rows, found {len(selected)}")

    keys = {
        (row["domain"], row["episode_id"], row["turn_id"]) for row in selected
    }
    if len(keys) != 57:
        raise RuntimeError("referent-absent row keys are not unique")
    for label, expected in (
        ("authorization", AUTHORIZATION_REVOCATION_KEYS),
        ("deictic", DEICTIC_PRIOR_CONTEXT_KEYS),
    ):
        missing = expected - keys
        if missing:
            raise RuntimeError(f"{label} manual label keys absent from source: {missing}")

    annotations: list[dict[str, object]] = []
    for source_row_number, row in enumerate(selected, start=1):
        key = (row["domain"], row["episode_id"], row["turn_id"])
        request_type = (
            "authorization_revocation"
            if key in AUTHORIZATION_REVOCATION_KEYS
            else "information_deletion"
        )
        grounding = (
            "deictic_prior_context"
            if key in DEICTIC_PRIOR_CONTEXT_KEYS
            else "explicit_current_turn"
        )
        annotations.append(
            {
                "source_row_number": source_row_number,
                "domain": row["domain"],
                "episode_id": row["episode_id"],
                "turn_id": row["turn_id"],
                "text_sha256": row["text_sha256"],
                "request_type": request_type,
                "target_grounding": grounding,
                "authorization_mixed": "false",
                "coder_confidence": "high",
                "note_code": (
                    "principal_access_revoke"
                    if request_type == "authorization_revocation"
                    else (
                        "deictic_exact_content"
                        if grounding == "deictic_prior_context"
                        else "explicit_content"
                    )
                ),
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
        "authorization_mixed_count": 0,
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
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = annotate(**vars(args))
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
