# Track E v0.2 Canonical P0 Result

**Status:** fixed deterministic development result  
**Date:** 2026-08-17  
**Workflow runs:** `32018731996`, normalization rerun `32019088890`  
**Artifacts:** `9284507228`, normalized `9284636274`

## 1. Result boundary

This P0 evaluates two independently implemented observers over the canonical Track S event contract:

- `G_generic_observer_v0.2`
- `T_typed_observer_v0.2`

Both receive the same faulty event history, query, observer surface, external commitment, and projection rows. It is a fixed author-designed audit, not a population sample. Results are exact counts only.

## 2. Fixed suite

```text
21 archetypes
  14 fault archetypes
    13 declared identifiable under the provided observer surface
     1 declared non-identifiable without an external witness
   7 complex clean controls
42 observer-case rows
```

Observer surfaces:

```text
BYTES                   1
LOCAL_SCHEMA            2
SEMANTIC_JOURNAL       11
EXTERNAL_COMMITMENT     4
PROJECTION_COMMITMENT   3
```

Fault coverage includes duplicate/tampered IDs, invalid references, principal/mind mismatch, unauthorized replication, transfer from an unexposed source, identity-fork collapse, invalid snapshot membership, forward-reference policy laundering, fake independent support, committed omission/tamper/reordering, stale projection state, and one unwitnessed omission.

Clean controls include valid declassification, forward-reference independent support, backdated policy revision, explicit snapshot restoration, authorized replication, a committed clean journal, and a clean projection commitment.

## 3. Primary fixed-suite result

For both observers:

```text
identifiable fault detection:   13 / 13
clean-control false alarms:      0 / 7
non-identifiable alerts:         0 / 1
G/T detection-containment disagreements: 0
```

The no-witness dropped-revoke case remains undetected by both observers at the semantic-journal surface. Both then return the wrong disclosure answer without containment. This is the expected impossibility result: a history with an omitted event is not distinguishable from a shorter valid history when no surviving commitment, receipt, peer log, or projection binds the missing event.

Consequently:

```text
silent incorrect use among all fault archetypes: 1 / 14
silent incorrect use among declared identifiable faults: 0 / 13
```

## 4. Localization result

After normalizing typed row/object IDs back to source journal event IDs:

```text
mutated-event hit given detection:       12 / 13 = 0.9231
mean candidate-set size:                 2.6154
exact responsible-set match:             1 / 13 = 0.0769
```

The low exact-set rate is not hidden. Current observers are good at containment-level detection but frequently return a violated constraint plus a superset or subset of the minimal causal event set. Localization remains an open engineering/research target.

The result also demonstrates why the historical v0.1 metric named `exact_localization_given_detection` was misleading: intersecting one mutated identifier is materially easier than returning the complete minimal responsible set.

## 5. Forward-reference result

Both observers detect:

- a public derived record inserted before its private parent;
- an independence-requiring justification inserted before its same-origin evidence members.

Validation indexes the complete visible relation before evaluating cross-event derivation/support invariants. Append order therefore does not create the two v0.1 bypasses.

## 6. Commitment result

An authenticated out-of-band journal commitment detects:

- omission of a committed revoke;
- content tampering;
- append-order change.

A projection-bound commitment detects stale derived rows even when the underlying journal is unchanged.

The envelope is not represented merely as another removable journal event. Missing external commitment delivery is a distinct observer state.

## 7. Generic-versus-typed result

The fixed suite shows no detection/containment advantage for the typed observer:

```text
G identifiable detection recall = T identifiable detection recall = 1.0
G clean false-alarm rate         = T clean false-alarm rate         = 0.0
G/T outcome disagreements        = 0
```

This is a useful negative/neutral result, not a failure to report. Under a sufficiently complete observer and equal information, the generic program can enforce the same declared invariants on these archetypes.

Potential typed advantages remain untested in this P0:

- earlier write-time prevention;
- diagnostic specificity after implementation hardening;
- smaller repair/replay blast radius;
- lower operator effort;
- lower or higher runtime/storage/migration cost;
- robustness under concurrency, partial transactions, stale indexes, and held-out fault topologies.

## 8. Limitations

1. The archetypes are hand designed and small.
2. Seven clean controls do not establish a general zero-false-alarm rate.
3. Detection happens before answering; production systems require explicit containment policies and availability trade-offs.
4. Repair, replay, residue cleanup, and cost are not yet implemented.
5. Several alerts return broad candidate sets.
6. External commitments are modeled as trusted inputs; key management, delivery failure, checkpoint rotation, and forked commitment chains require a separate threat-model implementation.
7. No concurrent or crash-consistency fault is included yet.
8. No inferential statistics are attached.

## 9. Reproducibility

Committed deterministic outputs:

- `results/track_e_v02_p0/rows.csv`
- `results/track_e_v02_p0/summary.json`

Environment-stamped metadata:

- `results/track_e_v02_p0/run_metadata.json`

The workflow regenerates the deterministic files into `/tmp`, diffs them against the committed copies, and uploads all run outputs.

## 10. Next deciding experiment

The next Track E increment should retain the same fault semantics but add matched physical execution:

1. journal append versus projection transaction boundaries;
2. duplicate/out-of-order replay;
3. partial snapshot restore;
4. concurrent transfer and policy revocation;
5. stale availability/attribution/index projections;
6. repair/rebuild operations and independently verified residue;
7. localization candidate-set and operator-action measurements;
8. matched cost accounting for G and T.

The comparative claim remains falsifiable: if complete generic G matches or exceeds typed T on silent-failure prevention, localization, repair, safety, and cost, the typed enforcement contribution is narrowed or rejected.
