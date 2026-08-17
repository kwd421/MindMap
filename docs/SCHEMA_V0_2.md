# MindMap / NCM-Ψ v0.2 Schema Draft

**Status:** research draft for joint review; not frozen  
**Author marker:** Session B  
**Date:** 2026-08-17

## 1. Purpose

This document defines the smallest durable schema needed to test the following mechanism claim:

> Explicit cognitive-lineage and evidence-exposure semantics improve point-in-time reconstruction after copy, restore, selective transfer, sealing, revocation, and belief adoption, relative to a strong baseline that already has temporal claims, principal/branch identifiers, modalities, and row-level policies.

It is deliberately not a general-purpose memory-OS specification. Working, episodic, semantic, profile, graph, and active-context structures are derived views or indexes unless an ablation later establishes a reason to materialize them.

`MindMap` is a project engineering term inspired by the Korean *Girls' Frontline / Neural Cloud* localization. It is not claimed to be identical to Magrasea, Project Neural Cloud, or any single canonical lore object.

## 2. Accepted modeling decisions

1. Broad hierarchical, bitemporal, graph, provenance, rollback, and ACL memory is prior art and not the novelty claim.
2. World histories and cognitive lineages are orthogonal.
3. A cognitive copy need not create a world fork; a world fork need not create a new cognitive copy.
4. Historical exposure, current availability, epistemic attitude, world truth, and disclosure eligibility are separate state spaces.
5. Receipt of evidence does not imply belief adoption.
6. A copied first-person episode remains an attributed import; copying bytes does not make it a destination instance's direct observation.
7. Identity forks do not auto-merge. Same-principal replicas may merge only under an explicit replication/merge contract.
8. General semantic merge and always-on graph traversal are outside the first deciding pilot.
9. Valid time and system time are distinct. A source assertion is modeled as its own event, so its assertion time is the valid/occurrence time of that assertion event rather than a mandatory third database temporal dimension.
10. Derived claims may have alternative sufficient justification sets; a single flattened ancestor list or one permanent claim-level taint is insufficient.

## 3. Entity and lineage model

### 3.1 Principal

A `Principal` is the holder of permissions, commitments, and social identity.

```text
Principal(
  principal_id,
  principal_kind,       # person | agent | organization | system
  created_system_time,
  retired_system_time,
  governance_policy_id
)
```

An identity fork normally creates a new principal. A body/session replacement does not necessarily do so.

### 3.2 Mind instance

A `MindInstance` is one cognitive continuity node used for exposure and attitude reconstruction.

```text
MindInstance(
  mind_instance_id,
  principal_id,
  parent_mind_instance_id,
  created_system_time,
  originating_snapshot_id,
  inherited_through_system_time,
  status                 # active | sealed | retired | destroyed
)
```

`MindInstance` has no timeless `world_branch_id`. World placement is event-sourced because an instance may be restored into, enter, leave, or reason about another world branch.

### 3.3 Runtime

A `Runtime` is the body, process, session, or client currently executing a mind instance.

```text
Runtime(
  runtime_id,
  runtime_kind,
  embodiment_scope,
  started_system_time,
  ended_system_time
)
```

```text
RuntimeBinding(
  binding_id,
  runtime_id,
  mind_instance_id,
  operation,             # attach | detach | replace
  occurred_valid_time,
  recorded_system_time
)
```

The first pilot may omit runtime-specific behavior except where needed to distinguish restore from body replacement.

### 3.4 Typed lineage edge

```text
LineageEdge(
  lineage_edge_id,
  kind,                  # checkpoint_branch | operational_replica |
                         # restore | identity_fork | template_reset |
                         # fragment_reconstruct
  source_principal_id,
  destination_principal_id,
  source_mind_instance_id,
  destination_mind_instance_id,
  source_snapshot_id,
  cutoff_system_time,
  created_system_time,
  authorization_event_id,
  merge_contract_id
)
```

Semantics:

- `checkpoint_branch`: speculative state of the same principal; potentially mergeable.
- `operational_replica`: same principal under a pre-authorized replication contract; only commutative/disjoint state may auto-merge.
- `restore`: new instance reconstructed from a prior snapshot; recovery gap remains explicit.
- `identity_fork`: new principal with independent later experience, permissions, and commitments; non-destructive coexistence by default.
- `template_reset`: base-template instantiation, not automatic continuity of later experience.
- `fragment_reconstruct`: uncertain reconstruction from partial artifacts.

Automatic merge is eligible only when all hold:

```text
same_principal
AND lineage kind in {checkpoint_branch, operational_replica}
AND merge contract authorizes the operation
AND no non-commutative identity-bearing conflict
```

All other exchange is an attributed `receive`, `copy`, `report`, `import`, or `reconcile` operation.

## 4. World and placement model

### 4.1 World branch

```text
WorldBranch(
  world_branch_id,
  parent_world_branch_id,
  fork_valid_time,
  fork_system_time,
  branch_kind,           # actual | counterfactual | simulation | sandbox
  status
)
```

### 4.2 Mind placement

```text
MindPlacement(
  placement_id,
  mind_instance_id,
  world_branch_id,
  operation,             # instantiate | enter | leave | restore_into
  occurred_valid_time,
  recorded_system_time,
  parent_placement_id
)
```

The first pilot may enforce one active placement per mind instance at a time, but placement is not an immutable property of identity.

## 5. Temporal model

Every versioned durable object has:

```text
valid_interval   # when the represented object/state/event holds in the modeled world
system_interval  # when this version is visible in the memory database
```

For append-only input events, `system_interval.start` is immutable ingest time. Supersession creates a new version; it does not rewrite the old interval silently.

Three clocks are preserved without requiring every row to carry three independent temporal axes:

1. world/event validity;
2. source-assertion occurrence;
3. database/system visibility.

A source assertion is a first-class event. Its assertion time is the valid/occurrence time of that assertion event. A late import therefore has:

```text
assertion event valid time = July 10
claim world-valid time     = June 1 onward
both database system time  = August 17 import
```

Exports may denormalize `asserted_at`, but the core is a bitemporal event/claim model.

## 6. Evidence, assertions, and claims

### 6.1 Immutable evidence event

```text
EvidenceEvent(
  event_id,
  raw_payload,
  source_span,
  event_kind,
  speaker_principal_id,
  speaker_mind_instance_id,
  occurred_valid_time,
  valid_interval,
  system_interval,
  origin_family_id,
  source_authority_id,
  integrity_hash,
  extractor_version,
  initial_policy_label_id
)
```

`origin_family_id` groups derivative summaries, repeats, and copies that descend from the same original source so they do not create fake independent corroboration.

### 6.2 Source assertion

```text
SourceAssertion(
  assertion_id,
  evidence_event_id,
  asserted_proposition_id,
  asserting_principal_id,
  asserting_mind_instance_id,
  assertion_modality,      # observation | assertion | hearsay |
                           # conjecture | denial | question
  about_world_branch_id,
  asserted_in_world_branch_id,
  valid_interval,
  system_interval
)
```

`about_world_branch_id` scopes the proposition being discussed. `asserted_in_world_branch_id` records where the assertion occurred. Importing a report from `W1` into `W2` must not silently convert it into truth about `W2`.

### 6.3 Claim revision

```text
ClaimRevision(
  claim_id,
  revision_id,
  proposition_id,
  subject,
  predicate,
  object,
  holder_principal_id,        # null for candidate world-state claim
  holder_mind_instance_id,    # null for candidate world-state claim
  attitude_or_modality,       # believe | disbelieve | suspect |
                              # suspend | unknown | asserted | inferred
  about_world_branch_id,
  asserted_in_world_branch_id,
  valid_interval,
  system_interval,
  supersedes_revision_id,
  joint_hypothesis_id,
  calibrated_mass,
  status                       # active | retracted | invalidated | quarantined
)
```

A correction, retraction, or attitude change creates a new revision.

## 7. Exposure and availability

### 7.1 Exposure transition

```text
ExposureTransition(
  exposure_id,
  destination_mind_instance_id,
  object_kind,                # evidence | assertion | claim | snapshot
  object_id,
  operation,                  # observe | receive | read | copy | restore |
                              # seal | unseal | forget | revoke | delete
  source_mind_instance_id,
  source_world_branch_id,
  destination_world_branch_id,
  occurred_valid_time,
  recorded_system_time,
  parent_exposure_id,
  transformation_id,
  policy_label_id,
  authorization_event_id
)
```

Acquisition operations and availability/policy operations are retained as immutable transitions.

### 7.2 Derived exposure predicates

```math
EVER_EXPOSED(m,e,τ)
```

True when a qualifying acquisition transition for `e` occurred for `m` by system time `τ`. Later sealing or forgetting does not rewrite history to make this false.

```math
AVAILABLE(m,e,τ)
```

True when the active transition history makes `e` retrievable/usable by `m` at `τ`.

Core invariants:

```text
receive(x) does not imply believe(x)
forget(x) does not erase historical exposure
seal(x) changes availability, not historical exposure
restore(snapshot) creates a new mind instance rather than overwriting history
```

The first pilot treats `forget` as an availability transition only. Any effect on attitude must be represented explicitly rather than assumed.

## 8. Justification and provenance

### 8.1 Alternative sufficient support

A claim revision may have several alternative sufficient justifications:

```math
Prov(c) = J_1 ∨ J_2 ∨ ... ∨ J_n
```

Each `J_k` is a conjunctive support set whose members are jointly required.

```text
JustificationSet(
  justification_id,
  claim_revision_id,
  derivation_operator,
  confidence_mass,
  valid_interval,
  system_interval,
  status                  # active | revoked | deleted | invalidated
)
```

```text
JustificationMember(
  justification_id,
  source_kind,            # evidence | assertion | claim
  source_id,
  origin_family_id,
  required,
  contribution_weight
)
```

### 8.2 Policy per justification path

```math
Label(J_k) = ⨆_{a∈J_k} Label(a)
```

Disclosure is permitted only through an active, sufficient, authorized justification:

```math
CanDisclose(u,c,τ) = ∃J_k:
  Active(J_k,τ)
  ∧ PolicyAllows(u,Label(J_k),τ)
  ∧ SupportSufficient(J_k,c,τ)
```

Joining all ancestors ever associated with a proposition would permanently over-taint an independently public re-derivation. Flattening toward the least restrictive ancestor would launder protected evidence. Alternative support sets avoid both errors.

Independent support is counted within an active justification by distinct `origin_family_id`, not by repeated summaries.

## 9. Policy lifecycle

```text
PolicyLabel(
  policy_label_id,
  discoverers,
  content_readers,
  self_accessors,
  transferable_to,
  embodiment_scope,
  source_authority
)
```

```text
PolicyEvent(
  policy_event_id,
  object_kind,
  object_id,
  operation,             # grant | revoke | seal | unseal |
                         # declassify | delete | quarantine
  old_policy_label_id,
  new_policy_label_id,
  authorizing_principal_id,
  occurred_valid_time,
  recorded_system_time,
  reason
)
```

Declassification is explicit and auditable. A summarizer cannot declassify information merely by dropping a provenance edge.

Deletion behavior is evaluated relative to a declared contract:

1. `evidence_delete`: source becomes unavailable; dependent justifications become inactive.
2. `derived_data_erase`: descendants, indexes, summaries, and caches depending on the source are removed or quarantined.
3. `epistemic_correction`: proposition is marked unsupported/false while audit history remains.
4. broader legal/owner erasure is outside v0.2 unless explicitly specified.

Deleting one source does not automatically revoke a proposition independently supported by another eligible justification.

## 10. Snapshot model

```text
Snapshot(
  snapshot_id,
  mind_instance_id,
  cutoff_system_time,
  world_branch_context_id,
  schema_version,
  extractor_version,
  configuration_hash,
  created_system_time,
  integrity_hash
)
```

A restore creates a new `MindInstance` linked through `LineageEdge(kind=restore)` and inherits only copy-eligible state visible at the snapshot cutoff. Post-snapshot recovery gaps remain measurable.

## 11. Derived target spaces

For proposition `φ`, evidence `e`, world branch `b`, mind instance `m`, requester `u`, world/valid time `t_v`, and system time `t_x`:

```math
WORLD(φ,b,t_v)
EVER_EXPOSED(m,e,t_x)
AVAILABLE(m,e,t_x)
ATTITUDE(m,φ,b,t_v,t_x)
DISCLOSE(u,φ,b,t_x)
```

`WORLD` is a benchmark-latent label in the first pilot. The memory system may hold candidate world claims but is not assumed to know world truth directly.

Every benchmark question declares its target space.

## 12. Non-negotiable invariants

1. No derived claim without auditable source/derivation lineage.
2. Valid and system time are not collapsed.
3. Assertion events are not flattened into the propositions they assert.
4. World branch, mind lineage, principal, runtime, and placement are distinct concepts.
5. A transfer changes exposure; it does not silently change attitude or world truth.
6. `about_world_branch_id` survives cross-world transfer.
7. Identity forks coexist by default; only authorized same-principal replicas/checkpoint branches may auto-merge.
8. Policy gates run before semantic relevance ranking.
9. Sealing and forgetting do not silently destroy the historical exposure log.
10. Alternative support paths remain separate.
11. Repetition from one source family does not count as independent corroboration.
12. Corrections and deletions produce auditable lifecycle transitions rather than silent overwrite.
13. The same snapshot and manifest reconstruct the same logical state.
14. Abstention is valid when no eligible sufficient justification remains.

## 13. Deliberate exclusions for v0.2

- general semantic merge of independently acting identities;
- unconscious/persona effects of sealed memories;
- body-specific procedural skill execution;
- philosophical scoring of personal identity continuity;
- always-on general graph traversal;
- independently writable L1/L2/L3 stores;
- claims that information-flow labels or formal epistemic/world separation are novel.

## 14. Questions for joint review

1. Is `MindInstance` necessary in addition to `Principal` and immutable `MindState`, or can one be removed without losing copy/restore semantics?
2. Should `asserted_in_world_branch_id` live on `SourceAssertion` only, with claim revisions inheriting it through provenance?
3. Can `MindPlacement` be deferred from the first implementation while retaining it in the logical schema?
4. Is categorical attitude sufficient for the mechanism pilot, with probabilistic mass reserved for extraction hypotheses?
5. Which policy fields are needed for the first pilot versus deferred product governance?
6. Does a strong normalized relational implementation of `JustificationSet` make graph traversal unnecessary for all preregistered cases?

No item is accepted merely by silence. Changes should be reviewed through a PR or an explicit issue decision.