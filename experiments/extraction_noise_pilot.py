#!/usr/bin/env python3
"""Correlated fault-injection study for NCM-Ψ v0.2.

The perturbations act on joint event/lineage hypotheses rather than dropping
independent fields. This is still a structured mechanism study, not a natural
extractor benchmark.
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
    LineageOnlyResolver,
    NCMResolver,
    PolicyOnlyCharacterResolver,
)
from mindmap.corruption import CORRUPTION_MODES, corrupt_dataset, corrupt_scenario
from mindmap.scenarios import generate_scenarios

SYSTEMS = [
    BranchScopedCharacterResolver(),
    LineageOnlyResolver(),
    PolicyOnlyCharacterResolver(),
    NCMResolver(),
]
PREVALENCES = [0.0, 0.05, 0.10, 0.20, 0.30]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


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
    return tags


def score(scenarios, resolver) -> dict[str, float]:
    total = correct = 0
    tag_total = defaultdict(int)
    tag_errors = defaultdict(int)
    for scenario in scenarios:
        for query in scenario.queries:
            answer = resolver.answer(scenario, query)
            ok = answer == query.expected
            total += 1
            correct += int(ok)
            for tag in eligible_error_tags(scenario.template, query.kind, query.expected):
                tag_total[tag] += 1
                tag_errors[tag] += int(answer == "yes") if tag == "unauthorized_disclosure" else int(not ok)
    return {
        "accuracy": correct / total,
        "cross_instance_error_rate": tag_errors["cross_instance"] / max(1, tag_total["cross_instance"]),
        "cross_world_error_rate": tag_errors["cross_world"] / max(1, tag_total["cross_world"]),
        "unauthorized_disclosure_rate": tag_errors["unauthorized_disclosure"] / max(1, tag_total["unauthorized_disclosure"]),
    }


def run(seed: int, per_template: int, replicates: int, output_dir: Path) -> dict[str, object]:
    started = time.perf_counter()
    base = generate_scenarios(seed=seed, per_template=per_template)
    run_rows: list[dict[str, object]] = []

    for prevalence in PREVALENCES:
        for replicate in range(replicates):
            dataset_seed = seed + int(prevalence * 10_000) + replicate * 7_919
            corrupted = corrupt_dataset(base, prevalence=prevalence, seed=dataset_seed, cascade_probability=0.35)
            corrupted_count = sum(1 for s in corrupted if s.metadata.get("corruption_modes"))
            for resolver in SYSTEMS:
                run_rows.append({
                    "prevalence": prevalence,
                    "replicate": replicate,
                    "dataset_seed": dataset_seed,
                    "system": resolver.name,
                    "n_scenarios": len(corrupted),
                    "n_corrupted_scenarios": corrupted_count,
                    **score(corrupted, resolver),
                })

    summary_rows: list[dict[str, object]] = []
    grouped: dict[tuple[float, str], list[dict[str, object]]] = defaultdict(list)
    for row in run_rows:
        grouped[(float(row["prevalence"]), str(row["system"]))].append(row)
    for (prevalence, system), rows in sorted(grouped.items()):
        out: dict[str, object] = {"prevalence": prevalence, "system": system, "replicates": len(rows)}
        for metric in ["accuracy", "cross_instance_error_rate", "cross_world_error_rate", "unauthorized_disclosure_rate"]:
            values = [float(r[metric]) for r in rows]
            out[f"{metric}_mean"] = statistics.fmean(values)
            out[f"{metric}_sd"] = statistics.stdev(values) if len(values) > 1 else 0.0
            out[f"{metric}_min"] = min(values)
            out[f"{metric}_max"] = max(values)
        summary_rows.append(out)

    mode_rows: list[dict[str, object]] = []
    for mode_index, mode in enumerate(CORRUPTION_MODES):
        rr = random.Random(seed + mode_index * 104_729)
        corrupted = [corrupt_scenario(s, mode, rr) for s in base]
        effective = sum(1 for s in corrupted if s.metadata.get("corruption_effective") != "False")
        for resolver in SYSTEMS:
            mode_rows.append({
                "mode": mode,
                "system": resolver.name,
                "n_scenarios": len(corrupted),
                "n_effective": effective,
                **score(corrupted, resolver),
            })

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "extraction_noise_runs.csv", run_rows)
    write_csv(output_dir / "extraction_noise_summary.csv", summary_rows)
    write_csv(output_dir / "extraction_noise_by_mode.csv", mode_rows)
    manifest = {
        "study": "NCM-Psi v0.2 correlated structured fault injection",
        "interpretation": "structured intervention study; not a natural extractor accuracy claim",
        "seed": seed,
        "per_template": per_template,
        "replicates": replicates,
        "prevalences": PREVALENCES,
        "corruption_modes": CORRUPTION_MODES,
        "n_base_scenarios": len(base),
        "python": sys.version,
        "platform": platform.platform(),
        "elapsed_seconds": time.perf_counter() - started,
    }
    (output_dir / "extraction_noise_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"summary": summary_rows, "by_mode": mode_rows, "manifest": manifest}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument("--per-template", type=int, default=24)
    parser.add_argument("--replicates", type=int, default=20)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "results")
    args = parser.parse_args()
    results = run(args.seed, args.per_template, args.replicates, args.output_dir)
    print("NCM-Ψ v0.2 correlated fault-injection pilot")
    for row in results["summary"]:
        print(
            f"p={row['prevalence']:.2f} {row['system']}: "
            f"accuracy={row['accuracy_mean']:.4f}±{row['accuracy_sd']:.4f}, "
            f"cross_instance_error={row['cross_instance_error_rate_mean']:.4f}, "
            f"unauthorized_disclosure={row['unauthorized_disclosure_rate_mean']:.4f}"
        )


if __name__ == "__main__":
    main()
