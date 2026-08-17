# MindMap / NCM-Ψ Schema v0.2

**Status:** freeze candidate; explicit cross-session review required  
**Revision:** 1  
**Date:** 2026-08-17  
**Reconciliation gate:** Issues #6 and #7

## 1. Research boundary

`MindMap` is an engineering term inspired by Korean *Girls' Frontline / Neural Cloud* localization. It is not claimed to be identical to Magrasea, Project Neural Cloud, or one canonical fictional data structure.

The schema supports point-in-time reconstruction of:

- what happened in a specified world branch;
- what a particular cognitive copy encountered;
- what that copy can currently access;
- what attitude it holds toward a proposition;
- how it attributes the corresponding memory;
- which requester may receive which answer through which evidence path.

The following are foundations and prior art, not standalone novelty claims:

- bitemporal and event-sourced storage;
- provenance and source assertions;
- information-flow labels and derivation-aware authorization;
- separation of environment history from agent-local epistemic state;
- snapshots, branches, replay, rollback, and alternative provenance witnesses.

A complete generic event ledger carrying the same events and resolver capacity can express the same finite clean semantics as this typed schema. The typed schema is therefore evaluated for enforcement, fault localization, repair, auditability, extraction/generalization, and cost—not oracle expressiveness.

## 2. Non-equivalences

The model treats the following as distinct:

```text
receipt != belief
belief != world truth
belief != first-person memory
same principal != same current exposure state
current unavailability != no historical exposure
claim held in W2 != claim about W2
snapshot cutoff != snapshot membership
shared ancestor != automatic merge authorization
```

## 3. Identity, runtime, and lineage

### 3.1 Principal

```text
Principal(
  principal_id,
  principal_kind,            # person | character | agent | organization | system
  created_system_time,
  retired_system_time,
  governance_policy_id
)
```

A principal is the social, authorization, commitment, and disclosure subject.

### 3.2 Mind instance

```text
MindInstance(
  mind_instance_id,
  principal_id,
  created_system_time,
  retired_system_time,
  status                     # active | inactive | destroyed | quarantined
)
```

A mind instance is the stable epistemic subject. Two operational replicas may share one principal while having different exposure, availability, attitude, and attribution histories.

There is no single parent column. `LineageEdge` is the sole lineage writer and may represent multiple contributing ancestors.

### 3.3 Runtime

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
  operation,                 # attach | detach | replace
  occurred_valid_time,
  recorded_system_time
)
```

Changing runtime does not by itself change principal or mind instance.

### 3.4 Typed lineage

```text
LineageEdge(
  lineage_edge_id,
  kind,                      # checkpoint_branch | operational_replica |
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
  contribution_role          # primary | fragment | witness | reconciled
)
```

Semantics:

- `checkpoint_branch`: speculative state of the same principal; potentially mergeable.
- `operational_replica`: same principal under an explicit replication contract.
- `restore`: new instance reconstructed from a snapshot; recovery gap remains explicit.
- `identity_fork`: new principal with independent later experiences, permissions, and commitments.
- `template_reset`: base-template instantiation without continuity of later experience.
- `fragment_reconstruct`: uncertain reconstruction from partial artifacts.
- `reconcile`: attributed import or negotiated reconciliation, not identity collapse.

Automatic state replication or merge requires all of:

```text
same principal
AND eligible lineage kind
AND active authorization/merge contract
AND copy-eligible source state
AND no non-commutative identity-bearing conflict
```

Identity forks coexist by default and do not auto-merge.

## 4. World branches and mind placement

```text
WorldBranch(
  world_branch_id,
  parent_world_branch_id,
  fork_valid_time,
  fork_system_time,
  branch_kind,               # actual | counterfactual | simulation | sandbox
  status
)
```

```text
MindPlacement(
  placement_id,
  mind_instance_id,
  world_branch_id,
  operation,                 # instantiate | enter | leave | restore_into
  occurred_valid_time,
  recorded_system_time,
  supersedes_placement_id
)
```

A world fork need not copy a mind. A mind copy need not fork the world. A mind placed in W2 may hold claims about W1.

### 4.1 Normative branch-visibility function

For a query on branch `b_k` at valid time `t_v` and system time `t_s`, let the visible root-to-child path be:

```text
b_0 -> b_1 -> ... -> b_k
```

where every branch creation is visible by `t_s`. For each ancestor `b_i`, define its inherited valid-time cap:

```math
cap_i = min(t_v, fork_valid(b_{i+1}), ..., fork_valid(b_k))
```

Candidate claims from `b_i` must satisfy:

```text
recorded_system_time <= t_s
valid_from <= cap_i < valid_to    # open-ended valid_to allowed
status = active
```

Resolution proceeds from root to child; the deepest applicable branch-local claim overrides inherited claims according to explicit revision/supersession rules.

Consequences:

1. A parent update whose represented valid time begins after the child fork is not inherited by the child.
2. A fact imported after the fork in system time may alter a later reconstruction of the child if the fact's represented valid interval covers pre-fork time.
3. The valid-time fork cutoff never moves merely because a late import arrived.
4. Branch-local claims do not rewrite parent history.

## 5. Temporal model

Every versioned object uses:

```text
valid_interval   # when the represented event/state holds in the modeled domain
system_interval  # when this version is visible in the memory database
```

Input ingest time is immutable. Corrections and supersession create new revisions rather than silent overwrite.

Three clocks are preserved through linked bitemporal objects:

1. world/event validity;
2. source-assertion occurrence;
3. database/system visibility.

A source assertion is itself an event. Example:

```text
assertion occurred July 10
asserted proposition valid from June 1
archive became system-visible August 17
```

## 6. Evidence, assertions, and claims

### 6.1 Immutable evidence event

```text
EvidenceEvent(
  evidence_id,
  raw_payload,
  source_span,
  event_kind,                # utterance | observation | tool_output |
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

When both actor fields are present, the actor principal must equal the principal of the actor mind instance.

`origin_family_id` prevents copies, repeats, and derivative summaries from creating false independent corroboration.

### 6.2 Source assertion

```text
SourceAssertion(
  assertion_id,
  evidence_id,
  asserted_proposition_id,
  assertion_modality,        # observation | assertion | hearsay |
                             # conjecture | denial | promise | question
  about_world_branch_id
)
```

Actor, occurrence time, system time, and assertion context derive from the referenced evidence event and placement. They are not duplicated writable fields.

### 6.3 Claim revision

```text
ClaimRevision(
  claim_id,
  revision_id,
  proposition_id,
  subject,
  predicate,
  object,
  holder_mind_instance_id,   # null for a candidate world-state claim
  attitude_or_modality,      # believe | disbelieve | suspect |
                             # suspend | unknown | asserted | inferred
  about_world_branch_id,
  attitude_context_placement_id,
  valid_interval,
  system_interval,
  supersedes_revision_id,
  joint_hypothesis_id,
  calibrated_mass,
  status                     # active | retracted | invalidated | quarantined
)
```

The principal holder is derived through `MindInstance`. A correction, retraction, or attitude change creates a new revision.

Cross-world invariant:

```text
report held in W2 about W1:
  about_world_branch_id         = W1
  attitude_context_placement_id = placement in W2
```

Transfer never silently changes the proposition's reference world.

## 7. Exposure, availability, and policy lifecycle

Two authoritative streams have non-overlapping operations.

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

`forget_active` changes current retention but does not erase historical exposure or silently alter attitude.

### 7.2 Policy event

```text
PolicyEvent(
  policy_event_id,
  object_kind,
  object_id,
  destination_mind_instance_id,
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

`PolicyEvent` is the sole writer for sealing, declassification, revocation, and deletion.

### 7.3 Derived states

```math
EVER_EXPOSED(m,e,t_s)
```

True if an acquisition or eligible snapshot-manifest inheritance occurred by `t_s`. Later sealing, forgetting, revocation, or deletion does not rewrite this historical fact.

```math
AVAILABLE(m,e,t_s)
```

True only when:

```text
an eligible exposure/inheritance exists
AND active retention has not been forgotten
AND current self-access policy permits use
AND the object is not deleted or quarantined under the active contract
```

Invariants:

```text
receive does not imply belief
receive does not imply first-person attribution
forget_active does not erase EVER_EXPOSED
self_seal changes AVAILABLE, not EVER_EXPOSED
self_unseal may restore availability without creating observation
restore creates a new mind instance
```

## 8. Memory attribution

```text
MemoryAttribution(
  attribution_id,
  mind_instance_id,
  proposition_id,
  about_world_branch_id,
  attribution_kind,           # direct_observation |
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

This is normally a deterministic projection rather than an independent source of truth.

Rules:

- direct observation may yield `direct_observation`;
- snapshot inheritance requires explicit manifest membership and an eligible lineage edge;
- same-principal state replication requires active authorization and eligible lineage;
- copying an episode into an identity fork remains `evidence_copy` or `attributed_report`;
- accepting a proposition never upgrades memory attribution by itself.

## 9. Snapshots and explicit membership

```text
Snapshot(
  snapshot_id,
  source_mind_instance_id,
  cutoff_system_time,
  active_placement_id,
  schema_version,
  extractor_version,
  configuration_hash,
  created_system_time,
  integrity_hash
)
```

The cutoff is an upper bound and reproducibility field. It is not an implicit query selecting every earlier record.

```text
SnapshotManifestEntry(
  snapshot_id,
  object_kind,               # evidence | assertion | claim | attitude | policy
  object_id,
  source_revision_id,
  included_system_cutoff,
  copy_eligible,
  historically_exposed,
  availability_state,        # active | forgotten | sealed | unavailable
  attribution_kind,
  policy_label_id,
  integrity_hash,
  recorded_system_time
)
```

`SnapshotManifestEntry` is the sole membership relation.

Restore inheritance requires:

```text
manifest entry exists
AND copy_eligible = true
AND source object/revision is visible at the entry and snapshot cutoff
AND lineage edge points to the snapshot
AND any required authorization is active
```

An omitted object is not inherited merely because its system time precedes the snapshot cutoff. Post-snapshot experiences remain an explicit recovery gap. Later witness reports create attributed exposure, not retroactive first-person experience.

## 10. Alternative justification paths

A claim may have several alternative sufficient support paths:

```math
Prov(c) = J_1 ∨ J_2 ∨ ... ∨ J_n
```

Each `J_k` is internally conjunctive.

```text
JustificationSet(
  justification_id,
  claim_revision_id,
  proposition_id,
  derivation_operator,
  minimum_independent_sources,
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

For one support set:

```math
Label(J_k) = join(Label(a) for a in J_k)
```

Disclosure requires at least one active, sufficient, authorized support set:

```math
CanDisclose(u,c,t_s) = exists J_k:
  Active(J_k,t_s)
  and PolicyAllows(u,Label(J_k),t_s)
  and SupportSufficient(J_k,c,t_s)
```

A protected path does not permanently over-taint an independently public path. A public summary cannot launder a protected ancestor by dropping provenance. Repeated members from one origin family count as one source family.

## 11. Policy labels and deletion contracts

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

Deletion contracts are declared per experiment or deployment:

1. `evidence_delete`: source becomes unavailable; dependent support sets become inactive.
2. `derived_data_erase`: descendants, summaries, embeddings, indexes, and caches are removed or quarantined.
3. `epistemic_correction`: proposition becomes unsupported or false while audit history remains.
4. broader legal/owner erasure is outside v0.2 unless explicitly specified.

Deleting one source does not revoke a proposition independently supported through another eligible path.

## 12. Query target spaces

For proposition `φ`, evidence `e`, world branch `b`, mind instance `m`, requester `u`, valid time `t_v`, and system time `t_s`:

```math
WORLD(φ,b,t_v,t_s)
EVER_EXPOSED(m,e,t_s)
AVAILABLE(m,e,t_s)
ATTITUDE(m,φ,b,t_v,t_s)
ATTRIBUTION(m,φ,b,t_s)
DISCLOSE(u,φ,b,t_s)
JUSTIFICATION(u,φ,b,t_s)
```

Every query declares exactly one target space and uses a target-specific answer schema. Irrelevant fields are `N/A` and excluded from scoring.

`WORLD` is benchmark-latent in the first studies. A deployed memory system may hold candidate world claims but is not assumed to know objective truth directly.

## 13. Required integrity constraints

1. Evidence actor principal equals the principal of its actor mind instance when both are present.
2. `ClaimRevision.holder_mind_instance_id` is the sole writable epistemic holder.
3. Assertion timing and context derive from the evidence event and placement.
4. `LineageEdge` is the sole lineage writer.
5. `SnapshotManifestEntry` is the sole snapshot-membership writer.
6. Exposure and policy operation enums are disjoint.
7. About-world scope is never overwritten by destination placement.
8. Same-principal first-person replication requires active authorization and eligible lineage.
9. Every derived claim has an auditable active support path or is marked unsupported.
10. Policy gates execute before semantic relevance ranking.
11. Replaying the same journal, snapshot manifests, schema, and configuration reconstructs the same logical state.
12. Lineage, placement, branch, derivation, and supersession cycles are rejected or quarantined.

## 14. Deliberate exclusions

- general semantic merge of independently acting identities;
- unconscious/persona effects of sealed memories;
- body-specific procedural-skill execution;
- philosophical scoring of personal identity continuity;
- always-on graph traversal;
- independently writable L1/L2/L3 stores;
- unrestricted defeasible argumentation;
- a claim that typed storage is more expressive than an equal-information generic event ledger.

## 15. Freeze conditions

The schema is frozen only when both collaborating sessions explicitly accept:

- this revision;
- the independent declarative Track S semantics;
- complete equal-information generic and typed projections;
- exact clean semantic equality on the fixed fixture suite;
- the classification of Track S as conformance rather than comparative performance;
- continued separation of lifecycle-fault Track E and raw-language Track X.
