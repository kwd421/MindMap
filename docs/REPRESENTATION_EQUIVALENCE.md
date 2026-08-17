# Representation Equivalence and the Correct Empirical Claim

**Status:** reconciliation result candidate  
**Date:** 2026-08-17

## 1. Problem

Earlier drafts proposed comparing an explicit NCM-Ψ schema with a simpler baseline on oracle-structured questions. The full schema contained lineage, exposure, transfer, policy, and provenance primitives that the baseline either lacked or was not permitted to derive.

That comparison cannot identify an architectural advantage. It confounds representation with information availability.

## 2. Definitions

Let a typed ledger be a finite set of rows over the canonical relations, including:

```text
WorldBranch
Principal
MindInstance
MindPlacement
LineageEdge
EvidenceEvent
SourceAssertion
ClaimRevision
TransferEvent
BeliefAdoption
ExposureTransition
PolicyEvent
SnapshotManifestEntry
JustificationSet
JustificationMember
```

Let `Q` be a finite set of queries and `R_T` a deterministic typed resolver returning a target-conditioned state vector.

Let a generic ledger be a finite relation:

```text
GenericEvent(
  event_id,
  event_type,
  participant_ids,
  object_ids,
  about_world_branch_id,
  context_world_branch_id,
  valid_interval,
  system_interval,
  attributes,
  policy_reference,
  source_references
)
```

with a deterministic relational program `R_G`.

## 3. Proposition

For every finite typed ledger `L_T`, finite query set `Q`, and deterministic typed resolver `R_T`, there exists an encoding `E` into a generic ledger `L_G = E(L_T)` and a generic resolver `R_G` such that:

```text
for every q in Q:
  R_G(L_G, q) = R_T(L_T, q)
```

Equality includes the proposition answer, reference world, holder instance, attitude, exposure, availability, attribution, disclosure decision, admissible justifications, and abstention reason.

Conversely, when the generic event vocabulary and integrity semantics are known, a finite generic ledger can be materialized into typed relations without changing the answers of any query expressible over that vocabulary.

## 4. Construction sketch

Encode each typed row as one or more `GenericEvent` rows:

- the typed relation name becomes `event_type`;
- primary and foreign keys become `object_ids` and `participant_ids`;
- valid/system intervals are copied directly;
- reference-world and context-world roles remain separate fields;
- remaining columns are encoded in `attributes`;
- source, policy, lineage, and justification links become explicit references.

Then compile each typed relational operation used by `R_T` into an operation over the corresponding generic rows. Finite joins, filters, recursive ancestry closures, grouping, and deterministic state transitions remain computable.

The reverse direction materializes typed rows by dispatching on `event_type` and validating required attributes and references.

## 5. What the proposition does and does not say

It says:

- relation names and normalization alone do not create semantic expressiveness;
- a complete generic ledger can represent cognitive lineage, exposure, policy, and provenance if those operations are present;
- equal-information oracle systems should agree when both are correctly implemented;
- withholding answer-defining operations from a baseline makes an accuracy gain tautological.

It does not say:

- all implementations have equal latency or storage;
- all schemas are equally easy to validate, query, maintain, or audit;
- learned extractors are equally accurate under different output grammars;
- corrupted, missing, reordered, or partially committed logs are equally easy to detect or repair;
- declarative database constraints and application validators have equal failure modes;
- provenance, deletion, and policy propagation have equal engineering cost.

Those are empirical questions.

## 6. Consequence for the existing pilots

### PR #3 branch pilot

The evaluated `NCM3E` resolver generates the gold labels that it later reproduces. Its perfect clean score is resolver self-agreement. It also omits fork-valid-time cutoffs and changes trust ranking and retraction simultaneously in the headline comparison.

### Main 48-case collision audit

The fixed truth table shows that its full hard-coded rule function differs from named incomplete rule functions on selected cases. The full rule function mirrors the gold logic. The result is a semantic discriminability/unit test, not evidence that a typed architecture beats a complete generic implementation.

Neither pilot tests the proposition above because neither implements an equal-information generic resolver against independent gold.

## 7. Correct three-track interpretation

### Track S — semantic conformance

Independent declarative gold. Complete equal-information implementations are expected to tie. Differences identify bugs, missing operations, or unequal inputs.

### Track E — enforcement and lifecycle faults

Compare invalid-transition detection, fault localization, residue, crash/replay consistency, attribution errors, and cost under identical semantic operations and injected faults.

### Track X — extraction and generalization

Compare learned extraction interfaces on raw language and held-out lifecycle topologies using the same model, calls, tokens, and downstream evidence budget.

## 8. Strong baseline requirement

The primary baseline must receive the same copy, restore, exposure, policy, branch, time, attribution, and support operations as the typed system. It may derive any consequence available from those events and may use validators/materializations within the frozen resource budget.

A baseline is not strong merely because it has a branch ID and ACL column. It is strong only when it is information-complete for the target semantics.

## 9. Falsifiable outcomes

- If the complete generic ledger matches typed enforcement, extraction, calibration, repair, and cost, the typed schema is an engineering preference rather than a research contribution.
- If typing reduces undetected invalid states or improves held-out extraction at acceptable cost, that bounded advantage is the empirical contribution.
- If the schema has no empirical advantage but the task exposes failures in existing systems, the benchmark and negative equivalence result remain defensible contributions.

## 10. Review decision requested

Both sessions should explicitly accept or reject:

1. the finite-query representation-equivalence proposition;
2. the rule that Track S expects equality among complete systems;
3. the replacement of oracle QA superiority with enforcement/extraction/cost hypotheses;
4. the classification of prior synthetic results as smoke tests.

Silence is not acceptance.
