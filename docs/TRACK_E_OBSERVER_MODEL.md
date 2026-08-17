# Track E Observer and Identifiability Model

**Status:** pre-outcome freeze candidate  
**Date:** 2026-08-17

## 1. Purpose

Fault detection is meaningful only relative to the trusted information available to the observer. Track E therefore separates:

- semantic invalidity of a received history;
- inconsistency with an external commitment;
- stale or divergent derived state;
- omissions that leave no surviving witness.

No detector is credited for information it was not given.

## 2. Trusted surfaces

Let `J` be the received append-only journal, `C` an independently authenticated commitment, and `P` a derived projection.

### O0 — bytes only

Trusted input:

```text
received event bytes
```

Can detect malformed encoding and conflicting duplicate identifiers. It cannot infer missing expected events.

### O1 — locally typed journal

Trusted input:

```text
J + local event schemas/enums/reference domains
```

Can detect local and referential violations. It cannot establish cross-event lifecycle consistency that requires replay.

### O2 — complete semantic journal

Trusted input:

```text
J + canonical Track S transition semantics
```

Can detect unauthorized transfer, impossible adoption, invalid snapshot membership, attribution/lineage conflicts, policy laundering, and other violations entailed by surviving events.

### O3 — externally committed journal

Trusted input:

```text
J + authenticated C_journal
```

`C_journal` commits to at least:

```text
stream identity
monotonic sequence range
ordered event identifiers
canonical event hashes or Merkle root
commitment issuer/key id
commitment time and previous commitment
```

Can detect committed omissions, insertion, reordering, and tampering. The commitment is not stored solely inside the mutable journal it protects. Missing or invalid commitment delivery is itself a distinct state, not silent success.

### O4 — projection-bound commitment

Trusted input:

```text
J + C_journal + P + C_projection
```

`C_projection` binds:

```text
projection kind/version
journal stream id and committed head
schema/configuration hashes
rebuild/checkpoint metadata
projection content hash or verification sample
```

Can detect stale caches, indexes, summaries, or projections built from the wrong journal head.

## 3. Identifiability classes

A fault is classified by the weakest observer surface that can distinguish it from a valid history.

```text
local_bytes
local_schema
referential
semantic
journal_commitment
projection_commitment
non_identifiable_under_declared_surfaces
```

The class is justified by a witness, not assigned only from the intended detector outcome.

For each fault archetype, publish:

- a valid history `H0`;
- a faulty history or state `H1`;
- the trusted observer surface;
- the smallest distinguishing witness;
- the expected responsible event/constraint set;
- a paired argument if the fault is non-identifiable.

## 4. Omission impossibility condition

Suppose `H0` contains event `e` and `H1 = H0 \ {e}`. If the observer receives only `H1`, and there is no surviving event, sequence commitment, receipt, peer log, policy command, or external projection that entails the existence of `e`, then `H1` may be a valid complete history under the same schema.

No deterministic detector can distinguish the two histories from the declared surface alone.

This is reported as non-identifiability, not detector failure.

## 5. Envelope security requirements

An integrity envelope used as O3 evidence must be:

- authenticated independently of the journal;
- bound to one stream and sequence interval;
- append-linked or checkpoint-linked to a previous trusted commitment;
- canonicalization-versioned;
- replay/fork detectable;
- available through a delivery/audit path whose absence is observable.

An unauthenticated envelope stored only as another mutable event in `J` does not provide omission evidence if an attacker can remove or alter both the target event and the envelope.

## 6. Localization contracts

Detection and localization are separate.

For a known responsible set `R` and detector candidate set `D`:

```text
mutated_event_hit       = 1 if D intersects R else 0
localization_precision  = |D intersect R| / |D|       # undefined/0 when D empty
responsible_recall      = |D intersect R| / |R|
exact_responsible_set   = 1 if D == R else 0
candidate_set_size      = |D|
```

When several minimal causal sets are valid, score against the declared family of acceptable sets.

The old v0.1 `exact_localization_given_detection` metric is retained only as a historical label; its implementation measured `mutated_event_hit`.

## 7. Clean controls

Clean controls must include complex benign histories that exercise the same surfaces as faults:

- explicit valid forward-reference policy or rejected forward references;
- lawful declassification with preserved provenance;
- multi-hop derivation without laundering;
- idempotent duplicate replay;
- late backdated correction with valid/system-time semantics;
- explicit snapshot-manifest partial restore;
- authorized replication followed by later authorization revocation;
- child-world reconstruction with a late import about pre-fork valid state;
- independent public support plus protected alternative support;
- stale-looking but correctly head-bound projection rebuild.

Identifier renaming tests invariance but does not add semantic clean-control diversity.

## 8. Track E v0.2 comparison

Generic and typed implementations receive the same canonical events and external commitments.

They may differ in:

- when a violation is prevented or detected;
- diagnostic specificity;
- projection structure;
- repair/replay strategy;
- cost.

They may not differ in available facts, expected-event commitments, fault labels, or query answers encoded in input.

A G/T tie is a valid result. A typed advantage must survive matched information, observer surface, fault schedule, and implementation maturity.
