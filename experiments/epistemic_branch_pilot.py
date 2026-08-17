#!/usr/bin/env python3
"""Mechanism-isolation pilot for NCM-Ψ v0.2.

This experiment uses gold structured records. It measures conformance to the
specified world-branch, mind-lineage, exposure, attitude, and disclosure
semantics. It is not an end-to-end raw-dialogue benchmark.
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import random
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

from mindmap.core import (
    BranchScopedCharacterResolver,
    GlobalCharacterResolver,
    LineageOnlyResolver,
    NCMResolver,
    PolicyOnlyCharacterResolver,
)
from mindmap.scenarios import generate_scenarios

RESOLVERS = [
    GlobalCharacterResolver(),
    BranchScopedCharacterResolver(),
    LineageOnlyResolver(),
    PolicyOnlyCharacterResolver(),
    NCMResolver(),
]


def bootstrap_ci(values: list[float], seed: int, reps: int = 10_000) -> tuple[float, float]:
    rr = random.Random(seed)
    n = len(values)
    draws = [sum(values[rr.randrange(n)] for _ in range(n)) / n for _ in range(reps)]
    draws.sort()
    return draws[int(0.025 * reps)], draws[min(reps - 1, int(0.975 * reps))]


def sign_flip_pvalue(values: list[float], seed: int, reps: int = 100_000) -> float:
    observed = abs(statistics.fmean(values))
    rr = random.Random(seed)
    extreme = 0
    for _ in range(reps):
        stat = abs(statistics.fmean(v if rr.random() < 0.5 else -v for v in values))
        if stat >= observed - 1e-15:
            extreme += 1
    return (extreme + 1) / (reps + 1)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def relevant_failure_family(template: str, kind: str, expected: str) -> str:
    if kind == "disclose" and expected == "no":
        return "unauthorized_disclosure"
    if template in {
        "mind_fork_isolation", "selective_transfer", "sealed_memory",
        "restore_gap", "belief_vs_world", "combined",
    } and kind in {"access", "ever_exposed", "attitude", "lineage"}:
        return "cross_instance"
    if template in {"world_fork_isolation", "cross_world_report", "combined"} and kind in {"world", "access", "ever_exposed", "attitude"}:
        return "cross_world"
    if kind == "source_count":
        return "provenance_laundering"
    return "other"


TARGET_SPACE = {
    "world": "WORLD",
    "access": "AVAILABLE",
    "ever_exposed": "EVER_EXPOSED",
    "attitude": "ATTITUDE",
    "disclose": "DISCLOSE",
    "source_count": "PROVENANCE",
    "lineage": "LINEAGE_INHERITANCE",
}


def eligible_error_tags(template: str, kind: str, expected: str) -> set[str]:
    tags: set[str] = set()
    if kind == "disclose" and expected == "no":
        tags.add("unauthorized_disclosure")
    if template in {
        "mind_fork_isolation", "selective_transfer", "sealed_memory",
        "restore_gap", "belief_vs_world", "combined",
    } and kind in {"access", "ever_exposed", "attitude", "lineage"}:
        tags.add("cross_instance")
    if template in {"world_fork_isolation", "cross_world_report", "combined"} and kind in {"world", "access", "ever_exposed", "attitude"}:
        tags.add("cross_world")
    if kind == "source_count":
        tags.add("provenance_laundering")
    return tags


def run(seed: int, per_template: int, output_dir: Path) -> dict[str, object]:
    started = time.perf_counter()
    scenarios = generate_scenarios(seed=seed, per_template=per_template)
    query_rows: list[dict[str, object]] = []

    for scenario in scenarios:
        for resolver in RESOLVERS:
            for query in scenario.queries:
                answer = resolver.answer(scenario, query)
                correct = answer == query.expected
                family = relevant_failure_family(scenario.template, query.kind, query.expected)
                eligible_tags = eligible_error_tags(scenario.template, query.kind, query.expected)
                error_tags: set[str] = set()
                if not correct:
                    error_tags.update(t for t in eligible_tags if t != "unauthorized_disclosure")
                if query.kind == "disclose" and query.expected == "no" and answer == "yes":
                    error_tags.add("unauthorized_disclosure")
                query_rows.append({
                    "scenario_id": scenario.scenario_id,
                    "template": scenario.template,
                    "scenario_seed": scenario.seed,
                    "system": resolver.name,
                    "query_id": query.query_id,
                    "query_kind": query.kind,
                    "target_space": TARGET_SPACE.get(query.kind, query.kind.upper()),
                    "query_label": query.metadata.get("label", query.kind),
                    "failure_family": family,
                    "eligible_error_tags": "|".join(sorted(eligible_tags)),
                    "error_tags": "|".join(sorted(error_tags)),
                    "world_branch_id": query.world_branch_id,
                    "about_world_branch_id": query.about_world_branch_id or query.world_branch_id,
                    "target_mind_instance_id": query.target_mind_instance_id or "",
                    "requester_id": query.requester_id or "",
                    "gold_object_id": query.evidence_id or query.claim_id or "",
                    "transaction_time": query.transaction_time,
                    "valid_time": query.valid_time,
                    "expected": query.expected,
                    "answer": answer,
                    "correct": int(correct),
                    "unauthorized_disclosure": int(query.kind == "disclose" and query.expected == "no" and answer == "yes"),
                })

    summary_rows: list[dict[str, object]] = []
    for resolver in RESOLVERS:
        rows = [r for r in query_rows if r["system"] == resolver.name]
        summary_rows.append({
            "system": resolver.name,
            "n_scenarios": len(scenarios),
            "n_queries": len(rows),
            "accuracy": sum(int(r["correct"]) for r in rows) / len(rows),
            "unauthorized_disclosure_rate": (
                sum("unauthorized_disclosure" in str(r["error_tags"]).split("|") for r in rows)
                / max(1, sum("unauthorized_disclosure" in str(r["eligible_error_tags"]).split("|") for r in rows))
            ),
            "cross_instance_error_rate": (
                sum("cross_instance" in str(r["error_tags"]).split("|") for r in rows)
                / max(1, sum("cross_instance" in str(r["eligible_error_tags"]).split("|") for r in rows))
            ),
            "cross_world_error_rate": (
                sum("cross_world" in str(r["error_tags"]).split("|") for r in rows)
                / max(1, sum("cross_world" in str(r["eligible_error_tags"]).split("|") for r in rows))
            ),
            "provenance_laundering_error_rate": (
                sum("provenance_laundering" in str(r["error_tags"]).split("|") for r in rows)
                / max(1, sum("provenance_laundering" in str(r["eligible_error_tags"]).split("|") for r in rows))
            ),
        })

    scenario_rows: list[dict[str, object]] = []
    by_scenario_system: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in query_rows:
        by_scenario_system[(str(row["scenario_id"]), str(row["system"]))].append(row)
    scenario_meta = {s.scenario_id: s for s in scenarios}
    for (scenario_id, system), rows in sorted(by_scenario_system.items()):
        scenario = scenario_meta[scenario_id]
        scenario_rows.append({
            "scenario_id": scenario_id,
            "template": scenario.template,
            "scenario_seed": scenario.seed,
            "system": system,
            "n_queries": len(rows),
            "accuracy": sum(int(r["correct"]) for r in rows) / len(rows),
            "n_cross_instance_errors": sum("cross_instance" in str(r["error_tags"]).split("|") for r in rows),
            "n_cross_world_errors": sum("cross_world" in str(r["error_tags"]).split("|") for r in rows),
            "n_unauthorized_disclosures": sum("unauthorized_disclosure" in str(r["error_tags"]).split("|") for r in rows),
            "n_provenance_laundering_errors": sum("provenance_laundering" in str(r["error_tags"]).split("|") for r in rows),
        })

    grouped_rows: list[dict[str, object]] = []
    for grouping_name, key_fn in [
        ("template", lambda r: r["template"]),
        ("query_kind", lambda r: r["query_kind"]),
        ("failure_family", lambda r: r["failure_family"]),
    ]:
        grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
        for row in query_rows:
            grouped[(str(row["system"]), str(key_fn(row)))].append(row)
        for (system, group), rows in sorted(grouped.items()):
            grouped_rows.append({
                "grouping": grouping_name,
                "group": group,
                "system": system,
                "n": len(rows),
                "accuracy": sum(int(r["correct"]) for r in rows) / len(rows),
            })

    ablation_names = ["B5_branch_scoped_character", "B5a_lineage_only", "B5b_policy_only"]
    summary_accuracy = {str(r["system"]): float(r["accuracy"]) for r in summary_rows}
    strongest_ablation = max(ablation_names, key=lambda n: summary_accuracy[n])
    scenario_differences: list[float] = []
    for scenario in scenarios:
        b5 = [r for r in query_rows if r["scenario_id"] == scenario.scenario_id and r["system"] == strongest_ablation]
        b6 = [r for r in query_rows if r["scenario_id"] == scenario.scenario_id and r["system"] == "B6_ncm_psi"]
        scenario_differences.append(
            statistics.fmean(int(r["correct"]) for r in b6)
            - statistics.fmean(int(r["correct"]) for r in b5)
        )

    diff = statistics.fmean(scenario_differences)
    ci_low, ci_high = bootstrap_ci(scenario_differences, seed + 11)
    pvalue = sign_flip_pvalue(scenario_differences, seed + 29)
    comparison = {
        "comparison": f"B6_ncm_psi - {strongest_ablation}",
        "strongest_ablation": strongest_ablation,
        "scenario_clustered_accuracy_difference": diff,
        "bootstrap_95_ci_low": ci_low,
        "bootstrap_95_ci_high": ci_high,
        "sign_flip_pvalue": pvalue,
        "n_scenarios": len(scenarios),
        "n_positive_scenarios": sum(v > 0 for v in scenario_differences),
        "n_negative_scenarios": sum(v < 0 for v in scenario_differences),
        "n_tied_scenarios": sum(v == 0 for v in scenario_differences),
        "bootstrap_repetitions": 10_000,
        "sign_flip_repetitions": 100_000,
        "bootstrap_seed": seed + 11,
        "sign_flip_seed": seed + 29,
    }

    manifest = {
        "study": "NCM-Psi v0.2 mechanism-isolation pilot",
        "interpretation": "structured-oracle conformance/mechanism study; not end-to-end raw-text accuracy",
        "seed": seed,
        "per_template": per_template,
        "n_templates": len({s.template for s in scenarios}),
        "n_scenarios": len(scenarios),
        "queries_per_scenario": sorted({len(s.queries) for s in scenarios}),
        "n_query_system_rows": len(query_rows),
        "python": sys.version,
        "platform": platform.platform(),
        "elapsed_seconds": time.perf_counter() - started,
        "comparison": comparison,
    }

    write_csv(output_dir / "epistemic_branch_pilot_query_results.csv", query_rows)
    write_csv(output_dir / "epistemic_branch_pilot_per_scenario.csv", scenario_rows)
    write_csv(output_dir / "epistemic_branch_pilot_summary.csv", summary_rows)
    write_csv(output_dir / "epistemic_branch_pilot_grouped.csv", grouped_rows)
    (output_dir / "epistemic_branch_pilot_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"summary": summary_rows, "comparison": comparison, "manifest": manifest}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument("--per-template", type=int, default=24)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "results")
    args = parser.parse_args()
    results = run(args.seed, args.per_template, args.output_dir)
    print("NCM-Ψ v0.2 structured mechanism-isolation pilot")
    for row in results["summary"]:
        print(
            f"{row['system']}: accuracy={row['accuracy']:.4f}, "
            f"cross_instance_error={row['cross_instance_error_rate']:.4f}, "
            f"cross_world_error={row['cross_world_error_rate']:.4f}, "
            f"unauthorized_disclosure={row['unauthorized_disclosure_rate']:.4f}"
        )
    c = results["comparison"]
    print(
        f"B6-{c['strongest_ablation']} clustered accuracy difference: "
        f"{c['scenario_clustered_accuracy_difference']:.4f} "
        f"(95% bootstrap CI {c['bootstrap_95_ci_low']:.4f}, {c['bootstrap_95_ci_high']:.4f}); "
        f"sign-flip p={c['sign_flip_pvalue']:.6g}"
    )


if __name__ == "__main__":
    main()
