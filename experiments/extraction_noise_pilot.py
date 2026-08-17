#!/usr/bin/env python3
"""Fault-injection study for NCM³-E metadata extraction.

A critical structured record is corrupted with marginal probability p. We
compare one extraction pass with three-pass majority consensus under controlled
error correlation rho.

For the deterministic binary record corruption used here:

    p_shared = rho * p
    p_ind = (p - p_shared) / (1 - p_shared)
    p_majority = p_shared + (1-p_shared) * (3*p_ind**2 - 2*p_ind**3)

The model is deliberately controlled and is not claimed to match empirical LLM
extraction errors, which are likely correlated and field-dependent.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "src", ROOT / "experiments"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from mindmap import EpistemicBranchStore, MemoryEvent, SYSTEM_CONFIGS, UNKNOWN  # noqa: E402
from epistemic_branch_pilot import PRINCIPALS, generate_scenario  # noqa: E402


def deterministic_corruption(event: MemoryEvent) -> MemoryEvent:
    if event.branch == "main":
        branch = "alt"
    elif event.branch == "alt":
        branch = "main"
    else:
        branch = "root"

    pivot = sum(ord(char) for char in event.id) % len(PRINCIPALS)
    principal = PRINCIPALS[pivot]

    audience = set(event.audience)
    if principal in audience:
        audience.remove(principal)
    else:
        audience.add(principal)

    acl = set(event.read_acl)
    if principal in acl:
        acl.remove(principal)
    else:
        acl.add(principal)
    if pivot % 2 == 0:
        acl.discard("admin")
    else:
        acl.add("admin")

    return replace(
        event,
        branch=branch,
        tx_time=event.tx_time + 2,
        audience=frozenset(audience),
        read_acl=frozenset(acl),
        trust=1.0 - event.trust,
        retracts=None,
    )


def consensus(events: tuple[MemoryEvent, MemoryEvent, MemoryEvent]) -> MemoryEvent:
    return Counter(events).most_common(1)[0][0]


def theoretical_majority_error(p: float, rho: float) -> float:
    shared = rho * p
    if shared >= 1:
        return 1.0
    independent = (p - shared) / (1 - shared)
    return shared + (1 - shared) * (
        3 * independent**2 - 2 * independent**3
    )


def make_replicas(
    events: list[MemoryEvent], p: float, rho: float, rng: random.Random
) -> tuple[list[MemoryEvent], list[MemoryEvent], float, float]:
    shared_p = rho * p
    independent_p = 0.0 if shared_p >= 1 else (p - shared_p) / (1 - shared_p)

    single: list[MemoryEvent] = []
    voted: list[MemoryEvent] = []
    single_errors = 0
    voted_errors = 0

    for event in events:
        bad = deterministic_corruption(event)
        shared = rng.random() < shared_p
        replicas = tuple(
            bad if shared or rng.random() < independent_p else event
            for _ in range(3)
        )
        first = replicas[0]
        majority = consensus(replicas)
        single.append(first)
        voted.append(majority)
        single_errors += int(first != event)
        voted_errors += int(majority != event)

    n = len(events)
    return single, voted, single_errors / n, voted_errors / n


def evaluate(events: list[MemoryEvent], queries) -> dict[str, float]:
    store = EpistemicBranchStore()
    store.extend(events)
    correct = 0
    unknown_n = 0
    leaks = 0
    branch_errors = 0
    for query in queries:
        prediction = store.resolve(query, **SYSTEM_CONFIGS["NCM3E"]).answer
        correct += int(prediction == query.answer)
        if query.answer == UNKNOWN:
            unknown_n += 1
            leaks += int(prediction != UNKNOWN)
        branch_errors += int(
            prediction in query.alt_branch_values and prediction != query.answer
        )
    return {
        "AnswerAcc": correct / len(queries),
        "LeakRate_on_unknown": leaks / unknown_n if unknown_n else 0.0,
        "BranchContaminationRate": branch_errors / len(queries),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenarios", type=int, default=250)
    parser.add_argument("--repetitions", type=int, default=12)
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()

    generator_rng = random.Random(args.seed)
    events: list[MemoryEvent] = []
    queries = []
    for index in range(args.scenarios):
        scenario_events, scenario_queries = generate_scenario(index, generator_rng)
        events.extend(scenario_events)
        queries.extend(scenario_queries)

    rows: list[dict[str, object]] = []
    for rho in (0.0, 0.5, 0.9):
        for p in (0.0, 0.01, 0.05, 0.10, 0.20, 0.30):
            for repetition in range(args.repetitions):
                rng = random.Random(
                    args.seed
                    + repetition * 100_003
                    + int(p * 10_000)
                    + int(rho * 1_000_000)
                )
                single, majority, single_error, majority_error = make_replicas(
                    events, p, rho, rng
                )
                for method, corrupted, observed_error in (
                    ("single-pass", single, single_error),
                    ("triple-majority", majority, majority_error),
                ):
                    metrics = evaluate(corrupted, queries)
                    rows.append({
                        "method": method,
                        "p_target": p,
                        "rho": rho,
                        "repetition": repetition,
                        "representation_error_observed": observed_error,
                        "representation_error_theory": (
                            p
                            if method == "single-pass"
                            else theoretical_majority_error(p, rho)
                        ),
                        **metrics,
                    })

    detail = pd.DataFrame(rows)
    summary = (
        detail.groupby(["method", "p_target", "rho"], as_index=False)
        .agg(
            N_runs=("AnswerAcc", "size"),
            RepresentationError=("representation_error_observed", "mean"),
            RepresentationErrorTheory=("representation_error_theory", "mean"),
            AnswerAccMean=("AnswerAcc", "mean"),
            AnswerAccSD=("AnswerAcc", "std"),
            LeakRateMean=("LeakRate_on_unknown", "mean"),
            BranchContaminationMean=("BranchContaminationRate", "mean"),
        )
        .sort_values(["rho", "p_target", "method"])
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    detail.to_csv(args.output_dir / "extraction_noise_pilot_runs.csv", index=False)
    summary.to_csv(args.output_dir / "extraction_noise_pilot_summary.csv", index=False)
    metadata = {
        "benchmark": "NCM-EpiBranch-Synth v0.1 fault injection",
        "seed": args.seed,
        "scenarios": args.scenarios,
        "events": len(events),
        "queries": len(queries),
        "repetitions": args.repetitions,
        "error_model": (
            "deterministic binary critical-record corruption with shared and "
            "independent components"
        ),
        "formula": (
            "p_shared=rho*p; p_ind=(p-p_shared)/(1-p_shared); "
            "p_maj=p_shared+(1-p_shared)*(3*p_ind^2-2*p_ind^3)"
        ),
        "warning": (
            "Independent or partially correlated synthetic faults are not an "
            "empirical model of LLM extraction errors."
        ),
    }
    (args.output_dir / "extraction_noise_pilot_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(summary.to_string(index=False))
    print(f"\nWrote results to {args.output_dir}")


if __name__ == "__main__":
    main()
