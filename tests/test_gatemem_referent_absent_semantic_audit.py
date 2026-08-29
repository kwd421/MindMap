from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "run_gatemem_referent_absent_semantic_audit",
    ROOT / "tools" / "run_gatemem_referent_absent_semantic_audit.py",
)
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(AUDIT)
LABELS = (
    ROOT
    / "docs"
    / "research"
    / "inputs"
    / "EXP-20260828-009"
    / "manual_labels.csv"
)
SOURCE = (
    ROOT
    / "results"
    / "research"
    / "EXP-20260828-008"
    / "turn_results.csv"
)


def test_semantic_audit_reproduces_committed_artifacts(tmp_path: Path) -> None:
    summary = AUDIT.annotate(
        source_csv=SOURCE,
        labels_csv=LABELS,
        output_dir=tmp_path,
    )

    assert summary["population_rows"] == 57
    assert summary["request_type_counts"] == {
        "information_deletion": 53,
        "authorization_revocation": 4,
        "physical_domain_removal": 0,
        "ambiguous_or_other": 0,
    }
    assert summary["target_grounding_counts"] == {
        "explicit_current_turn": 53,
        "deictic_prior_context": 4,
        "ambiguous": 0,
    }
    assert summary["delete_signal_by_request_type"] == {
        "information_deletion": {"numerator": 0, "denominator": 53},
        "authorization_revocation": {"numerator": 0, "denominator": 4},
        "physical_domain_removal": {"numerator": 0, "denominator": 0},
        "ambiguous_or_other": {"numerator": 0, "denominator": 0},
    }

    committed = ROOT / "results" / "research" / "EXP-20260828-009"
    for name in ("annotations.csv", "summary.json", "artifact_manifest.json"):
        assert (tmp_path / name).read_bytes() == (committed / name).read_bytes()


def test_manual_label_vocabulary_represents_non_default_outcomes() -> None:
    base = {
        "domain": "synthetic",
        "episode_id": "episode",
        "turn_id": "turn",
        "text_sha256": "0" * 64,
        "request_type": "physical_domain_removal",
        "target_grounding": "ambiguous",
        "authorization_mixed": "true",
        "coder_confidence": "low",
        "note_code": "synthetic_control",
    }
    AUDIT.validate_manual_label(base, row_number=1)
    for request_type in AUDIT.REQUEST_TYPES:
        AUDIT.validate_manual_label(
            {**base, "request_type": request_type}, row_number=1
        )
    for grounding in AUDIT.TARGET_GROUNDINGS:
        AUDIT.validate_manual_label(
            {**base, "target_grounding": grounding}, row_number=1
        )


def _read_labels() -> list[dict[str, str]]:
    with LABELS.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_labels(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT.LABEL_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "extra",
        "duplicate",
        "text_hash_mismatch",
        "unknown_request_type",
        "unknown_target_grounding",
        "unknown_authorization_mixed",
        "unknown_coder_confidence",
    ],
)
def test_manual_label_manifest_fails_closed(
    tmp_path: Path, mutation: str
) -> None:
    rows = _read_labels()
    if mutation == "missing":
        rows.pop()
    elif mutation == "extra":
        extra = rows[0].copy()
        extra.update(
            {
                "domain": "synthetic_extra",
                "episode_id": "synthetic_episode",
                "turn_id": "synthetic_turn",
                "text_sha256": "f" * 64,
            }
        )
        rows.append(extra)
    elif mutation == "duplicate":
        rows.append(rows[0].copy())
    elif mutation == "text_hash_mismatch":
        rows[0]["text_sha256"] = "f" * 64
    elif mutation == "unknown_request_type":
        rows[0]["request_type"] = "implicit_default"
    elif mutation == "unknown_target_grounding":
        rows[0]["target_grounding"] = "implicit_default"
    elif mutation == "unknown_authorization_mixed":
        rows[0]["authorization_mixed"] = "unknown"
    else:
        rows[0]["coder_confidence"] = "unknown"
    labels = tmp_path / "labels.csv"
    _write_labels(labels, rows)

    with pytest.raises(RuntimeError):
        AUDIT.annotate(
            source_csv=SOURCE,
            labels_csv=labels,
            output_dir=tmp_path / "out",
        )
