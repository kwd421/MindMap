from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "run_gatemem_referent_absent_semantic_audit",
    ROOT / "tools" / "run_gatemem_referent_absent_semantic_audit.py",
)
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(AUDIT)


def test_semantic_audit_reproduces_committed_artifacts(tmp_path: Path) -> None:
    summary = AUDIT.annotate(
        source_csv=ROOT
        / "results"
        / "research"
        / "EXP-20260828-008"
        / "turn_results.csv",
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
