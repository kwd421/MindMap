from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "reproduce_gatemem_pr46.py"
)
SPEC = importlib.util.spec_from_file_location(
    "reproduce_gatemem_pr46",
    MODULE_PATH,
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"could not load reproduction module from {MODULE_PATH}")
REPRO = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = REPRO
SPEC.loader.exec_module(REPRO)


REFERENCE_ROWS = """domain,method,n_checkpoints,n_utility,n_privacy,n_safety,action_accuracy,utility_accuracy,privacy_answer_leakage_rate,privacy_context_leakage_rate,privacy_e2e_leakage_rate,deletion_answer_leakage_rate,deletion_context_leakage_rate,deletion_e2e_leakage_rate,over_refusal_rate,compliance_utility_score,compliance_utility_e2e_score,gated_by_action,opaque_mapping_count
education,always_no_memory,540,180,180,180,0.3333333333333333,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1.0,0.0,0.0,False,7697
education,raw_lexical,540,180,180,180,0.3333333333333333,0.26666666666666666,0.5388888888888889,0.5388888888888889,0.5388888888888889,0.8888888888888888,0.8888888888888888,0.8888888888888888,0.0,0.013662551440329225,0.013662551440329225,False,7697
household,always_no_memory,552,184,184,184,0.3333333333333333,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1.0,0.0,0.0,False,5951
household,raw_lexical,552,184,184,184,0.3333333333333333,0.34782608695652173,0.6847826086956522,0.6847826086956522,0.6847826086956522,0.8260869565217391,0.8260869565217391,0.8260869565217391,0.0,0.019067970740527653,0.019067970740527653,False,5951
medical,always_no_memory,579,210,192,177,0.30569948186528495,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1.0,0.0,0.0,False,5210
medical,raw_lexical,579,210,192,177,0.3626943005181347,0.5761904761904761,0.6979166666666666,0.6979166666666666,0.6979166666666666,0.7062146892655368,0.7062146892655368,0.7062146892655368,0.0,0.05113554838131109,0.05113554838131109,False,5210
office,always_no_memory,547,154,171,222,0.40585009140767825,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1.0,0.0,0.0,False,4967
office,raw_lexical,547,154,171,222,0.28153564899451555,0.6623376623376623,0.8888888888888888,0.8888888888888888,0.8888888888888888,0.9369369369369369,0.9369369369369369,0.9369369369369369,0.0,0.004641004641004645,0.004641004641004645,False,4967
"""


def _record(
    *,
    replicate: int,
    domain: str,
    method: str,
    predictions_sha256: str,
    key_commitment: str,
    mapping_commitment: str,
):
    return REPRO.RunRecord(
        replicate=replicate,
        domain=domain,
        method=method,
        row={},
        official_summary={"domain": domain, "method": method, "metric": 1},
        predictions_sha256=predictions_sha256,
        opaque_key_commitment_sha256=key_commitment,
        opaque_mapping_commitment_sha256=mapping_commitment,
        repository_revision="revision",
        run_metadata_sha256="metadata",
        official_summary_sha256="summary",
        episodes_sha256="episodes",
        checkpoints_sha256="checkpoints",
    )


class ReferenceRowsTest(unittest.TestCase):
    def test_frozen_reference_rows_have_complete_official_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "rows.csv"
            path.write_text(REFERENCE_ROWS, encoding="utf-8")
            rows = REPRO._read_reference_rows(path)

        self.assertEqual(len(rows), 8)
        self.assertEqual(
            sum(
                rows[(domain, "always_no_memory")]["n_checkpoints"]
                for domain in REPRO.DOMAINS
            ),
            2218,
        )

    def test_repeatability_contract_distinguishes_endpoint_hash_behavior(self) -> None:
        first = {}
        second = {}
        for domain in REPRO.DOMAINS:
            for method in REPRO.METHODS:
                key = (domain, method)
                first_hash = f"{domain}-{method}-first"
                second_hash = (
                    first_hash
                    if method == "always_no_memory"
                    else f"{domain}-{method}-second"
                )
                first[key] = _record(
                    replicate=1,
                    domain=domain,
                    method=method,
                    predictions_sha256=first_hash,
                    key_commitment=f"{domain}-{method}-key-1",
                    mapping_commitment=f"{domain}-{method}-mapping-1",
                )
                second[key] = _record(
                    replicate=2,
                    domain=domain,
                    method=method,
                    predictions_sha256=second_hash,
                    key_commitment=f"{domain}-{method}-key-2",
                    mapping_commitment=f"{domain}-{method}-mapping-2",
                )

        result = REPRO._repeatability(first, second)

        self.assertEqual(
            result["aggregate"]["official_summary_equal"],
            "8/8",
        )
        self.assertEqual(
            result["aggregate"]["raw_lexical_predictions_hash_changed"],
            "4/4",
        )


if __name__ == "__main__":
    unittest.main()
