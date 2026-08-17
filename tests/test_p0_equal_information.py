from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "experiments" / "p0_equal_information_audit.py"
spec = importlib.util.spec_from_file_location("p0_equal_information_audit", MODULE_PATH)
assert spec and spec.loader
p0 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = p0
spec.loader.exec_module(p0)


def test_clean_equal_information_conformance() -> None:
    fixtures = p0.all_fixtures()
    rows, validators = p0.evaluate_clean(fixtures)
    assert rows
    assert all(row["correct"] == 1 for row in rows)
    assert all(row["finding_count"] == 0 for row in validators)

    by_query: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        by_query.setdefault((row["fixture_id"], row["query_id"]), set()).add(row["prediction"])
    assert all(len(predictions) == 1 for predictions in by_query.values())


def test_complete_generic_and_typed_have_equal_fault_coverage() -> None:
    fixtures = p0.all_fixtures()
    rows = p0.evaluate_faults(fixtures, p0.make_faults(fixtures))
    for fault_id in sorted({row["fault_id"] for row in rows}):
        generic = [r for r in rows if r["fault_id"] == fault_id and r["system"] == "generic_audited"]
        typed = [r for r in rows if r["fault_id"] == fault_id and r["system"] == "typed"]
        assert [r["prediction"] for r in generic] == [r["prediction"] for r in typed]
        assert [r["detected"] for r in generic] == [r["detected"] for r in typed]
        assert [r["localized_target"] for r in generic] == [r["localized_target"] for r in typed]


def test_enforceable_faults_are_contained_by_complete_validators() -> None:
    fixtures = p0.all_fixtures()
    rows = p0.evaluate_faults(fixtures, p0.make_faults(fixtures))
    for system in ("generic_audited", "typed"):
        selected = [r for r in rows if r["system"] == system and r["fault_class"] == "enforceable"]
        assert selected
        assert all(r["detected"] == 1 for r in selected)
        assert all(r["silent_wrong"] == 0 for r in selected)


def test_well_formed_and_missing_faults_expose_verification_gap() -> None:
    fixtures = p0.all_fixtures()
    rows = p0.evaluate_faults(fixtures, p0.make_faults(fixtures))
    for system in ("generic_audited", "typed"):
        selected = [
            r
            for r in rows
            if r["system"] == system
            and r["fault_class"] in {"well_formed_semantic", "missing_event"}
        ]
        assert selected
        assert any(r["silent_wrong"] == 1 for r in selected)
        assert all(r["detected"] == 0 for r in selected)


def test_fixture_suite_kills_all_preregistered_mutants() -> None:
    rows = p0.evaluate_mutants(p0.all_fixtures())
    assert rows
    assert all(row["killed"] == 1 for row in rows)
