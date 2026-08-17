# Track E v0.1 Independent Code Audit

**Reviewer:** Session B  
**Date:** 2026-08-17  
**Reviewed source hash:** `636da65603e958fc9a877e67f634204ebd8517cd03f7891c7b0255a87e1ecbd6`  
**Reproduction run:** `32016372934`

## Verified result boundary

The fixed script reproduces its deterministic fields exactly in GitHub Actions. Its current scientific object is:

> a fixed observer-tier fault-observability audit over author-selected synthetic event histories.

Verified:

- 17 archetypes: 14 observable faults, 1 deliberately non-identifiable omission, and 2 clean controls;
- 20 alpha-renamings per archetype;
- 6 validator labels;
- complete generic/typed pairs have identical outcomes because they share the same invariant functions;
- envelope-labelled pairs detect the three cases backed by a surviving commitment;
- the no-witness dropped-revoke case remains non-identifiable;
- deterministic result CSVs and the source hash regenerate in CI.

Not established:

- an independent generic-versus-typed implementation advantage;
- population-level detection rates;
- robust false-alarm behavior outside two clean archetypes;
- exact/minimal fault localization;
- repair, containment, residue cleanup, crash/replay behavior, or production cost;
- alignment with the canonical Track S event contract.

## Blocking findings

### 1. Architecture labels share implementation

`G-Complete` and `T-Canonical` both call `semantic_alerts`; `G-Envelope` and `T-Envelope` both call `envelope_alerts`. Equality is expected and useful as an observer-tier control, but it is not an independent physical implementation comparison.

### 2. Alpha-renamings are invariance checks

The 20 variants are exact identifier renamings. They should demonstrate name invariance, not increase the independent sample count. Report exact archetype coverage and separately state the number of renaming checks.

### 3. Localization metric is not exact

Current success condition:

```text
any(alert.event_id in mutated_ids)
```

A detector may emit many unrelated candidates and still score 1. Rename the metric to `mutated_event_hit_rate`. Add:

- candidate-set size;
- localization precision;
- exact responsible-set match;
- smallest correct causal set where identifiable.

### 4. Envelope requires an external trust anchor

The in-ledger envelope is not self-protecting. If both a target event and the envelope are removed, the remaining ledger produces no alert. The integrity contract must specify an independently authenticated expected envelope/receipt/sequence commitment whose absence is observable.

### 5. Single-pass semantic validation is order-dependent

Two reproduced bypasses:

1. a public derived event recorded before its private parent produces no `policy_laundering` alert;
2. an independence-requiring justification recorded before two same-origin evidence rows produces no `non_independent_support` alert.

Use a two-pass validator that indexes complete visible state before validating cross-event derivation/support relations, or explicitly reject forward references.

### 6. Policy selection is not bitemporal

`policy_allows` sorts by valid time before system time. A late-recorded backdated revoke can be incorrectly overridden by an older-recorded grant with a later valid time. Disclosure queries need an explicit valid-time coordinate and the canonical `(valid_time, system_time)` revision semantics.

### 7. Event contract predates canonical Track S

The v0.1 script uses:

- inline `authorized` booleans;
- snapshot entry lists without manifest attributes;
- simplified branch, attribution, and policy state;
- no explicit authorization lifecycle.

Track E v0.2 must inject faults into the canonical `mindmap.canonical` common events and complete G/T implementations that passed Track S.

### 8. Clean-control coverage is insufficient

Two clean archetypes repeated by identifier renaming do not substantiate a general zero-false-alarm claim. Add benign controls for:

- legitimate forward references or explicitly rejected forward references;
- valid declassification;
- multi-hop derivation;
- duplicate idempotent replay;
- backdated but valid policy updates;
- explicit snapshot-manifest restore;
- authorized replication and later revocation;
- child-branch late import about pre-fork valid state.

### 9. Disclosure resolver can see future justifications

`resolve_query(... DISCLOSE ...)` selects all matching justifications without applying `justification.system_time <= query.system_time`. Add before/after-justification controls and fix point-in-system-time filtering.

### 10. Timing is environment-specific

The workflow now verifies deterministic fields while ignoring latency drift. Timings should remain run artifacts with platform metadata, not invariant committed outputs.

## Required disposition

Track E v0.1 may be integrated only as:

> a fixed observer-tier mechanism audit and source of candidate fault archetypes.

It must not be used as the confirmatory G-versus-T result.

The next experiment should use:

1. the canonical common-event contract;
2. independently implemented generic and typed validation/projection paths;
3. an explicit observer/trust model;
4. matched semantic and physical fault mappings;
5. separate detection, containment, localization, repair, residue, and cost endpoints;
6. exact fixed-suite counts before any held-out or stochastic analysis.
