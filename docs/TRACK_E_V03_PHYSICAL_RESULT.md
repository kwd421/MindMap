# Track E v0.3 Matched Physical Fault P1

**Status:** fixed deterministic development result  
**Date:** 2026-08-17  
**Workflow run:** `32026971500`  
**Artifact:** `9290509186`

## 1. Research question

Given the same canonical event history, queries, external journal witness, and projection witness, do the generic and typed physical implementations differ in their ability to detect and repair journal/projection divergence?

This P1 models physical state as:

```text
received append-only journal
+ materialized query projection
+ projection's source-journal head
+ optional authenticated authoritative journal head/content
+ optional projection content commitment
```

Both implementations use full deterministic replay/rebuild for repair. This is a fixed author-designed suite and receives exact counts only.

## 2. Fixed suite

```text
15 archetypes
  12 physical fault archetypes
    11 identifiable under the declared witnesses
     1 non-identifiable omission
   3 clean controls
30 implementation-case rows
```

Faults:

1. revoke appended, projection update crashes;
2. self-seal appended, projection update crashes;
3. restore lineage absent from projection;
4. authorized replication absent from projection;
5. revoked private support remains in projection;
6. late pre-fork import absent from projection;
7. externally committed revoke omitted from the received journal;
8. externally committed append order changed;
9. duplicate event replayed into the journal;
10. projection answer row corrupted while journal/head remain unchanged;
11. projection bound to a wrong but answer-equivalent journal head;
12. revoke omitted without an external journal or projection witness.

Clean controls:

- fully synchronized ordinary temporal state;
- synchronized authenticated revocation;
- synchronized snapshot/restore projection.

## 3. Fixed result

For both `G_generic_physical_v0.3` and `T_typed_physical_v0.3`:

```text
identifiable detection:                11 / 11
clean-control false alarms:             0 / 3
silent incorrect use, identifiable:     0 / 11
repair success after detection:        11 / 11
total answer residue after repair:      0
journal-commitment mismatches:           3
projection-head mismatches:              8
projection-content mismatches:           8
G/T outcome disagreements:               0
```

The no-witness omitted-revoke case remains undetected and returns one incorrect disclosure answer in both implementations:

```text
silent incorrect use among all faults: 1 / 12
```

This is the expected omission-impossibility result. A shorter received history cannot be distinguished from a valid complete history when no commitment, receipt, peer log, or projection binds the missing event.

## 4. Repair result

Every detected fault is repaired by replacing the received journal with the authoritative event history and rebuilding all registered projection rows.

For both implementations:

```text
mean events reprocessed per repair:      18.5455
mean query recomputations per repair:     2.1818
repair residue:                           0
```

The equality is expected: both physical stores currently use full replay and full registered-query recomputation. This P1 does not support a typed repair-cost advantage.

## 5. Witness decomposition

The suite separates three detection mechanisms:

### Authoritative journal mismatch

Detects omission, append-order changes, and duplicate replay relative to an independently authenticated expected journal.

### Projection-source-head mismatch

Detects projection state built from a journal prefix or alternative history even when selected answers happen to remain equal.

### Projection-content mismatch

Detects stale or corrupted projected answers relative to an independently bound expected projection content.

A fault may activate more than one witness. Metrics remain separate rather than blending all detection into one score.

## 6. Generic-versus-typed result

No generic-versus-typed detection, containment, repair, or full-rebuild-cost difference appears on this fixed suite.

This neutral result narrows the claim:

> With equal commitments and complete replay implementations, typed organization alone does not improve fixed-suite physical divergence detection or full-rebuild repair.

Potential differences remain open only where implementations genuinely differ:

- write-time prevention before a faulty physical state is committed;
- incremental dependency tracking and targeted repair;
- transaction boundaries and crash atomicity;
- concurrent transfer/revoke scheduling;
- stale secondary indexes, caches, and summaries;
- diagnostic specificity and operator effort;
- migration and schema-evolution behavior;
- storage, write amplification, and latency.

## 7. Important limitations

1. The suite is small and hand designed.
2. Three clean controls are insufficient for a general false-alarm claim.
3. External journal and projection commitments are treated as authenticated available inputs; key management and delivery availability are not implemented.
4. Repair uses an authoritative full event copy. Hash commitments alone cannot reconstruct omitted bytes.
5. Query projections are modeled as registered answer rows rather than full production tables/indexes.
6. No partial multi-row transaction, process crash, concurrent writer, or secondary-index residue is executed yet.
7. Full replay is deliberately simple and creates an equal repair-cost baseline.
8. No inferential statistics are attached.

## 8. Reproducibility

Committed deterministic outputs:

- `results/track_e_v03_physical/rows.csv`
- `results/track_e_v03_physical/summary.json`

Environment-stamped metadata:

- `results/track_e_v03_physical/run_metadata.json`

The workflow runs all tests, Track S, Track E v0.2 P0, and this P1. The next workflow revision diffs regenerated P1 rows/summary against the committed files and archives run outputs.

## 9. Next deciding experiment

The next increment should stop using full replay as the only repair policy and compare matched physical execution:

1. append and projection writes across explicit transaction boundaries;
2. crash after each write step;
3. duplicate and out-of-order replay with idempotency contracts;
4. concurrent transfer and revoke/deletion schedules;
5. stale availability, attribution, support, vector, and graph indexes;
6. dependency-indexed targeted repair versus full replay;
7. independently verified descendant/index/cache residue;
8. repair candidate-set, operator action count, write amplification, storage, and latency.

A neutral or generic-favorable result remains valid and would further narrow the typed enforcement contribution.
