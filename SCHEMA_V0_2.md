# NCM-Ψ / MindMap Schema v0.2

**Status:** provisional collaborative research schema  
**Date:** 2026-08-17  
**Scope:** branch-local epistemic reconstruction, selective cross-lineage transfer, policy lifecycle, and auditable source support for long-horizon agents.

## 1. Research position

The broad combination of hierarchical memory, temporal graphs, provenance, raw fallback, consolidation, snapshots, and retrieval is a systems synthesis rather than the central novelty claim. The v0.2 target is narrower:

> Reconstruct what a principal was entitled to believe, remember in first person, and disclose at a specified world time and system time after forks, restores, selective transfers, adoption decisions, revocations, and alternative derivations.

`MindMap` is an engineering project term inspired by Korean localization usage. It is not claimed to be identical to one canonical Girls' Frontline data structure.

- **MindMap:** versioned logical state of one principal, including beliefs, memories, commitments, capabilities, policies, and lineage.
- **Memory substrate:** durable evidence and claim store from which a MindMap can be reconstructed.
- **Active projection:** bounded, query-specific context materialized from one MindMap for one decision.

## 2. State spaces

For proposition \(\phi\), branch \(b\), world-valid time \(t_v\), system time \(t_s\), holder \(p\), and requester \(u\):

\[
WORLD(\phi,b,t_v)
\]

asks whether \(\phi\) is true in the represented world.

\[
BELIEF(p,\phi,b,t_v,t_s)
\]

asks the epistemic state of principal \(p\) toward \(\phi\).

\[
REMEMBER_1P(p,\phi,b,t_s)
\]

asks whether \(p\) may attribute \(\phi\) to its own first-person experience rather than to an imported report or copied artifact.

\[
DISCLOSE(u,\phi,b,t_s)
\]

asks whether the system may expose an answer and supporting evidence to requester \(u\).

These spaces must not be collapsed. A false rumor can be the correct answer to a belief query; a true secret can be the wrong answer to a disclosure query; a copied memory can support belief without becoming first-person experience.

## 3. Temporal model

v0.2 uses **bitemporal records with first-class assertion events**.

- `valid_interval`: when the represented object held in the application/world model.
- `system_interval`: when the object/version was visible in the memory database.

A source assertion is itself an event. Its assertion time is the valid time of that event, while the asserted proposition has its own valid interval.

```text
SourceAssertion A:
  proposition: Bob asserted C
  valid_interval:  [2026-07-10, 2026-07-10]
  system_interval: [2026-08-17, +inf)

Claim C:
  proposition: Alice moved to Busan
  valid_interval:  [2026-06-01, +inf)
  system_interval: [2026-08-17, +inf)

ASSERTS(A, C)
```

This preserves three clocks—world validity, source assertion, and system commit—without claiming that every row implements three independent temporal dimensions.

## 4. Durable entities

### 4.1 Principal

```text
Principal(
  principal_id,
  principal_kind,          # person | character | agent | organization
  created_system_time,
  retired_system_time,
  governance_policy_id
)
```

A principal holds permissions, commitments, and social identity.

### 4.2 Runtime

```text
Runtime(
  runtime_id,
  principal_id,
  embodiment_id,
  model_manifest,
  started_system_time,
  stopped_system_time
)
```

A body, process, or model session can change without changing principal identity.

### 4.3 MindState

```text
MindState(
  state_id,
  principal_id,
  branch_id,
  parent_state_ids,
  system_time,
  evidence_cutoff,
  extractor_manifest,
  policy_manifest,
  state_hash
)
```

A snapshot is a reproducible pointer to state and manifests, not an opaque summary blob.

### 4.4 LineageEdge

```text
LineageEdge(
  edge_id,
  kind,                    # checkpoint_branch | operational_replica |
                           # restore | identity_fork | template_reset |
                           # fragment_reconstruct
  source_principal,
  destination_principal,
  source_state,
  destination_state,
  created_system_time,
  authorization_id,
  recovery_gap_start,
  recovery_gap_end
)
```

#### Merge invariant

```text
AUTO_MERGE(a,b) iff
  same_principal(a,b)
  AND lineage_kind(a,b) in {checkpoint_branch, operational_replica}
  AND merge_contract_authorizes(a,b)
  AND no non_commutative_identity_bearing_conflict(a,b)
```

An `identity_fork` creates a new principal and is non-mergeable by default. Exchange is represented as attributed transfer or reconciliation.

## 5. Evidence and claims

### 5.1 EvidenceEvent

```text
EvidenceEvent(
  event_id,
  raw_payload_uri,
  source_span,
  event_type,
  speaker_principal,
  witness_set,
  valid_interval,
  system_interval,
  branch_id,
  origin_authority,
  discoverability_policy,
  content_policy,
  self_access_policy,
  transfer_policy,
  embodiment_scope,
  source_family_id,
  integrity_hash,
  extractor_version
)
```

The raw journal is append-only except under an explicit deletion contract. Every derived object must remain traceable to evidence or another auditable derivation.

### 5.2 SourceAssertion

```text
SourceAssertion(
  assertion_id,
  event_id,
  asserted_proposition_id,
  asserting_principal,
  assertion_modality,      # observation | assertion | hearsay |
                           # conjecture | denial | promise
  valid_interval,
  system_interval,
  branch_id
)
```

### 5.3 ClaimRevision

```text
ClaimRevision(
  claim_id,
  revision_id,
  proposition,
  holder_principal,        # null for world-state claim
  epistemic_modality,      # believed | doubted | rejected | inferred |
                           # quarantined | unknown
  valid_interval,
  system_interval,
  branch_id,
  source_assertion_ids,
  derives_from_claim_ids,
  joint_hypothesis_id,
  calibrated_mass,
  supersedes_id,
  status                   # active | unsupported | invalidated | deleted
)
```

A received assertion does not automatically create a belief revision.

### 5.4 JustificationSet

```text
JustificationSet(
  justification_id,
  claim_revision_id,
  source_event_ids,
  source_claim_ids,
  source_family_ids,
  derivation_operator,
  policy_label,
  confidence_mass,
  valid_interval,
  system_interval,
  defeater_ids,
  status                   # active | revoked | deleted | invalidated
)
```

A claim may have several alternative support sets. This prevents both provenance laundering and permanent over-taint.

For v0.2, confirmatory benchmark derivations are restricted to explicitly specified monotonic operators or labelled belief-adoption operations. Open-ended defeasible inference is evaluated separately.

## 6. Transfer and adoption

### 6.1 TransferEvent

```text
TransferEvent(
  transfer_id,
  source_principal,
  destination_principal,
  source_branch,
  destination_branch,
  transferred_ids,
  transfer_kind,           # report | evidence_copy | state_replication |
                           # declassification
  sent_valid_time,
  received_valid_time,
  system_interval,
  transformation,
  transfer_policy,
  authorization_id
)
```

### 6.2 BeliefAdoption

```text
BeliefAdoption(
  adoption_id,
  destination_principal,
  destination_branch,
  transfer_id,
  adopted_claim_id,
  stance,                  # accepted | doubted | rejected | quarantined
  reason_source_ids,
  valid_interval,
  system_interval
)
```

#### Transfer invariants

1. Receipt is not belief.
2. Belief is not first-person memory.
3. An identity fork receiving copied state obtains attributed evidence, not self-observation.
4. First-person state replication requires the same principal, an eligible lineage kind, and prior authorization.
5. A transformation must preserve the source identity and modality unless a separately auditable operation changes them.

## 7. Policy model

```text
PolicyLabel(
  discoverers,
  content_readers,
  self_accessors,
  transferable_to,
  embodiment_scope,
  origin_authority
)
```

Default derived policy is the restrictive meet/intersection of every source in one justification set. Relaxation requires an explicit authorized event.

```text
PolicyEvent(
  policy_event_id,
  kind,                    # grant | revoke | declassify | delete_evidence |
                           # delete_derived
  target_ids,
  actor_principal,
  valid_interval,
  system_interval,
  authorization_id,
  reason
)
```

### 7.1 Disclosure by alternative support

Let `Just(c)` be the active justification sets of claim \(c\).

\[
CanDisclose(u,c,\tau)=
\exists J\in Just(c):
Active(J,\tau)\land PolicyAllows(J,u,\tau)
\land SupportSufficient(J,c,\tau)
\]

Deleting or revoking one source invalidates every support set that depends on it. An independently supported public justification may survive. No summary can declassify material by dropping a provenance link.

### 7.2 Discoverability versus content

The existence of a sealed record and access to its content are separate decisions:

```text
may_discover(record, principal)
may_read_content(record, principal)
may_self_recall(record, principal)
```

## 8. Query contract

```text
MindQuery(
  text,
  target_state_space,      # WORLD | BELIEF | REMEMBER_1P | DISCLOSE
  target_holder,
  requester,
  branch_id,
  valid_time,
  system_time,
  token_budget,
  risk_class
)
```

### 8.1 Hard eligibility before ranking

\[
Eligible(m,q)=
LineageVisible(m,q.branch)
\land SystemVisible(m,q.system\_time)
\land ValidCompatible(m,q.valid\_time)
\land Discoverable(m,q.requester)
\land SelfAccessCompatible(m,q.target\_holder)
\]

Semantic relevance must never override lineage, time, or policy eligibility.

### 8.2 Retrieval and projection

1. Parse target state space and principals.
2. Apply lineage, system-time, and policy gates.
3. Retrieve raw evidence and claims with lexical+dense fusion and typed indices.
4. Resolve valid-time revisions and contradictory support.
5. Expand a bounded relation graph only for a routed multi-hop subset.
6. Select evidence under a fixed token budget.
7. Return an answer with admissible justifications or abstain.

```text
MindAnswer(
  answer,
  target_state_space,
  holder,
  epistemic_modality,
  first_person_status,
  source_principal,
  justification_ids,
  disclosure_decision,
  confidence,
  abstention_reason
)
```

## 9. Physical implementation

The first implementation should have one durable relational source of truth:

- PostgreSQL tables for evidence, assertions, claims, justification sets, lineage, transfer, adoption, and policy events;
- FTS/BM25 and vector indices as rebuildable secondary indices;
- optional graph views derived from typed relations;
- object storage for raw multimodal payloads;
- caches keyed by branch, system-time cutoff, policy manifest, and state hash.

Working, episodic, semantic/core, profile, and graph layers begin as views or materializations, not independently writable stores.

## 10. Deletion contracts

v0.2 distinguishes:

1. **Evidence deletion:** source becomes unretrievable; dependent justification sets are invalidated.
2. **Derived-data erasure:** summaries, embeddings, caches, and claims whose active supports depend on the source are removed or quarantined.
3. **Epistemic correction:** proposition is marked false or unsupported while audit history remains.
4. **Owner/legal erasure:** policy-defined removal beyond ordinary epistemic semantics; deferred from research claims.

The benchmark initially tests contracts 1 and 2.

## 11. Non-goals for v0.2

- general semantic merge of independently acting identities;
- philosophical scoring of personal identity continuity;
- always-on graph traversal;
- unrestricted natural-language theorem proving over hidden policies;
- body-specific procedural skill execution;
- claiming the fictional setting validates the engineering design.
