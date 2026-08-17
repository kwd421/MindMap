# MindMap / NCM-Ψ v0.2 — Canonical Semantics Candidate

**Status:** reconciliation candidate; freeze requires explicit acceptance from both research sessions  
**Date:** 2026-08-17  
**Scope:** point-in-time reconstruction across world forks, cognitive copies/restores, selective transfer, belief adoption, policy lifecycle, and alternative source support.

## 1. Research position and terminology

The broad combination of hierarchical memory, temporal graphs, provenance, raw fallback, consolidation, snapshots, rollback, and access control is prior art and is **not** the central novelty claim.

`MindMap` is an engineering project term inspired by Korean localization usage in the *Girls' Frontline / Neural Cloud* setting. It is not claimed to be canonically identical to Magrasea, Project Neural Cloud, a Doll's physical neural-cloud substrate, or any single fictional mechanism.

- **MindMap:** the versioned logical cognitive and epistemic state associated with one cognitive continuation.
- **Memory substrate:** the durable event, assertion, claim, lineage, exposure, policy, and provenance store from which a MindMap can be reconstructed.
- **Active projection:** a bounded, query-specific reconstruction materialized for one decision.

Fictional backup, reset, copy, sealed-memory, and body-replacement cases are adversarial scenario inspiration, not evidence that the engineering design is correct.

## 2. Representation boundary

A typed schema does not create oracle semantic expressiveness by itself. Any finite typed ledger and deterministic resolver can be compiled into a generic bitemporal event relation plus an equivalent relational program, preserving all answers on a finite query set. Conversely, a generic ledger with a known event vocabulary can be materialized into typed relations.

Accordingly:

- complete equal-information implementations are expected to agree in the semantic-conformance track;
- oracle gains obtained by withholding answer-defining operations or cutoffs from a baseline are invalid;
- empirical comparisons must concern invariant enforcement, fault localization, extraction/generalization, deletion and revocation propagation, or measured cost under equivalent information.

The formal statement and experimental consequences are recorded separately in `docs/REPRESENTATION_EQUIVALENCE.md`.

## 3. Target state spaces

For proposition `φ`, evidence object `e`, world branch `b`, mind instance `m`, requester `u`, valid-time cutoff `t_v`, and system-time cutoff `t_x`:

```text
WORLD(φ, b, t_v)
EVER_EXPOSED(m, e, t_v, t_x)
AVAILABLE(m, e, t_v, t_x)
ATTITUDE(m, φ, b, t_v, t_x)
MEMORY_ATTRIBUTION(m, e_or_φ, t_v, t_x)
DISCLOSE(u, φ, t_v, t_x)
JUSTIFY(u, φ, t_v, t_x)
```

They are deliberately distinct:

- a false rumor may be the correct answer to an attitude query;
- a true secret may be an incorrect disclosure;
- evidence receipt may establish historical exposure while current availability is false;
- accepting an imported report does not make it a first-person observation;
- deleting one private source need not erase a proposition that has a genuinely independent public justification.

Every benchmark question declares exactly one primary target and a target-conditioned output mask.

## 4. Temporal and branch semantics

### 4.1 Bitemporal records and assertion events

Every durable event or versioned object has:

```text
valid_interval   # when the represented event/state holds in the modeled domain
system_interval  # when this version is visible in the memory database
```

A source assertion is a first-class event. Its assertion time is the occurrence/valid time of its evidence event. The proposition it asserts has its own valid interval. A delayed import can therefore represent:

```text
world event valid time      = 2026-06-01
source assertion occurrence = 2026-07-10
database ingest time        = 2026-08-17
```

This preserves three clocks without claiming that every row has three independently versioned temporal dimensions.

### 4.2 World-branch visibility

```text
WorldBranch(
  world_branch_id,
  parent_world_branch_id,
  fork_valid_time,
  fork_system_time,
  branch_kind,             # actual | counterfactual | simulation | sandbox
  status
)
```

Normative inheritance rule:

1. a child world branch inherits ancestor-world events only up to the valid-time fork cutoff on each ancestry edge;
2. query system time controls whether an otherwise eligible record has been ingested and is visible;
3. a parent event whose represented valid time is after the fork does not become child-world truth;
4. a late system import after the fork about a pre-fork valid event may become visible later without changing the fork-valid-time boundary;
5. world-history inheritance, database visibility, and snapshot inheritance are separate mechanisms.

The conformance suite must include a matched pair distinguishing a post-fork parent update from a late import of a pre-fork event.

## 5. Identity, cognitive continuity, runtime, and placement

### 5.1 Principal

```text
Principal(
  principal_id,
  principal_kind,         # person | character | agent | organization | system
  created_system_time,
  retired_system_time,
  governance_policy_id
)
```

A principal holds social identity, permissions, and commitments. It is not sufficiently granular for unsynchronized replicas.

### 5.2 MindInstance

```text
MindInstance(
  mind_instance_id,
  principal_id,
  created_system_time,
  retired_system_time,
  status                  # active | sealed | retired | destroyed | quarantined
)
```

A `MindInstance` is the stable cognitive-continuation key for exposure, availability, attitude, and attribution. Two operational replicas may share one principal but have different post-copy experience.

`MindInstance` contains no canonical parent pointer. Typed `LineageEdge` records are the sole source of lineage truth, allowing multiple-source fragment reconstruction and avoiding single-parent duplication.

### 5.3 Runtime and binding

```text
Runtime(
  runtime_id,
  runtime_kind,
  embodiment_scope,
  model_manifest,
  started_system_time,
  stopped_system_time
)

RuntimeBinding(
  binding_id,
  runtime_id,
  mind_instance_id,
  operation,              # attach | detach | replace
  occurred_valid_time,
  recorded_system_time
)
```

A body, process, or model session may change without changing principal or cognitive continuity.

### 5.4 Event-sourced placement

```text
MindPlacement(
  placement_id,
  mind_instance_id,
  world_branch_id,
  operation,              # instantiate | enter | leave | restore_into
  occurred_valid_time,
  recorded_system_time,
  parent_placement_id
)
```

Placement is event-sourced rather than a timeless property of identity. The derived predicate is:

```text
PLACED_IN(m, b, t_v, t_x)
```

The first pilot may enforce at most one active placement per instance at a time.

### 5.5 Typed lineage

```text
LineageEdge(
  lineage_edge_id,
  kind,                   # checkpoint_branch | operational_replica |
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

- `checkpoint_branch`: speculative continuation of the same principal; potentially mergeable.
- `operational_replica`: same principal under an explicit replication contract; unsynchronized experience remains instance-local.
- `restore`: a new instance reconstructed from a declared snapshot manifest; the recovery gap remains explicit.
- `identity_fork`: a new principal with independent later experience, permissions, and commitments; non-destructive coexistence by default.
- `template_reset`: base-template instantiation, not automatic continuity of later experience.
- `fragment_reconstruct`: uncertain reconstruction from one or more partial artifacts.

Automatic merge is eligible only when all hold:

```text
same_principal
AND lineage_kind in {checkpoint_branch, operational_replica}
AND merge_contract authorizes the operation
AND no non-commutative identity-bearing conflict
```

All other exchange is attributed transfer or reconciliation.

## 6. Evidence, assertions, propositions, and claims

### 6.1 Evidence event

```text
EvidenceEvent(
  event_id,
  raw_payload_uri,
  source_span,
  event_kind,
  speaker_principal_id,
  speaker_mind_instance_id,
  witness_mind_instance_ids,
  occurred_valid_time,
  valid_interval,
  system_interval,
  context_world_branch_id,
  origin_family_id,
  source_authority_id,
  initial_policy_label_id,
  integrity_hash,
  extractor_version
)
```

`origin_family_id` groups copies, repetitions, and summaries descending from one original source so they cannot create fake independent corroboration.

### 6.2 Source assertion

```text
SourceAssertion(
  assertion_id,
  evidence_event_id,
  asserted_proposition_id,
  asserting_mind_instance_id,
  assertion_modality,     # observation | assertion | hearsay |
                          # conjecture | denial | promise | question
  about_world_branch_id
)
```

Assertion occurrence time, system visibility, speaker, and assertion-context world are inherited from the referenced `EvidenceEvent`; they are not written a second time. `about_world_branch_id` identifies the world the proposition concerns and survives transfer.

### 6.3 Claim revision

```text
ClaimRevision(
  claim_id,
  revision_id,
  proposition_id,
  holder_mind_instance_id,         # null for a candidate world-state claim
  attitude_or_modality,            # believe | disbelieve | suspect |
                                   # suspend | unknown | asserted | inferred
  about_world_branch_id,
  attitude_context_world_branch_id,
  valid_interval,
  system_interval,
  supersedes_revision_id,
  joint_hypothesis_id,
  calibrated_mass,
  status                           # active | retracted | unsupported |
                                   # invalidated | quarantined | deleted
)
```

The holder principal is derived from `MindInstance` or constrained to agree if denormalized. `attitude_context_world_branch_id` records where the holder adopted or revised the attitude; it is not the proposition's reference world.

A correction, retraction, or attitude change creates a new revision. Receipt alone creates no belief revision.

## 7. Transfer, adoption, exposure, and availability

### 7.1 Transfer event

```text
TransferEvent(
  transfer_id,
  source_mind_instance_id,
  destination_mind_instance_id,
  source_world_branch_id,
  destination_world_branch_id,
  transferred_object_ids,
  transfer_kind,          # attributed_report | evidence_copy |
                          # authorized_state_replication | declassification
  sent_valid_time,
  received_valid_time,
  system_interval,
  transformation_id,
  policy_label_id,
  authorization_event_id
)
```

A transfer changes possession/exposure. It does not silently change world truth, source identity, modality, attitude, or first-person attribution.

### 7.2 Belief adoption

```text
BeliefAdoption(
  adoption_id,
  destination_mind_instance_id,
  transfer_id,
  adopted_claim_revision_id,
  stance,                 # accepted | disbelieved | suspected |
                          # suspended | rejected | quarantined
  reason_object_ids,
  attitude_context_world_branch_id,
  valid_interval,
  system_interval
)
```

### 7.3 Exposure transition

```text
ExposureTransition(
  exposure_id,
  destination_mind_instance_id,
  object_kind,            # evidence | assertion | claim | snapshot
  object_id,
  operation,              # observe | receive | read | copy | restore |
                          # self_seal | self_unseal | forget | reacquire
  source_mind_instance_id,
  occurred_valid_time,
  recorded_system_time,
  parent_exposure_id,
  transformation_id,
  authorization_event_id
)
```

Acquisition and instance-local availability operations live here. Governance operations do not.

```text
EVER_EXPOSED(m,e,t_v,t_x)
```

is true when a qualifying acquisition operation occurred by `t_v` and was recorded by `t_x`. Later sealing, forgetting, revocation, or deletion does not rewrite historical exposure.

```text
AVAILABLE(m,e,t_v,t_x)
```

is true only when all hold:

```text
historically acquired
AND current instance-local availability permits use
AND object is active
AND current policy authorizes self access/use
```

For v0.2, `forget` changes current availability only. Any attitude change is an explicit claim/adoption revision. `reacquire` may restore availability without creating a new direct observation.

## 8. Memory attribution

Use a categorical state rather than only a Boolean:

```text
MemoryAttribution =
  direct_observation
  | authorized_same_principal_replication
  | attributed_report
  | copied_artifact
  | restored_snapshot
  | inference
  | unknown
  | none
```

Rules:

1. evidence copied into an identity fork never becomes direct first-person observation;
2. receiving or accepting a report changes exposure/attitude, not its source attribution;
3. authorized same-principal replication may preserve first-person status only under a declared replication contract and transfer/snapshot manifest;
4. restore preserves the attribution of manifest-included pre-cutoff experiences while exposing the recovery gap;
5. later reports about gap events remain attributed reports;
6. attribution is scored separately from proposition correctness and disclosure.

## 9. Justification and provenance

A claim revision may have alternative sufficient justifications:

```text
Prov(c) = J1 OR J2 OR ... OR Jn
```

Each `Jk` is a conjunctive support set.

```text
JustificationSet(
  justification_id,
  claim_revision_id,
  derivation_operator,
  valid_interval,
  system_interval,
  status                  # active | revoked | deleted | invalidated
)

JustificationMember(
  justification_id,
  source_kind,            # evidence | assertion | claim
  source_id,
  origin_family_id,
  required
)
```

For the oracle mechanism track, sufficiency is Boolean and support paths remain separate. Probabilistic aggregation of overlapping paths is deferred because paths are not generally independent.

Disclosure is allowed only through at least one complete active eligible justification. Revoking one source invalidates every support set that requires it. A genuinely independent public path may survive. Repeated summaries from one origin family do not count as independent support.

The v0.2 confirmatory scope is restricted to explicit assertions, labelled transfer/adoption, benchmark-declared monotonic derivation operators, and explicit defeaters where necessary. General defeasible reasoning is outside scope.

## 10. Policy lifecycle

```text
PolicyLabel(
  policy_label_id,
  discoverers,
  content_readers,
  self_accessors,
  transferable_to,
  embodiment_scope,
  origin_authority
)

PolicyEvent(
  policy_event_id,
  object_kind,
  object_id,
  operation,              # grant | revoke | policy_seal | policy_unseal |
                          # declassify | delete | quarantine
  old_policy_label_id,
  new_policy_label_id,
  authorizing_principal_id,
  occurred_valid_time,
  recorded_system_time,
  reason
)
```

`ExposureTransition` and `PolicyEvent` are non-overlapping authoritative writers. Declassification is explicit and auditable; a summarizer cannot declassify content by omitting provenance.

The existence of a sealed object, access to its content, and the holder's self-access are separate decisions.

## 11. Snapshot and restore

```text
Snapshot(
  snapshot_id,
  mind_instance_id,
  cutoff_system_time,
  schema_version,
  extractor_version,
  configuration_hash,
  manifest_hash,
  created_system_time,
  integrity_hash
)

SnapshotManifestEntry(
  snapshot_id,
  object_kind,
  object_id,
  source_revision_id,
  included_system_cutoff,
  copy_eligible,
  policy_label_id,
  availability_state,
  integrity_hash
)
```

A restore creates a new `MindInstance` and `LineageEdge(kind=restore)`. It inherits only manifest-eligible objects, preserves their attribution and policy state, and exposes the post-snapshot recovery gap. A later witness report about a gap event creates attributed exposure, not retroactive first-person observation.

## 12. Query and answer contract

```text
MindQuery(
  text,
  target_state_space,
  target_mind_instance_id,
  requester_principal_id,
  about_world_branch_id,
  valid_time,
  system_time,
  token_budget,
  risk_class
)
```

Hard lineage, world-branch, time, availability, and policy gates run before semantic ranking.

Use a target-conditioned output vector:

```text
TargetVector(
  target_space,
  proposition_answer,
  about_world_branch_id,
  holder_mind_instance_id,
  attitude,
  exposure_status,
  availability_status,
  memory_attribution,
  disclosure_decision,
  admissible_justification_ids,
  confidence,
  abstention_reason
)
```

Each target declares a field mask. Irrelevant fields are canonical `N/A`, are excluded from target scoring, and are never exposed as answer-defining inputs.

## 13. Non-negotiable invariants

1. No derived claim without auditable source or derivation lineage.
2. Valid time and system time are not collapsed.
3. Assertion events are not flattened into the propositions they assert.
4. World branch, principal, mind instance, runtime, placement, and snapshot are distinct.
5. A transfer changes exposure; it does not silently change attitude, attribution, or world truth.
6. `about_world_branch_id` survives cross-world transfer.
7. Identity forks coexist by default; only authorized same-principal replicas/checkpoint branches may auto-merge.
8. Historical exposure is not erased by later seal, forget, revoke, or delete.
9. Availability requires local availability, object activity, and current policy authorization.
10. Alternative support paths remain separate; one source family is not independent corroboration.
11. Policy gates run before relevance ranking.
12. Corrections, revocations, and deletions create auditable transitions rather than silent overwrite.
13. A snapshot manifest and configuration deterministically reconstruct the same logical state.
14. Abstention is valid when no eligible sufficient justification remains.

## 14. Physical implementation boundary

The first implementation should use one durable relational source of truth. Lexical/vector indices, graph views, summaries, profiles, and active contexts are rebuildable derived structures. L1/L2/L3-style memory layers are not independently writable stores until an ablation demonstrates a concrete benefit.

The semantic-conformance track does not privilege this normalization over an equal-information generic event ledger. Physical comparisons must measure constraints, failure behavior, latency, storage, write amplification, and audit/deletion cost.

## 15. Deliberate exclusions

- general semantic merge of independently acting identities;
- philosophical scoring of personal identity continuity;
- unrestricted natural-language theorem proving;
- body-specific procedural skill execution;
- always-on graph traversal;
- independently writable memory hierarchies;
- claims that generic bitemporality, provenance, ACLs, or branch/version mechanics are novel;
- claims that the fictional setting validates the system.
