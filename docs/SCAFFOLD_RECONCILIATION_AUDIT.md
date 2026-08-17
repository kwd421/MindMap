# Scaffold Reconciliation Audit

**Status:** independent static review  
**Date:** 2026-08-17  
**Reviewed branch:** `research/v0.2-reconciled` before canonical implementation refactor

## 1. Decision

The committed `src/mindmap` package and semantic tests are useful **pre-pivot reference-scaffold artifacts**, but they are not an implementation of the canonical `SCHEMA_V0_2.md` or `PREREG_V0_2.md`.

Permitted current label:

> exploratory resolver/scenario scaffold demonstrating selected old-model distinctions.

Not permitted:

- complete generic-versus-typed semantic comparison;
- proof of canonical schema sufficiency;
- S-track conformance completion;
- E-track lifecycle enforcement evidence;
- X-track held-out extraction/generalization evidence.

## 2. Canonical-schema mismatches

### 2.1 Lineage has two writers and only one parent

Current code:

```text
MindInstance.parent_mind_instance_id
MindInstance.inherited_through_tx
MindInstance.world_branch_id
```

Canonical decisions:

- `LineageEdge` is the sole lineage source;
- multiple contributing ancestors must be representable;
- world placement is event-sourced and not a timeless mind-instance field.

The current `mind_cutoff()` walks a single parent chain. It cannot represent fragment reconstruction, reconciliation, or multi-source ancestry and can silently choose no semantics for those cases.

### 2.2 World placement and proposition reference remain partially collapsed

The current model carries:

```text
EvidenceEvent.world_branch_id
ClaimRevision.world_branch_id
ClaimRevision.about_world_branch_id
ClaimRevision.asserted_in_world_branch_id
ExposureTransition.world_branch_id
MindInstance.world_branch_id
```

This duplicates context writers and lacks a canonical `MindPlacement` relation. The cross-world fixture demonstrates the intended distinction, but the physical model does not enforce one authoritative placement/context source.

### 2.3 Exposure and policy lifecycle overlap

Current code defines:

```text
GRANT_OPS = {observe, receive, read, copy, restore, unseal}
REVOKE_OPS = {seal, forget, revoke}
ExposureTransition.policy_label
```

Canonical decisions require:

- exposure operations such as observe/receive/read/copy/restore/reacquire/forget-active;
- policy operations such as grant/revoke/seal/unseal/declassify/delete/erase;
- no two authoritative writers for one lifecycle operation.

`unseal`, `seal`, and `revoke` are policy operations in the canonical design, not exposure grants/revocations. `REVOKE_OPS` is defined but not used by the resolver.

### 2.4 No explicit policy-event stream

The current resolver derives disclosure from static evidence/claim/exposure labels and a strictest-ancestor calculation. It cannot reconstruct a dated policy lifecycle with separate requester, self-access, declassification, deletion, or descendant invalidation events.

### 2.5 No explicit memory-attribution target

The canonical target:

```text
ATTRIBUTION ∈ {
  direct_observation,
  same_principal_snapshot_inheritance,
  same_principal_state_replication,
  attributed_report,
  evidence_copy,
  reconstruction,
  unknown
}
```

is not present in `Query` or `NCMResolver`. The existing `lineage` query is an access/inheritance Boolean and cannot distinguish receipt, belief acceptance, and first-person attribution.

### 2.6 Alternative sufficient justifications are not represented

`strictest_policy()` joins every ancestor policy. `origin_families()` flattens all ancestors into one set.

The canonical model requires:

```text
OR over alternative sufficient JustificationSets
AND within each set
```

Otherwise one protected path permanently over-taints an independently public path, or an implementation relaxing the join risks laundering the protected path.

### 2.7 Runtime, binding, snapshot manifest, and authorization are incomplete

The scaffold has no canonical:

```text
Principal
Runtime / RuntimeBinding
LineageEdge authorization
merge contract
MindPlacement
PolicyEvent
JustificationSet
Snapshot manifest with active placement
```

`operational_replica + state_replication` authorization and identity-fork attribution cannot be enforced by the current model.

## 3. S-track mismatch

The canonical S track expects complete equal-information generic and typed implementations to agree.

The current tests instead intentionally compare:

```text
BranchScopedCharacterResolver
versus
NCMResolver
```

where the former collapses copied instances and checks only final-row policy. It is an intentionally incomplete diagnostic baseline, not complete generic G.

Examples:

- `test_mind_fork_isolation_requires_instance_lineage` expects the scoped baseline to leak and NCM to succeed;
- `test_private_policy_propagates_through_derivation` expects the scoped baseline to disclose and NCM to block.

These are useful ablation tests. They do not test semantic equivalence under equal information.

Required S-track architecture:

```text
independent declarative gold
CommonEventLog
G = complete generic bitemporal event program
T = complete typed v0.2 ledger
```

Both G and T must receive identical operations, identifiers, cutoffs, policies, support members, and authorizations. Any clean disagreement is a bug or underspecified semantics.

## 4. Gold independence

Scenario fixtures store `Query.expected` values manually, which is more independent than the fixed 48-case script's shared `gold()` helpers. However:

- many expectations are encoded in the same imperative builder that constructs implementation-facing records;
- no declarative transition specification is separately executed;
- mutation tests do not yet prove oracle/system separation;
- the test suite mainly checks NCM against hand-entered expected values rather than G and T against an independently generated state trace.

Required correction:

1. define a declarative event fixture format;
2. implement gold transitions in a module that imports no resolver code;
3. transform the same fixture into G and T;
4. score each target with an independent evaluator;
5. add mutation tests for every invariant.

## 5. E-track status

No matched lifecycle fault harness exists yet.

Missing fault families include:

- missing/duplicated/reordered events;
- crash between journal append and projection update;
- duplicate or out-of-order replay;
- stale availability/attribution/cache/index projections;
- stale descendants after revoke/delete;
- corrupted lineage/placement/support links;
- snapshot manifest mismatch;
- missing/revoked authorization;
- concurrent transfer and policy races;
- repair and residue measurement.

The existing corruption module is oriented toward extraction/noise interventions and does not by itself measure write-time prevention, silent violation, localization, repair blast radius, or replay cost.

## 6. X-track status

The current scenario generator uses direct structured records. It does not establish:

- held-out topology families;
- raw dialogue/document rendering with hidden structured state;
- calibrated joint extraction hypotheses;
- representation-specific validation under equal model/call/token budgets;
- target routing, abstention, or downstream safety on unseen topologies.

The extraction-noise script should remain an exploratory simulator until its raw-language inputs, extractor, correlation model, and held-out topology discipline are frozen.

## 7. Additional static findings

### 7.1 Policy enum fragility

`POLICY_RANK[x]` assumes every inherited label is in a fixed three-value dictionary. Unknown or versioned policy labels cause a hard failure rather than explicit quarantine/abstention.

### 7.2 Missing referential validation

`MemoryIndex` builds dictionaries but does not validate:

- duplicate IDs;
- missing parents;
- missing source events/claims;
- branch/mind cycles at construction time;
- actor/holder principal consistency;
- transfer authorization;
- system-time monotonicity;
- unsupported operation values.

Some errors are silently skipped in provenance traversal.

### 7.3 Ambiguous supersession

Latest claim selection is primarily `(recorded_at, revision_id)`. `supersedes_revision_id` is stored but not used to validate a revision chain or invalidate competing branches.

### 7.4 Policy flattening

`strictest_policy()` is conservative for one derivation path but cannot choose an admissible independent path. The current private-derivation fixture tests taint propagation only, not path-sensitive support.

### 7.5 Query overloading

`lineage` currently aliases access. A canonical evaluator needs separate lineage, ever-exposed, available, attitude, attribution, disclosure, and justification contracts.

## 8. CI status

A GitHub Actions workflow was added to run `pytest`, but GitHub did not allocate a runner because the account's Actions billing/spending limit prevented job start. The failure is infrastructure-level, not a test result.

Until a runner or local materialization is available:

- test pass/fail remains unverified in this review;
- no green-CI claim is permitted;
- static findings remain actionable independently of execution.

## 9. Reconciliation plan

### Phase R1 — quarantine and classify

- retain current package as `legacy_oracle_scaffold` or clearly mark every module/result as pre-pivot exploratory;
- remove comparative architecture claims from its docs/results;
- retain selected scenarios as candidate semantic fixtures.

### Phase R2 — canonical event and gold core

Implement:

```text
CommonEvent
DeclarativeGoldState
Target-conditioned evaluator
```

with no resolver imports in the gold module.

### Phase R3 — complete G and T

- G: complete generic bitemporal event relation/program;
- T: canonical typed schema;
- identical information and resolver capacity;
- clean S fixtures expected to tie.

### Phase R4 — lifecycle fault harness

Add matched semantic fault specifications, implementation mappings, invariant checks, detection/localization/repair metrics, and replay/cost measurement.

### Phase R5 — held-out raw-language track

Freeze topology-family splits and compare frozen-extractor and equal-budget end-to-end conditions.

## 10. Merge recommendation

Do not merge the current package as a canonical v0.2 implementation.

Acceptable merge paths:

1. merge canonical documents and audits only, while leaving implementation behind a clearly named legacy/experimental boundary; or
2. refactor the package to R2/R3 before merging code.

The existing tests and scenarios are worth preserving, but their scientific role must match the reconciled S/E/X claim.