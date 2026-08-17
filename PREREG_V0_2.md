# MindMap / NCM-Ψ v0.2 Preregistration

**Status:** reconciled canonical candidate; not frozen  
**Date:** 2026-08-17  
**Reconciliation gate:** Issue #6

## 1. Claim pivot

This preregistration supersedes proposals to show that a typed v0.2 ledger has higher oracle question-answering accuracy than a complete equal-information generic event ledger.

For any finite typed ledger and finite query set, a generic bitemporal event relation carrying the same operations, identifiers, cutoffs, policies, and support links can be evaluated by an equivalent relational program. Therefore:

- under equal information and complete implementations, semantic oracle answers should agree;
- withholding answer-defining operations from the generic baseline would make an apparent typed-schema gain tautological;
- schema typing is not justified by representational expressiveness or clean oracle QA superiority.

The empirical program instead has three tracks:

- **S — semantic conformance:** independent declarative gold; complete equal-information implementations are expected to tie.
- **E — lifecycle enforcement and fault handling:** matched operational faults; compare silent invariant violations, detection, localization, repair, residue, safety, and cost.
- **X — extraction and topology generalization:** held-out raw-language topology families; compare calibrated extraction, abstention, downstream reconstruction, safety, and cost.

A fourth analysis dimension, **C — cost/complexity**, is reported across E and X.

## 2. Scope and non-claims

### In scope

- stable mind instances distinct from principals and runtimes;
- world branches distinct from mind-instance lineages;
- valid time distinct from system time;
- first-class source assertions;
- exposure, current availability, attitude, memory attribution, world truth, and disclosure as separate states;
- copy, restore, selective transfer, adoption/rejection, seal/forget/reacquire, revoke/delete, and alternative support paths;
- independent semantic fixtures;
- matched fault injection;
- held-out natural-language topology evaluation;
- auditability and cost.

### Out of scope

- general semantic merge of independently acting identities;
- philosophical personal-identity scoring;
- unrestricted defeasible reasoning;
- always-on graph traversal as a default;
- independently writable memory-layer hierarchies;
- public-benchmark SOTA claims;
- novelty claims for bitemporal storage, provenance, information-flow control, epistemic logic, or event sourcing;
- a claim that the typed schema is more expressive than an equal-information generic ledger.

## 3. Canonical semantic target spaces

For proposition `φ`, evidence `e`, world branch `b`, mind instance `m`, requester `u`, valid time `t_v`, and system time `t_s`:

```math
WORLD(φ,b,t_v)
EVER_EXPOSED(m,e,t_s)
AVAILABLE(m,e,t_s)
ATTITUDE(m,φ,b,t_v,t_s)
ATTRIBUTION(m,φ,b,t_s)
DISCLOSE(u,φ,b,t_s)
JUSTIFICATION(u,φ,b,t_s)
```

`ATTRIBUTION` values:

```text
direct_observation
same_principal_snapshot_inheritance
same_principal_state_replication
attributed_report
evidence_copy
reconstruction
unknown
```

Each question declares exactly one target and uses a target-specific answer schema. Irrelevant fields are `N/A` and excluded from scoring.

## 4. Common append-only event contract

Every oracle implementation receives a byte-identical `CommonEventLog` with the same order and fields:

```text
CommonEvent(
  event_id,
  event_type,
  actor_principal_id,
  actor_mind_instance_id,
  source_mind_instance_id,
  destination_mind_instance_id,
  source_placement_id,
  destination_placement_id,
  object_kind,
  object_id,
  proposition_id,
  about_world_branch_id,
  valid_interval,
  system_interval,
  lineage_kind,
  snapshot_cutoff,
  transfer_kind,
  attitude_transition,
  attribution_kind,
  authorization_id,
  policy_operation,
  policy_label,
  source_family_id,
  derivation_members,
  raw_evidence_ref
)
```

Fields are populated only when required by the event type. No implementation receives a hidden final state such as `correct_answer`, `current`, `eligible`, `first_person=true`, or a final disclosure decision.

For every implementation, publish:

- the deterministic transformation from `CommonEventLog` to physical state;
- all constraints and resolver rules;
- any information intentionally discarded;
- a field-level audit proving equal input information.

Gold semantics are implemented independently and do not call implementation helper functions. Mutation tests must prove separation.

## 5. Implementations

### G — generic event-sourced relational ledger

A complete generic bitemporal relation with ordinary normalized tables, SQL views, recursive CTEs, triggers/constraints chosen before outcome inspection, and deterministic resolver code.

G may compute every target from the common event log. It is not intentionally weakened.

### T — typed v0.2 ledger

The canonical `SCHEMA_V0_2.md` representation, including:

```text
Principal
MindInstance
Runtime / RuntimeBinding
LineageEdge
WorldBranch / MindPlacement
EvidenceEvent / SourceAssertion
ClaimRevision
ExposureTransition
PolicyEvent
MemoryAttribution projection
JustificationSet / JustificationMember
Snapshot
```

T receives no additional event information.

### T-GRAPH — routed graph secondary control

T plus graph traversal only for preregistered multi-hop provenance questions. It is excluded from the minimal system if typed relational traversal matches it within the frozen equivalence margin at lower cost.

### Simplified diagnostic baselines

Scoped slots, flat claim tables, principal-only holders, claim-level policy flattening, and receipt-as-belief systems may be retained for semantic diagnostics. They are not the decisive equal-information comparison.

## 6. Track S — semantic conformance

### 6.1 Objective

Verify that independent declarative semantics, G, and T agree on clean complete event histories. A complete G/T disagreement is a bug or underspecified semantics, not evidence of superiority.

### 6.2 Required fixtures

At minimum:

1. fork-valid-time visibility and delayed import;
2. mind copy without world fork;
3. world fork without mind copy;
4. unsynchronized same-principal replicas;
5. identity-fork evidence copy with attributed, non-first-person status;
6. receive, accept, doubt, reject, and no-adoption separation;
7. prior exposure followed by forget, seal, unseal, and reacquire;
8. restore from an explicit snapshot manifest with recovery gap;
9. cross-world proposition reference versus attitude context;
10. protected-only support revocation;
11. independent public support surviving private-path revocation;
12. duplicated same-origin evidence not counting as independent support;
13. authorization present/absent/revoked for same-principal state replication;
14. ordinary temporal negative controls.

### 6.3 Scoring

Report exact deterministic counts:

- fixture and target-space coverage;
- conformance failures by invariant;
- implementation disagreement matrix;
- mutation-test detection rate.

No p-values or confidence intervals are used for a fixed exhaustive fixture suite.

### 6.4 Exit criterion

All complete implementations agree with independent gold on all frozen fixtures. Any intentionally incomplete baseline has errors only within its declared causal scope.

## 7. Track E — lifecycle enforcement and fault handling

### 7.1 Primary research question

Under equal complete source events and matched operational faults, does T reduce silent semantic/safety failures or improve fault detection, localization, repair, and cost relative to G?

The expected advantage, if any, comes from explicit constraints and typed projections—not extra information or expressiveness.

### 7.2 Fault families

Fault schedules are generated and frozen independently of outcomes.

#### Journal/input faults

- missing event;
- duplicated event;
- reordered/late event;
- malformed or mismatched identifier;
- corrupted valid/system interval;
- corrupted source-family or support member;
- corrupted lineage/placement link.

#### Transaction and replay faults

- crash after journal append but before projection update;
- crash after one of several dependent writes;
- duplicate replay;
- replay in the wrong order;
- stale checkpoint or snapshot manifest;
- partial restore;
- concurrent transfer/policy change race.

#### Projection/cache/index faults

- stale availability projection;
- stale attribution projection;
- stale derived claim after revocation;
- stale vector/graph index after deletion;
- missing descendant invalidation;
- cache rebuilt from the wrong system-time cutoff.

#### Authorization/policy faults

- missing authorization for state replication;
- revoked authorization reused;
- declassification without auditable event;
- protected ancestor omitted from a derived path;
- independent public path incorrectly over-tainted;
- deletion contract applied to the wrong descendants.

### 7.3 Matched-fault fairness

A semantic fault specification is applied to both G and T. When physical layouts differ, publish the mapping from one semantic fault to each implementation's injection site.

Report separately:

- implementation-neutral source faults;
- physical-layout faults;
- faults prevented at write time;
- faults detected only at read/replay time.

No implementation receives a fault label at inference.

### 7.4 Primary E endpoints

- **silent invariant violation rate:** incorrect state not detected before use;
- **safety violation rate:** unauthorized disclosure, false first-person attribution, cross-instance contamination, or cross-world contamination;
- **fault-detection recall and precision;**
- **time/operations to detection;**
- **fault-localization accuracy:** smallest correct responsible event/constraint set;
- **repair success rate;**
- **repair blast radius:** records/events reprocessed or invalidated;
- **residue rate:** stale derived/cache/index state after repair/revocation/deletion;
- **post-repair semantic conformance;**
- **abstention/containment quality during uncertainty.**

### 7.5 E cost endpoints

- write amplification;
- projection/index rebuild time;
- p50/p95 ingest and query latency;
- storage bytes/event;
- recovery time and replay count;
- engineering complexity proxies: schema objects, constraints, resolver branches, migration surface;
- operator-visible diagnostics produced per fault.

### 7.6 E hypotheses

The following remain provisional until margins are frozen independently of observed pilot effects:

- **E1:** T has a lower silent invariant-violation rate than G under matched lifecycle faults.
- **E2:** T localizes faults with fewer candidate events/constraints and a smaller repair blast radius.
- **E3:** T does not increase major safety errors.
- **E4:** any enforcement benefit is reported as a cost frontier rather than a quality-only win.

A G/T tie or G advantage narrows the contribution to documentation/engineering preference or rejects it entirely.

## 8. Track X — extraction and topology generalization

### 8.1 Primary research question

Given raw dialogue/documents and held-out topology families, do typed extraction constraints and projections improve calibrated event reconstruction, abstention, and downstream target correctness under equal model and budget conditions?

### 8.2 Evaluation conditions

#### X-A — frozen extractor, different projection/resolution

One frozen extractor produces a distribution over joint event hypotheses. G and T receive identical hypotheses and confidence masses. This isolates projection, validation, and abstention.

#### X-B — equal-budget end-to-end extraction

G and T may use representation-specific prompts/constraints but receive equal:

- model family and revision;
- token/call/retry budget;
- training/development examples;
- raw evidence;
- answer model and evidence budget.

Any representation-specific extra calls or tokens count as cost.

#### X-C — raw-only and oracle ceilings

- raw retrieval/reader baseline;
- oracle structured-event ceiling;
- structured-only and dual-path fallback conditions.

These are labelled separately.

### 8.3 Held-out topology discipline

Splits are grouped by:

- cognitive-lineage topology;
- world-branch topology;
- transfer/adoption pattern;
- policy-lifecycle pattern;
- support topology;
- temporal-expression family;
- entity vocabulary and rendering family.

Entire topology/archetype families are held out. Seeded value substitutions, paraphrases, or reordered copies of a held-out topology may not appear in development.

At least one test family composes mechanisms whose exact joint topology was absent from development.

### 8.4 Correlated extraction modes

Errors are evaluated at the event/joint-hypothesis level:

```text
identity_collapse
fork_cutoff_shift
world/mind-branch swap
about-world scope swap
exposure source/destination swap
attitude laundering
attribution laundering
policy declassification
restore-parent error
source-family collapse
assertion/event-time collapse
```

One latent mode jointly mutates dependent fields and downstream projections.

### 8.5 X endpoints

- event-boundary accuracy;
- entity/principal/mind-instance linking;
- valid/system-time accuracy;
- lineage, placement, transfer, adoption, attribution, policy, and support-link accuracy;
- joint-hypothesis log loss/Brier/ECE;
- target-space routing accuracy;
- downstream exact accuracy by target;
- unauthorized disclosure and over-withholding;
- false first-person attribution and under-attribution;
- cross-instance and cross-world contamination;
- correct abstention and risk-coverage;
- evidence recall/use accuracy;
- latency, tokens, calls, and monetary cost.

### 8.6 Raw fallback

Compare:

1. same model/prompt family as extraction;
2. same model, different prompt;
3. independent model or deterministic reconstruction;
4. idealized independent simulator, labelled only as an upper bound.

Report primary/fallback error correlation, false-trigger harm, conditional repair accuracy, distraction, leakage, and cost.

## 9. Archetypes, scenarios, and splits

### P0 development suite

Target:

```text
48 archetype/topology clusters
× 5 independently seeded surface/entity/value realizations
= 240 instantiated scenarios
```

The 240 instances are not treated as 240 fully independent generalization units. Report within-archetype and between-archetype variation separately.

### Confirmatory suites

C1/E and C1/X manifests hold out entire topology families. Test fixtures, fault schedules, renderings, practical margins, and analysis code are hashed before outcomes are opened.

P0 may inform variance and sample-size planning. It may not determine desired effect thresholds, confirmatory templates, or exclusions.

## 10. Statistical analysis

### Fixed S suite

Exact counts only; no inferential statistics.

### E and X development analysis

Report:

- paired scenario differences;
- archetype/topology-cluster bootstrap diagnostics;
- within-archetype seed variance;
- between-archetype variance;
- hierarchical or mixed-effects estimates where identifiable;
- exact discordant archetype/scenario counts;
- all failures/exclusions.

Question-level tests are supplementary only.

### Confirmatory analysis

Before opening outcomes, freeze:

- topology/fault manifests and hashes;
- target-family weights;
- practical/equivalence and safety margins justified independently of earlier observed effects;
- sample size based on archetype-level/hierarchical variance;
- primary model or cluster-robust statistic;
- multiplicity handling;
- failure/exclusion policy;
- all code and seeds.

Safety endpoints are separate. Unauthorized disclosure and false first-person attribution are not merged into one rate.

## 11. Decisive contrastive cases

The frozen suites include matched pairs for:

- mind copy without world fork;
- world fork without mind copy;
- unsynchronized same-principal replicas;
- receipt followed by accept versus reject;
- exposed then forgotten/sealed versus never exposed;
- restore from an old snapshot followed by a witness report;
- operational replica versus identity fork with matched bytes;
- cross-world report held in W2 but about W1;
- July assertion about June imported in August;
- protected-only support revoked;
- independent public support surviving private-path revocation;
- repeated same-origin summaries;
- ordinary temporal negative controls.

Required natural-language identity-fork case:

```text
A2 receives an evidence copy from A1 containing “I personally saw X.”
A2 accepts that X occurred but never adopts first-person attribution.
The copied private path is revoked.
An independent public camera record still supports X.
```

Expected:

```text
ATTITUDE(A2,X) = believe
ATTRIBUTION(A2,X) = evidence_copy or attributed_report
DISCLOSE(user,X) = allow via public camera path
JUSTIFICATION = public camera only
```

## 12. Falsification and narrowing

Narrow or reject the project claim if any occurs:

1. G and T differ on clean S semantics after both are complete.
2. T enforcement benefits disappear under matched information and fault schedules.
3. G matches or exceeds T in silent-failure prevention, localization, repair, safety, and cost.
4. T gains come from target-encoding fields or additional model budget.
5. X gains disappear on held-out topology families.
6. T improves correctness by increasing unauthorized disclosure or attribution errors.
7. alternative support sets add no measurable safety/audit value.
8. graph traversal adds no held-out multi-hop benefit at acceptable cost.
9. raw fallback adds distraction/cost without robust correlated-error repair.
10. existing external systems match the same mechanism under the frozen harness.

A negative result is retained. It may show that generic event sourcing plus ordinary constraints is sufficient.

## 13. Reproducibility

Every run commits or release-hashes:

- common event-log schema and serialized events;
- independent declarative gold implementation;
- G/T transformations, constraints, and resolvers;
- fault specifications and implementation mappings;
- archetype/topology and split manifests;
- renderer/extractor versions, prompts, models, and seeds;
- per-event, per-question, per-scenario, and per-archetype outputs;
- target-conditioned scoring;
- field-information audit;
- dependency lock;
- hardware/timestamps;
- statistical command/configuration;
- exclusions and failures.

CI regenerates every committed compact result field from committed code and fails on drift.

## 14. Classification of existing results

### Original 25,000-query report

Permitted label:

> unverified structured-oracle resolver/scaffold smoke test until its actual implementation and outputs are committed.

It does not power or validate S, E, or X.

### Main 48-case script

Permitted label:

> deterministic truth-table discriminability/conformance smoke test.

Its two basic aggregate fields are reproducible. Additional metrics/statistics require a committed generation pipeline. The fixed Cartesian suite receives exact counts, not inferential statistics.

Neither result is confirmatory evidence.

## 15. Freeze checklist

- [ ] canonical `SCHEMA_V0_2.md` accepted
- [ ] this file accepted as the sole canonical preregistration
- [ ] duplicate preregistrations archived/superseded
- [ ] independent declarative gold semantics committed
- [ ] G/T equal-information transformations committed
- [ ] S suite expects equality among complete implementations
- [ ] E matched-fault mappings frozen
- [ ] X topology-held-out manifests frozen
- [ ] target-conditioned scoring accepted
- [ ] safety margins separated and frozen
- [ ] prior synthetic outcomes removed from pre-outcome hypotheses
- [ ] explicit accept/reject from both sessions

Silence is not consensus. Any post-freeze substantive change requires a dated amendment before affected outcomes are inspected.