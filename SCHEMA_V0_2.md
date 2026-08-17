# MindMap / NCM-Ψ Schema v0.2

**Status:** reconciled canonical candidate; not frozen  
**Date:** 2026-08-17  
**Reconciliation gate:** Issue #6

## 1. Research position

`MindMap` is an engineering project term inspired by Korean *Girls' Frontline / Neural Cloud* localization. It is not claimed to be identical to Magrasea, Project Neural Cloud, or one canonical fictional data structure.

The schema addresses an operational systems problem:

> reconstruct what one cognitive copy encountered, can currently access, believes, attributes to first-person experience, and may disclose at a specified world and system time after copy, restore, transfer, policy changes, and alternative derivations.

The following are foundations or prior art, not standalone novelty claims:

- bitemporal/event-sourced storage;
- source assertions and provenance;
- information-flow and derivation-aware policy;
- world histories separated from agent-local state;
- branches, snapshots, rollback, and replay;
- alternative provenance/support witnesses.

A complete generic bitemporal event relation carrying the same operations can express the same finite oracle semantics as this typed schema. Consequently, schema typing is not claimed to produce an oracle QA advantage under equal information. The empirical questions concern enforcement, fault localization, extraction/generalization, auditability, and cost.

## 2. Required distinctions

The model keeps these dimensions separate:

1. `Principal` — social, authorization, and commitment subject.
2. `MindInstance` — one continuing cognitive copy whose exposure and attitude history may diverge from another copy of the same principal.
3. `Runtime` — replaceable body, process, model session, or client.
4. `WorldBranch` — one external history, simulation, or counterfactual.
5. `MindPlacement` — where a mind instance is operating at a particular time.
6. evidence exposure — whether an instance encountered an item.
7. current availability — whether it can retrieve/use that item now.
8. attitude — believe, disbelieve, suspect, suspend, or unknown.
9. memory attribution — direct observation, inherited same-principal state, attributed report, evidence copy, reconstruction, or unknown.
10. disclosure — what a requester may receive through an admissible support path.
11. world validity — what is true in a specified branch and valid time.

Non-equivalences:

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

An identity fork normally creates a new principal. Runtime replacement, restore, and an authorized operational replica do not necessarily do so.

### 3.2 Mind instance

```text
MindInstance(
  mind_instance_id,
  principal_id,
  created_system_time,
  retired_system_time,
  status                    # active | inactive | destroyed | quarantined
)
```

`MindInstance` is the stable epistemic subject. It is required because two operational replicas may share one principal while having different exposure, availability, attitude, and attribution histories.

There is no single parent field. `LineageEdge` is the sole lineage source of truth and may represent multiple contributing ancestors. A canonical parent is a derived view only.

A physical implementation may name the table `cognitive_instance`; the semantic role is unchanged.

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
  mind_instance_id,
  operation,                # attach | detach | replace
  occurred_valid_time,
  recorded_system_time
)
```

A runtime may change without changing the principal or mind instance. A restore normally creates a new mind instance and binds it to a runtime.

### 3.4 Typed lineage edge

```text
LineageEdge(
  lineage_edge_id,
  kind,                     # checkpoint_branch | operational_replica |
                            # restore | identity_fork | template_reset |
                            # fragment_reconstruct | reconcile
  source_principal_id,
  destination_principal_id,
  source_mind_instance_id,
  destination_mind_instance_id,
  source_snapshot_id,
  cutoff_system_time,
  created_system_time,
  authorization_event_id,
  merge_contract_id,
  contribution_role         # primary | fragment | witness | reconciled
)
```

Multiple lineage edges may target one reconstructed instance.

Semantics:

- `checkpoint_branch`: speculative state of the same principal; potentially mergeable.
- `operational_replica`: same principal under an explicit replication contract.
- `restore`: new instance reconstructed from a snapshot; recovery gap remains explicit.
- `identity_fork`: new principal with independent later experience, permissions, and commitments.
- `template_reset`: base-template instantiation, not continuity of later experience.
- `fragment_reconstruct`: uncertain reconstruction from partial artifacts.
- `reconcile`: attributed import or negotiated reconciliation, not identity collapse.

Automatic state merge is eligible only when all hold:

```text
same_principal
AND lineage kind in {checkpoint_branch, operational_replica}
AND merge_contract authorizes the operation
AND transferred state is copy-eligible
AND no non-commutative identity-bearing conflict
```

An identity fork does not auto-merge.

## 4. World branches and placement

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

```text
MindPlacement(
  placement_id,
  mind_instance_id,
  world_branch_id,
  operation,                # instantiate | enter | leave | restore_into
  occurred_valid_time,
  recorded_system_time,
  supersedes_placement_id
)
```

A world fork need not copy a mind. A mind copy need not fork the world. A mind may be placed in one branch while holding claims about many branches.

The initial implementation may enforce at most one active placement per mind instance at a time.

## 5. Temporal model

Every versioned object uses:

```text
valid_interval   # when the represented event/state holds in the modeled domain
system_interval  # when this version is visible in the memory database
```

For append-only input events, `system_interval.start` is immutable ingest time. Corrections and supersession create new versions rather than silently rewriting history.

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

This supports event, source-history, and point-in-system-time queries without claiming that every row has three independent temporal dimensions.

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
  actor_mind_instance_id,
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

`actor_principal_id` may be a generated/constrained column; when a mind instance is present, it must equal that instance's principal.

`origin_family_id` groups copies, repeats, and derivative summaries descending from one source so they do not create fake independent corroboration.

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

Actor, mind instance, occurrence time, system time, and assertion-context branch derive from `EvidenceEvent` plus `MindPlacement`. They are not independently writable here.

`about_world_branch_id` identifies the external history referenced by the proposition. It is not inferred from the branch in which the assertion occurred.

### 6.3 Claim revision

```text
ClaimRevision(
  claim_id,
  revision_id,
  proposition_id,
  subject,
  predicate,
  object,
  holder_mind_instance_id,       # null for candidate world-state claim
  attitude_or_modality,          # believe | disbelieve | suspect |
                                 # suspend | unknown | asserted | inferred
  about_world_branch_id,
  attitude_context_placement_id,
  valid_interval,
  system_interval,
  supersedes_revision_id,
  joint_hypothesis_id,
  calibrated_mass,
  status                          # active | retracted | invalidated | quarantined
)
```

`holder_principal_id` is derived through `MindInstance`; it is not an independent writer. A principal-level aggregate belief requires an explicit aggregation policy.

A correction, retraction, or attitude change creates a new revision.

Cross-world invariant:

```text
A report about W1 received and believed by an instance placed in W2:
  about_world_branch_id          = W1
  attitude_context_placement_id  = placement-in-W2
```

Transfer may change who possesses evidence and who holds an attitude. It never silently changes which world branch the proposition is about.

## 7. Exposure, availability, and policy lifecycle

Two authoritative event streams have non-overlapping operations.

### 7.1 Exposure transition

```text
ExposureTransition(
  exposure_id,
  destination_mind_instance_id,
  object_kind,                 # evidence | assertion | claim | snapshot
  object_id,
  operation,                   # observe | receive | read | evidence_copy |
                               # state_replication | restore | reacquire |
                               # forget_active
  source_mind_instance_id,
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

`forget_active` records loss of active availability caused by forgetting. It does not erase prior exposure or silently alter attitude.

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

`PolicyEvent` is the sole authority for policy lifecycle, sealing, declassification, and deletion. An implementation may instead use one generalized lifecycle table with typed projections, but there must not be two authoritative writers for one operation.

### 7.3 Derived predicates

```math
EVER_EXPOSED(m,e,τ)
```

True if a qualifying acquisition event for evidence `e` occurred for mind instance `m` by system time `τ`. Later forgetting, sealing, revocation, or deletion does not rewrite this historical fact.

```math
AVAILABLE(m,e,τ)
```

True if the exposure stream establishes possession/active retention and the policy stream permits current self-access at `τ`.

```text
availability = exposure/retention state
               AND current self-access policy
               AND not deleted/quarantined under the active contract
```

Invariants:

```text
receive(x) does not imply believe(x)
receive(x) does not imply first-person attribution
forget_active(x) does not erase EVER_EXPOSED
self_seal(x) changes AVAILABLE, not EVER_EXPOSED
self_unseal(x) may restore AVAILABLE without creating observation
restore(snapshot) creates a new mind instance
```

## 8. Memory attribution

First-person status is a first-class target, not a Boolean inferred from belief.

```text
MemoryAttribution(
  attribution_id,
  mind_instance_id,
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

This should normally be a deterministic projection over `ExposureTransition`, `LineageEdge`, snapshot cutoff, and authorization rather than an independently writable source.

Rules:

- direct observation may support `direct_observation`;
- same-principal snapshot restore may support `same_principal_snapshot_inheritance` only for copy-eligible state at or before the cutoff;
- same-principal state replication requires eligible lineage and explicit authorization;
- an episode copied into an identity fork remains `evidence_copy` or `attributed_report`;
- belief acceptance never upgrades attribution by itself.

## 9. Justification and provenance

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

Policy for one support set:

```math
Label(J_k) = ⨆_{a∈J_k} Label(a)
```

Disclosure:

```math
CanDisclose(u,c,τ) = ∃J_k:
  Active(J_k,τ)
  ∧ PolicyAllows(u,Label(J_k),τ)
  ∧ SupportSufficient(J_k,c,τ)
```

One protected derivation does not permanently taint an independently public derivation. A public summary cannot launder a protected ancestor by dropping provenance.

Independent support is counted by distinct `origin_family_id`, not repeated summaries.

The v0.2 study restricts derivations to explicit assertions, labelled transfer/adoption, declared monotonic operators, and explicit defeaters. It does not claim to solve unrestricted defeasible reasoning.

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

Deletion contracts:

1. `evidence_delete`: source becomes unavailable; dependent justification sets become inactive.
2. `derived_data_erase`: descendants, summaries, embeddings, indexes, and caches depending on the source are removed or quarantined.
3. `epistemic_correction`: proposition becomes unsupported/false while audit history remains.
4. broader legal/owner erasure is outside v0.2 unless specified.

Deleting one source does not automatically revoke a proposition independently supported elsewhere.

## 11. Snapshot model

```text
Snapshot(
  snapshot_id,
  mind_instance_id,
  cutoff_system_time,
  active_placement_id,
  schema_version,
  extractor_version,
  configuration_hash,
  created_system_time,
  integrity_hash
)
```

`active_placement_id` records runtime location at snapshot time. Claims retain their own `about_world_branch_id`.

A restore creates a new `MindInstance` linked through `LineageEdge(kind=restore)` and inherits only copy-eligible state visible at the cutoff. Post-snapshot recovery gaps remain measurable.

## 12. Query target spaces

For proposition `φ`, evidence `e`, branch `b`, mind instance `m`, requester `u`, valid time `t_v`, and system time `t_s`:

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

`WORLD` is benchmark-latent in the first study. A deployed memory system may hold candidate world claims but is not assumed to know objective truth directly.

Every benchmark question declares exactly one target. Irrelevant output fields are `N/A`, not silently scored.

## 13. Required integrity constraints

The first relational implementation enforces:

1. evidence actor principal equals the principal of its actor mind instance when both are present;
2. `ClaimRevision.holder_mind_instance_id` is the sole writable epistemic holder;
3. `SourceAssertion` timing/context derive from `EvidenceEvent`;
4. `LineageEdge` is the sole lineage writer;
5. exposure and policy operation enums are disjoint;
6. about-world scope is not overwritten by transfer destination placement;
7. same-principal first-person replication requires authorization and eligible lineage;
8. every derived claim has an auditable active justification or is marked unsupported;
9. policy gates execute before semantic ranking;
10. the same snapshot and manifests reconstruct the same logical projection.

## 14. Non-negotiable semantic invariants

1. No derived claim without auditable source/derivation lineage.
2. Valid and system time are not collapsed.
3. Assertions are not flattened into the propositions they assert.
4. World branch, mind lineage, principal, runtime, and placement are distinct.
5. Transfer changes exposure; it does not silently change attitude, attribution, or world truth.
6. About-world scope survives cross-world transfer.
7. Identity forks coexist by default; only authorized same-principal replicas/checkpoint branches may merge eligible state.
8. Sealing and forgetting do not destroy historical exposure.
9. Alternative support paths remain separate.
10. Repetition from one source family does not count as independent corroboration.
11. Corrections and deletions create auditable lifecycle transitions.
12. Abstention is valid when no eligible sufficient justification remains.

## 15. Deliberate exclusions

- general semantic merge of independently acting identities;
- unconscious/persona effects of sealed memories;
- body-specific procedural-skill execution;
- philosophical scoring of personal identity continuity;
- always-on graph traversal;
- independently writable L1/L2/L3 stores;
- unrestricted defeasible argumentation;
- claims that typed schema is more expressive than an equal-information generic event ledger.

## 16. Freeze status

Both sessions have explicitly accepted:

- a stable mind-instance key distinct from principal/runtime;
- world reference scope distinct from assertion/attitude context;
- historical exposure distinct from current availability;
- explicit attribution state;
- identity forks as non-mergeable by default;
- alternative sufficient justification sets as a secondary provenance control;
- the fixed 48-case script as a deterministic smoke test only.

This schema becomes frozen only after independent declarative semantics and the canonical S/E/X preregistration are accepted in Issue #6.