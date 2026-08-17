from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "experiments" / "equal_information_conformance_v0_2.py"
SPEC = importlib.util.spec_from_file_location("equal_information_conformance_v0_2", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class EqualInformationConformanceTests(unittest.TestCase):
    def test_literal_gold_is_independent_of_candidate_calls(self) -> None:
        for fixture in MODULE.fixtures():
            self.assertIsInstance(fixture.expected, dict)
            self.assertEqual(
                set(fixture.expected),
                {query.query_id for query in fixture.queries},
            )

    def test_candidate_mutation_does_not_mutate_gold(self) -> None:
        before = {
            fixture.fixture_id: dict(fixture.expected)
            for fixture in MODULE.fixtures()
        }
        with patch.object(MODULE.TypedResolver, "resolve", return_value="MUTATED"):
            report = MODULE.run()
        after = {
            fixture.fixture_id: dict(fixture.expected)
            for fixture in MODULE.fixtures()
        }
        self.assertEqual(before, after)
        self.assertGreater(report["summary"]["failure_count"], 0)
        self.assertEqual(
            report["summary"]["generic_correct"],
            report["summary"]["query_count"],
        )

    def test_typed_and_generic_resolvers_match_literal_gold(self) -> None:
        report = MODULE.run()
        summary = report["summary"]
        self.assertEqual(summary["failure_count"], 0)
        self.assertEqual(summary["typed_correct"], summary["query_count"])
        self.assertEqual(summary["generic_correct"], summary["query_count"])
        self.assertEqual(summary["systems_agree"], summary["query_count"])

    def test_suite_contains_deciding_contrastive_cases(self) -> None:
        fixture_ids = {fixture.fixture_id for fixture in MODULE.fixtures()}
        required = {
            "unsynchronized_replicas",
            "identity_fork_copy_cross_world",
            "receipt_rejection",
            "exposure_availability_lifecycle",
            "alternative_public_support",
            "protected_only_revocation",
            "fork_cutoff_vs_late_import",
            "snapshot_restore_gap",
            "authorized_same_principal_replication",
        }
        self.assertTrue(required.issubset(fixture_ids))


if __name__ == "__main__":
    unittest.main()
