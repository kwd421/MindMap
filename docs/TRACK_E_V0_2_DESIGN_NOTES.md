# Track E v0.2 Canonical Fault-Harness Design Notes

**Status:** working coordination note  
**Date:** 2026-08-17

Track E v0.2 will be built on the canonical `mindmap.canonical` event contract and the complete G/T implementations that passed Track S.

The fixed v0.1 observer-tier audit remains a source of fault archetypes, not the comparative result.

## Required architecture

```text
Canonical CommonEvent history
        |
        +--> independent semantic validity oracle
        |
        +--> Generic physical projection + generic validator
        |
        +--> Typed physical projection + typed validator
        |
        +--> independently authenticated integrity commitment
```

## Observer surfaces

Every result declares exactly which information is trusted and visible:

1. `journal_only` — received event bytes and their append order;
2. `semantic_state` — complete journal plus canonical invariants;
3. `external_commitment` — journal plus authenticated expected sequence/head/object commitments;
4. `projection_commitment` — external journal head plus projection/index head and rebuild manifest.

An omission is detectable only when some surviving trusted surface commits to the missing object or transition.

## First implementation gates

- two-pass cross-event validation;
- no forward-reference order dependence;
- bitemporal policy selection;
- explicit authorization lifecycle;
- explicit snapshot-manifest membership;
- world-branch valid/system-time semantics reused from Track S;
- source-family-aware alternative support paths;
- exact responsible-set and candidate-set localization metrics;
- clean controls substantially larger than fault-label renamings;
- deterministic fixed-suite counts only.

## Initial endpoints

- detection precision/recall by observer surface;
- silent incorrect-state/use rate;
- quarantine/containment correctness;
- mutated-event hit rate;
- localization precision and candidate-set size;
- exact responsible-set match where identifiable;
- post-replay semantic conformance;
- residue in projections/indexes/caches;
- events reprocessed and time to recovery;
- write, validation, rebuild, and storage cost.

## Integration rule

No Track E branch may replace the canonical root schema or protocol. It integrates into `research/v0.2-reconciled` through a focused PR after its deterministic outputs regenerate in CI.
