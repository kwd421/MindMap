from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
import time
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from .model import *
from .fixtures import all_fixtures
from .validation_common import ValidationResult
from .generic_validation import validate_generic_audited
from .typed_validation import parse_typed
from .resolvers import TypedState, generic_answer
from .faults import make_faults

SYSTEMS = ("generic_basic", "generic_audited", "typed")
MUTANTS = (
    "receipt_implies_belief",
    "identity_fork_first_person",
    "forget_erases_history",
    "flatten_policy",
    "system_time_fork",
    "same_origin_independent",
    "branch_collapse",
)


def validate_system(system: str, events: Sequence[CommonEvent]) -> tuple[Optional[TypedState], ValidationResult]:
    if system == "generic_basic":
        findings: list[Finding] = []
        seen: set[str] = set()
        c = RunCounters()
        for e in events:
            c.scanned_events += 1
            c.local_checks += 2
            if e.event_id in seen:
                findings.append(Finding("duplicate_event_id", (e.event_id,), "duplicate", "generic_ingest"))
            seen.add(e.event_id)
            if e.valid_time < 0 or e.system_time < 0:
                findings.append(Finding("invalid_time", (e.event_id,), "negative", "generic_ingest"))
        return None, ValidationResult(findings, c)
    if system == "generic_audited":
        return None, validate_generic_audited(events)
    typed, result = parse_typed(events)
    return TypedState(typed), result


def answer_system(system: str, events: Sequence[CommonEvent], state: Optional[TypedState], q: Query) -> str:
    return state.answer(q) if system == "typed" and state is not None else generic_answer(events, q)


def evaluate_clean(fixtures: Sequence[Fixture]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    query_rows: list[dict[str, Any]] = []
    validator_rows: list[dict[str, Any]] = []
    for fixture in fixtures:
        for system in SYSTEMS:
            state, validation = validate_system(system, fixture.events)
            validator_rows.append({
                "fixture_id": fixture.fixture_id,
                "archetype": fixture.archetype,
                "system": system,
                "finding_count": len(validation.findings),
                "local_checks": validation.counters.local_checks,
                "cross_checks": validation.counters.cross_checks,
                "scanned_events": validation.counters.scanned_events,
            })
            for q in fixture.queries:
                pred = answer_system(system, fixture.events, state, q)
                query_rows.append({
                    "fixture_id": fixture.fixture_id,
                    "archetype": fixture.archetype,
                    "query_id": q.query_id,
                    "target": q.target,
                    "system": system,
                    "gold": q.expected,
                    "prediction": pred,
                    "correct": int(pred == q.expected),
                    "validator_findings": len(validation.findings),
                })
    return query_rows, validator_rows


def evaluate_faults(fixtures: Sequence[Fixture], faults: Sequence[Fault]) -> list[dict[str, Any]]:
    by_id = {f.fixture_id: f for f in fixtures}
    rows: list[dict[str, Any]] = []
    for fault in faults:
        fixture = by_id[fault.fixture_id]
        semantic_effect = any(generic_answer(fault.mutated_events, q) != q.expected for q in fixture.queries)
        for system in SYSTEMS:
            state, validation = validate_system(system, fault.mutated_events)
            localized = validation.localized_ids
            detected = bool(validation.findings)
            for q in fixture.queries:
                affected = bool(set(q.depends_on).intersection({fault.target_event_id} if fault.target_event_id else set()))
                if detected and set(q.depends_on).intersection(localized):
                    pred = ABSTAIN
                else:
                    pred = answer_system(system, fault.mutated_events, state, q)
                correct = pred == q.expected
                silent_wrong = int(not correct and pred != ABSTAIN)
                contained = int(pred == ABSTAIN)
                rows.append({
                    "fault_id": fault.fault_id,
                    "fault_class": fault.fault_class,
                    "description": fault.description,
                    "fixture_id": fixture.fixture_id,
                    "archetype": fixture.archetype,
                    "target_event_id": fault.target_event_id,
                    "query_id": q.query_id,
                    "target": q.target,
                    "system": system,
                    "gold": q.expected,
                    "prediction": pred,
                    "affected_by_declared_target": int(affected),
                    "fault_has_observed_semantic_effect": int(semantic_effect),
                    "correct": int(correct),
                    "detected": int(detected),
                    "localized_target": int(fault.target_event_id in localized if fault.target_event_id else False),
                    "silent_wrong": silent_wrong,
                    "contained": contained,
                    "finding_codes": "|".join(sorted({f.code for f in validation.findings})),
                    "localized_ids": "|".join(sorted(localized)),
                    "local_checks": validation.counters.local_checks,
                    "cross_checks": validation.counters.cross_checks,
                })
    return rows


def evaluate_mutants(fixtures: Sequence[Fixture]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for mutant in MUTANTS:
        failures = 0
        total = 0
        failed_fixtures: set[str] = set()
        for fixture in fixtures:
            for q in fixture.queries:
                pred = generic_answer(fixture.events, q, mutant=mutant)
                total += 1
                if pred != q.expected:
                    failures += 1
                    failed_fixtures.add(fixture.fixture_id)
        rows.append({
            "mutant": mutant,
            "killed": int(failures > 0),
            "failed_queries": failures,
            "total_queries": total,
            "failed_fixtures": len(failed_fixtures),
            "fixture_ids": "|".join(sorted(failed_fixtures)),
        })
    return rows


def summarize_clean(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for system in SYSTEMS:
        sr = [r for r in rows if r["system"] == system]
        by_fixture: dict[str, list[int]] = {}
        for r in sr:
            by_fixture.setdefault(str(r["fixture_id"]), []).append(int(r["correct"]))
        out.append({
            "system": system,
            "queries": len(sr),
            "accuracy": sum(int(r["correct"]) for r in sr) / len(sr),
            "fixtures_all_correct": sum(all(v) for v in by_fixture.values()) / len(by_fixture),
            "validator_findings": sum(int(r["validator_findings"]) for r in sr),
        })
    return out


def summarize_faults(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for system in SYSTEMS:
        for fault_class in sorted({str(r["fault_class"]) for r in rows}):
            sr = [r for r in rows if r["system"] == system and r["fault_class"] == fault_class]
            faults = sorted({str(r["fault_id"]) for r in sr})
            detected_faults = sum(any(int(r["detected"]) for r in sr if r["fault_id"] == fid) for fid in faults)
            localized_faults = sum(any(int(r["localized_target"]) for r in sr if r["fault_id"] == fid) for fid in faults)
            out.append({
                "system": system,
                "fault_class": fault_class,
                "faults": len(faults),
                "queries": len(sr),
                "query_accuracy": sum(int(r["correct"]) for r in sr) / len(sr),
                "fault_detection_recall": detected_faults / len(faults),
                "target_localization_recall": localized_faults / len(faults),
                "silent_wrong_rate": sum(int(r["silent_wrong"]) for r in sr) / len(sr),
                "containment_rate": sum(int(r["contained"]) for r in sr) / len(sr),
                "safe_outcome_rate": 1.0 - (sum(int(r["silent_wrong"]) for r in sr) / len(sr)),
                "answer_coverage": 1.0 - (sum(int(r["contained"]) for r in sr) / len(sr)),
                "conditional_accuracy_when_answered": (
                    sum(int(r["correct"]) for r in sr if not int(r["contained"]))
                    / max(1, sum(1 for r in sr if not int(r["contained"])))
                ),
                "faults_with_observed_semantic_effect": len({str(r["fault_id"]) for r in sr if int(r["fault_has_observed_semantic_effect"])}),
                "mean_checks_per_query": statistics.mean(int(r["local_checks"]) + int(r["cross_checks"]) for r in sr),
            })
    return out


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def stable_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("results/p0_equal_information"))
    args = parser.parse_args()
    started = time.perf_counter()

    fixtures = all_fixtures()
    clean_rows, validator_rows = evaluate_clean(fixtures)
    faults = make_faults(fixtures)
    fault_rows = evaluate_faults(fixtures, faults)
    mutant_rows = evaluate_mutants(fixtures)
    clean_summary = summarize_clean(clean_rows)
    fault_summary = summarize_faults(fault_rows)

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "clean_query_results.csv", clean_rows)
    write_csv(out / "clean_summary.csv", clean_summary)
    write_csv(out / "validator_summary.csv", validator_rows)
    write_csv(out / "fault_query_results.csv", fault_rows)
    write_csv(out / "fault_summary.csv", fault_summary)
    write_csv(out / "mutation_summary.csv", mutant_rows)

    metadata = {
        "benchmark": "NCM-Psi P0 Equal-Information Audit v0.1",
        "scope": "symbolic deterministic semantic-conformance and fault-class audit",
        "fixtures": len(fixtures),
        "queries": sum(len(f.queries) for f in fixtures),
        "faults": len(faults),
        "systems": list(SYSTEMS),
        "mutants": list(MUTANTS),
        "gold_independence": (
            "Expected outputs are literal fixture data; neither generic nor typed resolver is called to generate gold."
        ),
        "decisive_interpretation": (
            "A complete generic invariant layer and the typed ledger are expected to tie on finite clean semantics and on faults covered by equivalent invariants."
        ),
        "limitations": [
            "No natural-language extraction or LLM reader is evaluated.",
            "Fixtures are hand-authored archetypes, not an independent population sample.",
            "The generic-audited and typed validators implement intentionally equivalent finite invariants.",
            "Well-formed source/extraction errors cannot be detected without independent evidence in this setup.",
            "Latency and check counts are Python reference-implementation diagnostics, not database production costs.",
        ],
        "runtime_seconds": time.perf_counter() - started,
    }
    (out / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = {}
    for path in sorted(out.iterdir()):
        if path.is_file():
            manifest[path.name] = {"bytes": path.stat().st_size, "sha256": stable_hash(path)}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("CLEAN")
    for row in clean_summary:
        print(row)
    print("\nFAULTS")
    for row in fault_summary:
        print(row)
    print("\nMUTANTS")
    for row in mutant_rows:
        print(row)
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
