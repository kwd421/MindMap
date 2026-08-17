#!/usr/bin/env python3
"""NCM³-E mechanism-isolation pilot.

This is not an end-to-end language benchmark. It tests state-resolution semantics
under branch divergence, valid/transaction time, perspective possession, caller
access control, provenance reliability, and retraction.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from mindmap import (  # noqa: E402
    EpistemicBranchStore,
    EventKind,
    MemoryEvent,
    MemoryQuery,
    QueryKind,
    SYSTEM_CONFIGS,
    UNKNOWN,
)

SEED = 20260817
PRINCIPALS = ("alice", "bob", "carol", "dave")
ALL_CALLERS = frozenset((*PRINCIPALS, "admin"))
PREDICATES = ("lives_in", "works_as", "favorite_food")
VALUES = (
    "Arbor Bay", "Cedar Falls", "Dawnport", "Elmstead", "Frosthaven",
    "Glenmoor", "Harborwick", "Ivydale", "Juniper City", "Kingswell",
    "Lakehurst", "Moonridge", "Northpass", "Opalton", "Pinecross",
    "paramedic", "librarian", "architect", "translator", "park ranger",
    "miso ramen", "lemon tart", "kimchi stew", "soba salad", "pumpkin soup",
)


def _event_text(subject: str, predicate: str, value: str, kind: EventKind, speaker: str) -> str:
    if kind is EventKind.WORLD_UPDATE:
        return f"Direct observation: {subject} now has {predicate} = {value}."
    if kind is EventKind.CORRECTION:
        return f"{speaker} corrected the record: {subject}'s {predicate} is {value}."
    if kind is EventKind.RETRACTION:
        return f"{speaker} retracted an earlier claim about {subject}'s {predicate}."
    return f"{speaker} claimed that {subject}'s {predicate} is {value}."


def generate_scenario(index: int, rng: random.Random) -> tuple[list[MemoryEvent], list[MemoryQuery]]:
    sid = f"s{index:04d}"
    subject = f"target-{index:04d}"
    predicate = rng.choice(PREDICATES)
    value0, value1, rumor, main_value, alt_value, secret_value = rng.sample(VALUES, 6)

    shuffled = list(PRINCIPALS)
    rng.shuffle(shuffled)
    root_witnesses = frozenset(shuffled[:2])
    correction_audience = frozenset(shuffled[1:3])
    secret_audience = frozenset(shuffled[:2])
    main_witnesses = frozenset((shuffled[0], shuffled[2]))
    alt_witnesses = frozenset((shuffled[1], shuffled[3]))
    main_correction_audience = frozenset((shuffled[0], shuffled[3]))
    alt_correction_audience = frozenset((shuffled[1], shuffled[2]))

    events: list[MemoryEvent] = []

    def add(
        eid: str,
        branch: str,
        event_time: int,
        tx_time: int,
        pred: str,
        value: str,
        kind: EventKind,
        speaker: str,
        audience: frozenset[str],
        read_acl: frozenset[str],
        trust: float,
        retracts: str | None = None,
    ) -> MemoryEvent:
        event = MemoryEvent(
            id=f"{sid}-{eid}",
            scenario_id=sid,
            branch=branch,
            event_time=event_time,
            tx_time=tx_time,
            subject=subject,
            predicate=pred,
            value=value,
            kind=kind,
            speaker=speaker,
            audience=audience,
            read_acl=read_acl,
            trust=trust,
            retracts=f"{sid}-{retracts}" if retracts else None,
            provenance=(),
            text=_event_text(subject, pred, value, kind, speaker),
        )
        events.append(event)
        return event

    # Common history. The second world update happened at valid time 3 but was
    # not entered into the memory ledger until transaction time 5.
    add("e01", "root", 1, 1, predicate, value0, EventKind.WORLD_UPDATE,
        "sensor", frozenset(PRINCIPALS), ALL_CALLERS, 1.00)
    add("e02", "root", 2, 2, predicate, rumor, EventKind.CLAIM,
        "rumor-source", frozenset(PRINCIPALS), ALL_CALLERS, 0.15)
    add("e03", "root", 3, 5, predicate, value1, EventKind.WORLD_UPDATE,
        "sensor", root_witnesses, ALL_CALLERS, 1.00)
    add("e04", "root", 4, 6, predicate, value1, EventKind.CORRECTION,
        "official", correction_audience, ALL_CALLERS, 0.95)

    # Separate secret key makes privacy leakage unambiguous.
    add("e05", "root", 4, 4, "secret_code", secret_value, EventKind.CLAIM,
        "keeper", secret_audience, frozenset((*secret_audience, "admin")), 0.90)

    # Divergent worldlines. Cross-branch rumors are intentionally late.
    add("m01", "main", 6, 6, predicate, main_value, EventKind.WORLD_UPDATE,
        "main-sensor", main_witnesses, ALL_CALLERS, 1.00)
    add("m02", "main", 7, 7, predicate, alt_value, EventKind.CLAIM,
        "main-rumor", frozenset(PRINCIPALS), ALL_CALLERS, 0.10)
    add("m03", "main", 8, 8, predicate, main_value, EventKind.CORRECTION,
        "main-official", main_correction_audience, ALL_CALLERS, 0.95)
    add("m04", "main", 9, 9, predicate, "", EventKind.RETRACTION,
        "main-rumor", frozenset(PRINCIPALS), ALL_CALLERS, 1.00, retracts="m02")

    add("a01", "alt", 6, 6, predicate, alt_value, EventKind.WORLD_UPDATE,
        "alt-sensor", alt_witnesses, ALL_CALLERS, 1.00)
    add("a02", "alt", 7, 7, predicate, main_value, EventKind.CLAIM,
        "alt-rumor", frozenset(PRINCIPALS), ALL_CALLERS, 0.10)
    add("a03", "alt", 8, 8, predicate, alt_value, EventKind.CORRECTION,
        "alt-official", alt_correction_audience, ALL_CALLERS, 0.95)
    add("a04", "alt", 10, 10, predicate, "", EventKind.RETRACTION,
        "alt-rumor", frozenset(PRINCIPALS), ALL_CALLERS, 1.00, retracts="a02")

    store = EpistemicBranchStore()
    store.extend(events)
    queries: list[MemoryQuery] = []

    def q(
        qid: str,
        branch: str,
        valid_at: int,
        tx_at: int,
        pred: str,
        kind: QueryKind,
        caller: str,
        viewpoint: str | None,
        category: str,
        alt_values: Iterable[str] = (),
        stale_values: Iterable[str] = (),
    ) -> None:
        provisional = MemoryQuery(
            id=f"{sid}-{qid}", scenario_id=sid, branch=branch,
            valid_at=valid_at, tx_at=tx_at, subject=subject, predicate=pred,
            kind=kind, caller=caller, viewpoint=viewpoint, answer=UNKNOWN,
            category=category, alt_branch_values=frozenset(alt_values),
            stale_values=frozenset(stale_values),
        )
        answer = store.resolve(provisional, **SYSTEM_CONFIGS["NCM3E"]).answer
        queries.append(MemoryQuery(**{**asdict(provisional), "answer": answer}))

    q("q-world-main", "main", 10, 10, predicate, QueryKind.WORLD, "admin", None,
      "world_current", (alt_value,), (value0, value1))
    q("q-world-alt", "alt", 10, 10, predicate, QueryKind.WORLD, "admin", None,
      "world_current", (main_value,), (value0, value1))

    for branch, other_value in (("main", alt_value), ("alt", main_value)):
        for principal in PRINCIPALS:
            q(f"q-belief-{branch}-{principal}", branch, 10, 10, predicate,
              QueryKind.BELIEF, "admin", principal, "belief_current",
              (other_value,), (value0, value1, rumor))
        for principal in shuffled[:2]:
            q(f"q-source-{branch}-{principal}", branch, 10, 10, predicate,
              QueryKind.SOURCE, "admin", principal, "source_attribution")

    for principal in (shuffled[0], shuffled[2]):
        q(f"q-before-tx-{principal}", "main", 4, 4, predicate,
          QueryKind.BELIEF, "admin", principal, "transaction_time",
          stale_values=(value1,))
        q(f"q-after-tx-{principal}", "main", 4, 6, predicate,
          QueryKind.BELIEF, "admin", principal, "transaction_time",
          stale_values=(value0, rumor))

    unwitnessed = next(
        p for p in PRINCIPALS
        if p not in main_witnesses and p not in main_correction_audience
    )
    q("q-authorized-unwitnessed", "main", 6, 6, predicate,
      QueryKind.BELIEF, "admin", unwitnessed, "access_not_knowledge",
      alt_values=(main_value,), stale_values=(value0, value1, rumor))

    witness = next(iter(secret_audience))
    outsider = next(p for p in PRINCIPALS if p not in secret_audience)
    q("q-witness-unauthorized", "main", 10, 10, "secret_code",
      QueryKind.BELIEF, outsider, witness, "knowledge_not_access",
      alt_values=(secret_value,))

    non_witness = next(p for p in PRINCIPALS if p not in secret_audience)
    q("q-admin-unwitnessed-secret", "main", 10, 10, "secret_code",
      QueryKind.BELIEF, "admin", non_witness, "access_not_knowledge",
      alt_values=(secret_value,))

    return events, queries


def evaluate(events: list[MemoryEvent], queries: list[MemoryQuery]) -> pd.DataFrame:
    store = EpistemicBranchStore()
    store.extend(events)
    rows: list[dict[str, object]] = []
    for system, config in SYSTEM_CONFIGS.items():
        for query in queries:
            resolution = store.resolve(query, **config)
            pred = resolution.answer
            rows.append({
                "system": system,
                "query_id": query.id,
                "scenario_id": query.scenario_id,
                "category": query.category,
                "branch": query.branch,
                "kind": query.kind.value,
                "caller": query.caller,
                "viewpoint": query.viewpoint,
                "gold": query.answer,
                "prediction": pred,
                "correct": int(pred == query.answer),
                "abstain_gold": int(query.answer == UNKNOWN),
                "abstain_pred": int(pred == UNKNOWN),
                "leak": int(query.answer == UNKNOWN and pred != UNKNOWN),
                "branch_contamination": int(
                    pred in query.alt_branch_values and pred != query.answer
                ),
                "stale_error": int(pred in query.stale_values and pred != query.answer),
                "evidence_id": resolution.evidence_id,
            })
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for system, group in df.groupby("system", sort=False):
        unknown = group[group.abstain_gold == 1]
        privacy = group[
            group.category.isin(["knowledge_not_access", "access_not_knowledge"])
        ]
        rows.append({
            "system": system,
            "N": len(group),
            "AnswerAcc": group.correct.mean(),
            "LeakRate_on_unknown": unknown.leak.mean() if len(unknown) else 0.0,
            "PrivacyLeakRate": privacy.leak.mean() if len(privacy) else 0.0,
            "BranchContaminationRate": group.branch_contamination.mean(),
            "StaleErrorRate": group.stale_error.mean(),
            "AbstentionRecall": (
                (unknown.abstain_pred == 1).sum() / len(unknown) if len(unknown) else 1.0
            ),
        })
    return pd.DataFrame(rows).sort_values("AnswerAcc", ascending=False)


def paired_stats(df: pd.DataFrame, baseline: str, proposed: str, seed: int) -> dict[str, object]:
    a = df[df.system == baseline].sort_values("query_id").correct.to_numpy()
    b = df[df.system == proposed].sort_values("query_id").correct.to_numpy()
    if len(a) != len(b):
        raise AssertionError("paired systems have different query counts")
    diff = b - a
    rng = np.random.default_rng(seed)
    boots = np.array([
        diff[rng.integers(0, len(diff), len(diff))].mean() for _ in range(10_000)
    ])
    proposed_only = int(((b == 1) & (a == 0)).sum())
    baseline_only = int(((a == 1) & (b == 0)).sum())
    p_value = float(
        binomtest(
            min(proposed_only, baseline_only),
            n=proposed_only + baseline_only,
            p=0.5,
        ).pvalue
    )
    return {
        "baseline": baseline,
        "proposed": proposed,
        "n": int(len(a)),
        "answer_accuracy_baseline": float(a.mean()),
        "answer_accuracy_proposed": float(b.mean()),
        "absolute_improvement": float(diff.mean()),
        "paired_bootstrap_95ci": [
            float(x) for x in np.quantile(boots, [0.025, 0.975])
        ],
        "discordant_proposed_only": proposed_only,
        "discordant_baseline_only": baseline_only,
        "mcnemar_exact_p": p_value,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenarios", type=int, default=250)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    events: list[MemoryEvent] = []
    queries: list[MemoryQuery] = []
    for index in range(args.scenarios):
        scenario_events, scenario_queries = generate_scenario(index, rng)
        events.extend(scenario_events)
        queries.extend(scenario_queries)

    results = evaluate(events, queries)
    summary = summarize(results)
    by_category = (
        results.groupby(["system", "category"], as_index=False)
        .agg(
            N=("correct", "size"),
            AnswerAcc=("correct", "mean"),
            LeakRate=("leak", "mean"),
            BranchContaminationRate=("branch_contamination", "mean"),
            StaleErrorRate=("stale_error", "mean"),
        )
    )
    stats = paired_stats(results, "EpistemicTemporalLatest", "NCM3E", args.seed)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_dir / "epistemic_branch_pilot_summary.csv", index=False)
    by_category.to_csv(
        args.output_dir / "epistemic_branch_pilot_by_category.csv", index=False
    )
    results.to_csv(
        args.output_dir / "epistemic_branch_pilot_query_level.csv", index=False
    )
    metadata = {
        "benchmark": "NCM-EpiBranch-Synth v0.1",
        "scope": "mechanism-isolation state-resolution pilot; not end-to-end language QA",
        "seed": args.seed,
        "scenarios": args.scenarios,
        "events": len(events),
        "queries": len(queries),
        "systems": list(SYSTEM_CONFIGS),
        "paired_comparison": stats,
        "limitations": [
            "Gold metadata is generated rather than extracted by an LLM.",
            "Subject and predicate routing are provided to the resolver.",
            "The experiment isolates state semantics and cannot establish public-benchmark SOTA.",
            "Events are synthetic and query templates are programmatic.",
        ],
    }
    (args.output_dir / "epistemic_branch_pilot_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(summary.to_string(index=False))
    print("\nPaired comparison")
    print(json.dumps(stats, indent=2))
    print(f"\nWrote results to {args.output_dir}")


if __name__ == "__main__":
    main()
