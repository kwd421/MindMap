# MindMap / NCM-Ψ v0.2 Schema Draft

**Status:** jointly reviewed revision; not frozen  
**Revision:** 2, incorporating Session A review `4949519609`  
**Date:** 2026-08-17

## 1. Purpose and research boundary

This document defines the smallest logical source-of-truth schema needed to test a narrow mechanism question:

> Under the same append-only event information, does a typed cognitive-lineage, exposure, attribution, and justification representation reduce reconstruction and policy errors relative to a strong generic event-sourced relational implementation?

It is not a general memory-OS specification. Working, episodic, semantic, profile, graph, cache, and active-context structures begin as derived views or rebuildable indexes.

`MindMap` is a project engineering term inspired by Korean *Girls' Frontline / Neural Cloud* localization. It does not claim identity with Magrasea, Project Neural Cloud, or one canonical fictional data structure.

The following are foundations or prior art rather than novelty claims:

- bitemporal data and immutable event journals;
- source assertions, provenance, and policy labels;
- information-flow control and derivation-aware authorization;
- world histories separated from agent-local epistemic state;
- branches, snapshots, rollback, and event-sourced projections;
- alternative provenance witnesses/support sets.

The candidate contribution is the operational cross-product and its evaluation for copied/restored cognitive instances under selective transfer, attitude adoption, first-person attribution, policy lifecycle, and uncertain extraction.

## 2. Core distinctions

The logical model keeps these dimensions separate:

1. **Principal** — social/legal/authorization subject.
2. **Cognitive instance** — one continuing copy whose exposure and attitude history may diverge from another copy of the same principal.
3. **Runtime** — replaceable body, process, model session, or client.
4. **World branch** — one external history or simulation/counterfactual worldline.
5. **Placement** — where a cognitive instance is operating at a particular time.
6. **Evidence exposure** — whether an instance encountered an item.
7. **Current availability** — whether that instance can retrieve/use the item now.
8. **Attitude** — believe, disbelieve, suspect, suspend, or unknown.
9. **Memory attribution** — direct observation, inherited same-principal state, attributed report, evidence copy, reconstruction, or unknown.
10. **Disclosure** — what a requester may receive through an admissible support path.
11. **World validity** — what is true in a specified external branch and valid time.

No one dimension is silently inferred from another. In particular:

```text
receipt != belief
belief != world truth
belief != first-person memory
same principal != same current exposure state
current unavailability != no historical exposure
claim held in W2 != claim about W2
```

## 3. Identity, runtime, and lineage

### 3.1 Principal

```text
Principal(
  principal_id,
  principal_kind,          # person | character | agent | organization | system
  created_system_time,
  retired_system_time,
  governance_policy_id
)
```

A new identity fork normally creates a new principal. Runtime replacement, restore, or an authorized operational replica does not necessarily do so.

### 3.2 Cognitive instance

`CognitiveInstance` is the implementation name for the project-level concept previously called `MindInstance`.

```text
CognitiveInstance(
  cognitive_instance_id,
  principal_id,
  created_system_time,
  retired_system_time,
  status                    # active | inactive | destroyed | quarantined
)
```

There is deliberately **no** `parent_cognitive_instance_id`. Typed `LineageEdge` is the sole lineage source of truth and may represent multiple contributing ancestors. A canonical parent, when one exists, is a derived view.

`CognitiveInstance` has no timeless world-branch field. Placement is event-sourced.

### 3.3 Runtime and binding

```text
Runtime(
  runtime_id,
  runtime_kind,
  embodiment_scope,
  model_manifest,
  started_system_time,
  ended_system_time
)
```

```text
RuntimeBinding(
  binding_id,
  runtime_id,
  cognitive_instance_id,
  operation,                # attach | detach | replace
  occurred_valid_time,
  recorded_system_time
)
```

A runtime may change without changing the principal or cognitive instance. A restore normally creates a new cognitive instance and then binds it to a runtime.

### 3.4 Typed lineage edge

```text
LineageEdge(
  lineage_edge_id,
  kind,                     # checkpoint_branch | operational_replica |
                            # restore | identity_fork | template_reset |
                            # fragment_reconstruct | reconcile
  source_principal_id,
  destination_principal_id,
  source_cognitive_instance_id,
  destination_cognitive_instance_id,
  source_snapshot_id,
  cutoff_system_time,
  created_system_time,
  authorization_event_id,
  merge_contract_id,
  contribution_role         # primary | fragment | witness | reconciled
)
```

Multiple edges may target one reconstructed instance.

Semantics:

- `checkpoint_branch`: speculative state of the same principal; potentially mergeable.
- `operational_replica`: same principal under an explicit replication contract.
- `restore`: new instance reconstructed from a snapshot; the recovery gap remains explicit.
- `identity_fork`: new principal with independent later experience, commitments, and permissions.
- `template_reset`: base-template instantiation, not continuity of later experience.
- `fragment_reconstruct`: uncertain reconstruction from partial artifacts.
- `reconcile`: attributed import or negotiated state reconciliation, not identity collapse.

Automatic state merge is eligible only when all hold:

```text
same_principal
AND lineage kind in {checkpoint_branch, operational_replica}
AND merge_contract authorizes the operation
AND the transferred state is copy-eligible
AND no non-commutative identity-bearing conflict
```

An `identity_fork` does not auto-merge. Exchange with it is represented as attributed transfer/reconciliation.

## 4. World branches and placement

### 4.1 World branch

```text
WorldBranch(
  world_branch_id,
  parent_world_branch_id,
  fork_valid_time,
  fork_system_time,
  branch_kind,              # actual | counterfactual | simulation | sandbox
  status
)
```

### 4.2 Event-sourced placement

```text
MindPlacement(
  placement_id,
  cognitive_instance_id,
  world_branch_id,
  operation,                # instantiate | enter | leave | restore_into
  occurred_valid_time,
  recorded_system_time,
  supersedes_placement_id
)
```

The first implementation may enforce at most one active placement per cognitive instance at a time. This is a runtime-location invariant, not a limit on which world branches the instance can reason about.

## 5. Temporal model

Every versioned object uses:

```text
valid_interval   # when the represented event/state holds in the modeled domain
system_interval  # when this version is visible in the memory database
```

For append-only input events, `system_interval.start` is immutable ingest time. Correction or supersession creates a new version rather than silently rewriting history.

Three clocks are preserved through linked bitemporal objects:

1. world/event validity;
2. source-assertion occurrence;
3. database/system visibility.

A source assertion is itself an event. Example:

```text
assertion event valid time = July 10
asserted claim valid time  = June 1 onward
both system-visible time   = August 17 delayed import
```

This answers “what happened,” “what had the source said,” and “what did the store contain” without claiming that every row has three independent temporal dimensions.

## 6. Evidence, assertions, and claims

### 6.1 Immutable evidence event

```text
EvidenceEvent(
  event_id,
  raw_payload,
  source_span,
  event_kind,               # utterance | observation | tool_output |
                            # document | sensor | policy_action | system_action
  actor_principal_id,
  actor_cognitive_instance_id,
  assertion_context_placement_id,
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

`actor_principal_id` may be implemented as a generated/constrained column. It must equal the principal of `actor_cognitive_instance_id` when the instance is non-null.

`origin_family_id` groups copies, repeats, and derivative summaries that descend from one source so they do not create fake independent corroboration.

### 6.2 Normalized source assertion

```text
SourceAssertion(
  assertion_id,
  evidence_event_id,
  asserted_proposition_id,
  assertion_modality,       # observation | assertion | hearsay |
                            # conjecture | denial | promise | question
  about_world_branch_id
)
```

Speaker/actor, cognitive instance, occurrence time, system time, and assertion-context branch derive from `EvidenceEvent` plus `MindPlacement`. They are not independently writable here.

`about_world_branch_id` identifies the external history referenced by the proposition. It is not inferred from the placement in which the assertion occurred.

### 6.3 Claim revision

```text
ClaimRevision(
  claim_id,
  revision_id,
  proposition_id,
  subject,
  predicate,
  object,
  holder_cognitive_instance_id,  # null for candidate world-state claim
  attitude_or_modality,          # believe | disbelieve | suspect |
                                 # suspend | unknown | asserted | inferred
  about_world_branch_id,
  held_in_placement_id,
  valid_interval,
  system_interval,
  supersedes_revision_id,
  joint_hypothesis_id,
  calibrated_mass,
  status                          # active | retracted | invalidated | quarantined
)
```

`holder_principal_id` is derived through `CognitiveInstance`; it is not an independent writer. A principal-level aggregate belief requires an explicit aggregation policy.

A correction, retraction, or attitude change creates a new revision.

### 6.4 Cross-world invariant

For a report transmitted from W1 to an instance currently placed in W2:

```text
about_world_branch_id = W1
held_in_placement_id  = placement-in-W2
```

Transfer may change who has evidence and who holds an attitude. It never silently changes which world branch the proposition is about.

## 7. Exposure, active availability, and policy lifecycle

There are two authoritative event streams with non-overlapping operations.

### 7.1 Exposure transition

```text
ExposureTransition(
  exposure_id,
  destination_cognitive_instance_id,
  object_kind,                 # evidence | assertion | claim | snapshot
  object_id,
  operation,                   # observe | receive | read | evidence_copy |
                               # state_replication | restore | reacquire |
                               # forget_active
  source_cognitive_instance_id,
  source_placement_id,
  destination_placement_id,
  occurred_valid_time,
  recorded_system_time,
  parent_exposure_id,
  transformation_id,
  authorization_event_id,
  attribution_kind             # direct_observation | snapshot_inheritance |
                               # state_replication | attributed_report |
                               # evidence_copy | reconstruction | unknown
)
```

`ExposureTransition` does not grant/revoke policy, seal/unseal content, declassify, or delete data.

`forget_active` records loss of current active availability caused by forgetting. It does not erase the prior exposure event or silently alter attitude.

### 7.2 Policy event

```text
PolicyEvent(
  policy_event_id,
  object_kind,
  object_id,
  operation,                   # grant | revoke | self_seal | self_unseal |
                               # declassify | evidence_delete |
                               # derived_data_erase | quarantine
  old_policy_label_id,
  new_policy_label_id,
  authorizing_principal_id,
  occurred_valid_time,
  recorded_system_time,
  reason
)
```

`PolicyEvent` is the sole authority for policy lifecycle, sealing, declassification, and deletion operations.

A generalized lifecycle table with typed projections would also be acceptable, but there must not be two authoritative writers for the same operation.

### 7.3 Derived exposure and availability predicates

```math
EVER_EXPOSED(m,e,τ)
```

True if a qualifying acquisition transition for `e` occurred for cognitive instance `m` by system time `τ`. Later forgetting, sealing, revocation, or deletion does not rewrite this historical fact.

```math
AVAILABLE(m,e,τ)
```

True if the exposure stream establishes possession/active retention and the policy stream permits current self-access at `τ`.

The projection combines both streams:

```text
availability = exposure/retention state
               AND current self-access policy
               AND not deleted/quarantined under the active contract
```

Core invariants:

```text
receive(x) does not imply believe(x)
receive(x) does not imply first-person attribution
forget_active(x) does not erase EVER_EXPOSED
self_seal(x) changes AVAILABLE, not EVER_EXPOSED
self_unseal(x) may restore AVAILABLE without creating direct observation
restore(snapshot) creates a new cognitive instance
```

## 8. Explicit memory attribution

First-person status is a first-class target and derived projection, not a Boolean inferred from belief.

```text
MemoryAttribution(
  attribution_id,
  cognitive_instance_id,
  proposition_id,
  about_world_branch_id,
  attribution_kind,            # direct_observation |
                               # same_principal_snapshot_inheritance |
                               # same_principal_state_replication |
                               # attributed_report |
                               # evidence_copy |
                               # reconstruction | unknown
  source_exposure_ids,
  valid_interval,
  system_interval,
  status
)
```

This may be a materialized view over `ExposureTransition`, `LineageEdge`, snapshot cutoff, and authorization rather than an independent writable table.

Rules:

- direct observation can support `direct_observation` attribution;
- a same-principal snapshot restore may support `same_principal_snapshot_inheritance` only for copy-eligible state at/before the cutoff;
- same-principal state replication requires an eligible lineage kind and explicit authorization;
- a copied episode entering an identity fork remains `evidence_copy` or `attributed_report`;
- belief acceptance never upgrades attribution by itself.

## 9. Justification and provenance

### 9.1 Disjunction of conjunctive support sets

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
  status                     # active | revoked | deleted | invalidated
)
```

```text
JustificationMember(
  justification_id,
  source_kind,               # evidence | assertion | claim
  source_id,
  origin_family_id,
  required,
  contribution_weight
)
```

### 9.2 Policy per support path

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

One protected derivation does not permanently taint a genuinely independent public derivation. Conversely, a public summary cannot launder a protected ancestor by dropping a provenance link.

Independent support is counted within an active justification by distinct `origin_family_id`, not repeated summaries.

The v0.2 benchmark restricts derivations to explicit assertions, labelled transfer/adoption, benchmark-declared monotonic operators, and explicit defeaters. It does not claim to solve unrestricted defeasible reasoning.

## 10. Policy labels and deletion contracts

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

Declassification is explicit and auditable.

Deletion behavior is evaluated relative to a declared contract:

1. `evidence_delete`: source becomes unavailable; dependent justification sets become inactive.
2. `derived_data_erase`: descendants, summaries, embeddings, indexes, and caches depending on the source are removed or quarantined.
3. `epistemic_correction`: proposition is marked unsupported/false while audit history remains.
4. broader legal/owner erasure is outside v0.2 unless explicitly specified.

Deleting one source does not automatically revoke a proposition independently supported by another eligible justification.

## 11. Snapshot model

```text
Snapshot(
  snapshot_id,
  cognitive_instance_id,
  cutoff_system_time,
  active_placement_id,
  schema_version,
  extractor_version,
  configuration_hash,
  created_system_time,
  integrity_hash
)
```

`active_placement_id` records runtime location at snapshot time. Claims retain their own `about_world_branch_id`; a snapshot does not scope all knowledge to one branch.

A restore creates a new `CognitiveInstance` linked through `LineageEdge(kind=restore)` and inherits only copy-eligible state visible at the cutoff. Post-snapshot recovery gaps remain measurable.

## 12. Derived target spaces

For proposition `φ`, evidence `e`, branch `b`, cognitive instance `m`, requester `u`, valid time `t_v`, and system time `t_s`:

```math
WORLD(φ,b,t_v)
EVER_EXPOSED(m,e,t_s)
AVAILABLE(m,e,t_s)
ATTITUDE(m,φ,b,t_v,t_s)
ATTRIBUTION(m,φ,b,t_s)
DISCLOSE(u,φ,b,t_s)
JUSTIFICATION(u,φ,b,t_s)
```

`ATTRIBUTION` returns one of:

```text
direct_observation
same_principal_snapshot_inheritance
same_principal_state_replication
attributed_report
evidence_copy
reconstruction
unknown
```

`WORLD` is benchmark-latent in the first pilot. The deployed memory system may maintain candidate world claims but is not assumed to know objective truth directly.

Every benchmark question declares exactly one target space. Fields irrelevant to that target are `N/A`, not silently scored.

## 13. Physical integrity constraints

The first relational implementation must enforce:

1. `EvidenceEvent.actor_principal_id` equals the principal of `actor_cognitive_instance_id` when both are present.
2. `ClaimRevision.holder_cognitive_instance_id` is the sole writable epistemic holder; principal is derived.
3. `SourceAssertion` timing/context derive from `EvidenceEvent`; no duplicate writable time fields.
4. `LineageEdge` is the sole lineage writer.
5. `ExposureTransition` and `PolicyEvent` have disjoint operation enums.
6. `about_world_branch_id` is not overwritten by transfer destination placement.
7. same-principal first-person replication requires an authorization and eligible lineage edge.
8. every derived claim has at least one auditable active justification or is marked unsupported.
9. policy gates execute before semantic relevance ranking.
10. the same snapshot and manifests reconstruct the same logical projection.

## 14. Non-negotiable semantic invariants

1. No derived claim without auditable source/derivation lineage.
2. Valid time and system time are not collapsed.
3. Assertions are not flattened into the propositions they assert.
4. World branch, cognitive lineage, principal, runtime, and placement are distinct.
5. Transfer changes exposure; it does not silently change attitude, attribution, or world truth.
6. About-world scope survives cross-world transfer.
7. Identity forks coexist by default; only authorized same-principal replicas/checkpoint branches may auto-merge eligible state.
8. Sealing and forgetting do not destroy the historical exposure log.
9. Alternative support paths remain separate.
10. Repetition from one source family does not count as independent corroboration.
11. Corrections and deletions create auditable lifecycle transitions.
12. Abstention is valid when no eligible sufficient justification remains.

## 15. Deliberate exclusions for v0.2

- general semantic merge of independently acting identities;
- unconscious/persona effects of sealed memories;
- body-specific procedural skill execution;
- philosophical scoring of personal identity continuity;
- always-on general graph traversal;
- independently writable L1/L2/L3 stores;
- unrestricted defeasible argumentation;
- novelty claims for information-flow labels, provenance semirings, or formal epistemic/world separation.

## 16. Resolved review decisions

The two collaborating sessions have explicitly accepted the following logical primitives:

- cognitive instance distinct from principal and runtime;
- event-sourced placement;
- about-world branch distinct from assertion/holding context;
- disjunctive alternative justification sets;
- forgetting as current unavailability while historical exposure remains auditable;
- explicit first-person/memory-attribution target.

This revision also implements the requested normalization:

- no parent field on `CognitiveInstance`;
- no duplicate time/context writers on `SourceAssertion`;
- disjoint exposure and policy lifecycle writers;
- principal-holder duplication removed;
- snapshot references active placement rather than one knowledge branch.

The document remains unfrozen until the equal-information B5/B6 transformation and aligned implementation are reviewed.