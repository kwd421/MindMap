# Exploratory Results Status and Correction Ledger

**Status:** factual audit of pre-reconciliation synthetic artifacts  
**Date:** 2026-08-17

This file keeps completed exploratory observations outside the canonical preregistration. Nothing here is confirmatory evidence under `PREREG_V0_2.md`.

## 1. PR #3: NCM-EpiBranch-Synth scaffold

### Verified repository facts

The branch `research/ncm3e-v0.2` contains a deterministic generator, resolver, tests, a synthetic fault-injection script, result tables, and CI configuration.

The committed metadata reports 250 scenarios, 3,250 events, 5,250 queries, and a clean `NCM3E` score of 1.0.

### Critical validity finding

In `experiments/epistemic_branch_pilot.py`, the query helper constructs the gold answer by invoking:

```python
store.resolve(provisional, **SYSTEM_CONFIGS["NCM3E"])
```

Evaluation later invokes the same resolver and configuration. The clean score is therefore resolver self-agreement by construction, not independent semantic accuracy.

### Additional code findings

1. The branch-ancestry resolver has no fork-valid-time cutoff; all ancestor events are eligible subject only to query time, so a parent event after a child-world fork can leak into the child.
2. The headline `EpistemicTemporalLatest` versus `NCM3E` comparison changes both trust ranking and retraction handling, so it is not a one-factor ablation.
3. The bootstrap and exact paired test operate on correlated question rows even though multiple questions share one scenario.
4. The checked-in metadata contains a test-count field that the checked-in experiment entry point does not write, preventing byte-for-byte regeneration from one command.
5. `WORLD_UPDATE` records can enter belief resolution and are ranked by trust before recency; because the same resolver generates gold, a questionable stale result can still score as correct.

### Permitted label

> Deterministic resolver self-consistency and implementation-scaffold smoke test.

### Not established

- independent schema conformance;
- component necessity;
- branch-fork semantics;
- end-to-end extraction;
- real raw-evidence robustness;
- public benchmark benefit.

## 2. Main: 48-case collision audit

### Verified repository facts

The committed script enumerates:

```text
6 case labels × 4 policy labels × 2 support labels = 48 cases
48 cases × 4 decisions = 192 decisions per named rule function
```

The committed rule code reproduces the two basic aggregate fields written by the script, including:

```text
full rule function             = 1.0000 decision accuracy
strongest named incomplete rule = 0.9375 decision accuracy
exact fixed-suite difference    = 12 / 192 decisions
```

### Critical validity findings

1. The full predictor mirrors the semantic functions used by the gold generator; perfect agreement is expected.
2. Cases directly expose categorical labels such as lineage, transfer, stance, policy, and support rather than exercising the committed normalized schema.
3. The script does not implement principals versus mind instances, world branches, valid/system time, restore manifests, historical exposure, requesters, merge authorization, policy-event propagation, or actual justification members.
4. `JustificationSet` is reduced to a Boolean independent-public-support label.
5. Operational-replica state replication grants first-person status without testing the schema's authorization contract.
6. The committed summary file contains additional category/safety fields that the committed script does not generate.
7. The script contains no bootstrap, seed, confidence-interval, or exact-test analysis.
8. The reported two-sided `p=0.000488` corresponds to 12 decision-level wins and treats four decisions within one case as independent. At the case level, the analogous 8-win sign calculation is `0.0078125`, but neither value supports population inference because the 48 cases are a fixed author-selected Cartesian suite.

### Permitted label

> Deterministic truth-table discriminability and reference-rule smoke test.

### Appropriate reporting

- exact per-case and per-decision counts;
- no population-inference p-value or bootstrap interval;
- no use as a confirmatory effect-size estimate;
- no architecture claim against an information-complete generic ledger.

## 3. Earlier issue-reported 1,000-scenario / 25,000-question table

A separate Issue #1 report described 1,000 scenarios, 16 events per scenario, and 25,000 questions, including an idealized confidence-triggered raw-fallback simulation.

At the time of audit, the exact generator, evaluator, per-scenario output, corruption implementation, fallback confidence model, bootstrap code, and immutable run manifest for that table were not available in the reviewed repository artifacts.

### Permitted label

> Session-reported, unverified symbolic conformance output with an idealized fallback simulation.

It must not be conflated with the committed 250-scenario PR #3 experiment or the committed 48-case truth table.

## 4. Result-regeneration requirements

Before any exploratory table is upgraded to reproducible status:

- one committed entry point regenerates every committed result column;
- per-decision and per-scenario artifacts are committed or content-hashed in an immutable release;
- the run manifest records code SHA, configurations, environment, seeds, topology IDs, and output hashes;
- fixed deterministic suites report exact counts only;
- hidden/stochastic suites use topology/scenario-clustered analysis;
- gold generation is independent from candidate resolvers;
- one-feature ablations change exactly one mechanism;
- all failures and exclusions are retained.

## 5. Relationship to the canonical preregistration

The reconciled preregistration defines three new tracks:

- Track S: independent semantic conformance, expecting complete equal-information systems to agree;
- Track E: lifecycle enforcement and fault behavior;
- Track X: end-to-end extraction and held-out topology generalization.

No observation in this document is a confirmatory result for those tracks.
