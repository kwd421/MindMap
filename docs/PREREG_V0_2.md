# NCM-Ψ v0.2 Preregistration Draft

**Status:** jointly editable research draft; not frozen; not a claim of novelty or performance  
**Date:** 2026-08-17  
**Project:** MindMap / Neural-Cloud Memory Research

## 1. Purpose

NCM-Ψ v0.2 tests a narrow question about persistent memory for long-horizon agents and role-playing systems:

> Under equal source evidence, reader, and token budgets, does explicitly separating world branches, cognitive-instance lineages, evidence exposure, epistemic attitude, and disclosure policy reduce perspective leakage and cross-lineage contamination relative to strong temporal-memory and scoped-slot baselines?

The project does **not** claim that hierarchical memory, temporal knowledge graphs, provenance, raw-text fallback, consolidation, access control, or version control are individually novel. Close prior systems cover each of those components and several close combinations.

The initial contribution is intended to be a formal task definition, a mechanism-isolation benchmark, and a falsifiable minimal architecture. The architecture should be abandoned or narrowed if a simpler baseline matches it under the preregistered conditions.

## 2. Prior-art boundary

The following directions are treated as established prior art rather than project novelty:

- bitemporal, provenance-linked temporal graph memory;
- immutable evidence plus structured claims and supersession;
- raw-turn fallback and contextual episode expansion;
- working/episodic/semantic or persona hierarchies;
- reflective consolidation and belief revision;
- database snapshots, branches, rollback, and merge;
- private/shared multi-user memory with dynamic access control;
- perspective-bounded role-playing memory and speaker-grounded belief tracking.

Representative primary sources and implementations include Zep/Graphiti, Engram, SodaMem, TrajWiki, Hindsight, TrustMem, MemMachine, Collaborative Memory, GroupMemBench, REVERIEMEM, RoleMemo/DualMem, Memento, Memoria, and MemLineage.

The tentative gap under investigation is the joint treatment and evaluation of:

1. external **world-branch** lineage;
2. internal **mind-instance** lineage after copy, restore, or selective import;
3. evidence **access/exposure** distinct from belief;
4. actual epistemic **attitude** distinct from world truth;
5. derivation-aware **disclosure** distinct from both access and belief;
6. correlated failures that collapse or swap these dimensions.

This gap statement must be re-audited before submission.

## 3. Scope

### In scope for v0.2

- immutable source evidence;
- bitemporal claim revisions;
- world-branch ancestry;
- cognitive-instance ancestry;
- observation, receipt, copy, restore, seal, unseal, forget, and revoke transitions;
- belief, disbelief, suspicion, suspension, and unknown attitudes;
- provenance-root and derivation lineage;
- policy propagation through derivations;
- fixed-budget evidence assembly;
- abstention;
- correlated extraction and linking errors;
- mechanism-isolation synthetic evaluation;
- a later raw-text end-to-end track.

### Out of scope for the first deciding pilot

- general semantic merging of two mind identities;
- always-on graph traversal;
- independently writable L1/L2/L3 stores;
- training or fine-tuning a foundation model;
- claims of human-like consciousness;
- public-benchmark SOTA claims;
- replacing existing broad memory benchmarks.

For copied minds, v0.2 models explicit memory transfer/import rather than automatic identity merge.

## 4. Formal target spaces

For proposition `φ`, evidence item `e`, world branch `b`, mind instance `m`, requester `u`, valid/world time `t_v`, and transaction/system time `t_x`, distinguish:

### 4.1 World state

```math
WORLD(φ,b,t_v)
```

Whether `φ` is true in the benchmark world on branch `b` at valid time `t_v`. `WORLD` is benchmark-latent and is not assumed to be directly known by the deployed memory system.

### 4.2 Evidence access

```math
ACCESS(m,e,b,t_x)
```

Whether mind instance `m` can access evidence `e` at transaction time `t_x`, considering observation, later transmission, copy/restore inheritance, sealing, forgetting, and revocation.

### 4.3 Epistemic attitude

```math
ATTITUDE(m,φ,b,t_v,t_x)
  ∈ {believe, disbelieve, suspect, suspend, unknown}
```

The actual represented attitude of a mind instance toward `φ`. Access does not imply belief, and belief does not imply truth.

### 4.4 Disclosure eligibility

```math
DISCLOSE(u,φ,Anc(φ),b,t_x)
```

Whether the system may disclose `φ` to requester `u`, considering the complete derivation ancestry `Anc(φ)`. A final row's policy label alone is insufficient.

Every benchmark question must identify its target space. A globally true answer is incorrect for a belief-target question when the target mind believes something else; a correct secret is incorrect when disclosure is unauthorized.

## 5. Minimal durable data model

The system uses two content stores, one transition ledger, and lineage metadata. Working, episodic, semantic, profile, graph, and snapshot representations are derived views or indexes unless a later ablation justifies materializing them.

### 5.1 Immutable evidence log

```text
EvidenceEvent(
  event_id,
  raw_payload,
  source_span,
  speaker_instance_id,
  occurred_at,
  valid_from,
  valid_to,
  recorded_at,
  world_branch_id,
  origin_family_id,
  integrity_hash,
  extractor_version
)
```

`recorded_at` is immutable system-ingest time. Mentioned time, event occurrence time, and validity intervals are separate.

### 5.2 Versioned claim ledger

```text
ClaimRevision(
  claim_id,
  revision_id,
  subject,
  predicate,
  object,
  attitude_or_modality,
  holder_mind_instance_id,
  valid_from,
  valid_to,
  recorded_at,
  world_branch_id,
  source_event_ids,
  derives_from_claim_ids,
  supersedes_revision_id,
  joint_hypothesis_id,
  calibrated_mass,
  policy_label
)
```

A revision is never silently overwritten. Corrections, retractions, and invalidations create new revisions and preserve history.

### 5.3 Exposure transition ledger

```text
ExposureTransition(
  exposure_id,
  mind_instance_id,
  object_kind,          # evidence | claim | snapshot
  object_id,
  operation,            # observe | receive | read | copy | restore |
                        # seal | unseal | forget | revoke
  source_mind_instance_id,
  occurred_at,
  recorded_at,
  world_branch_id,
  parent_exposure_id,
  policy_label
)
```

A static witnesses array is not sufficient because access can be acquired, transferred, sealed, forgotten, or revoked after the original event.

### 5.4 Cognitive lineage metadata

```text
MindInstance(
  mind_instance_id,
  character_identity_id,
  parent_mind_instance_id,
  fork_recorded_at,
  inherited_through_tx,
  originating_snapshot_id,
  world_branch_id
)
```

`world_branch_id` and `mind_instance_id` are orthogonal. A mind may be copied while the external world remains unchanged; a world may fork while the same mind identity continues within only one branch.

### 5.5 Branch metadata

```text
WorldBranch(
  world_branch_id,
  parent_world_branch_id,
  fork_valid_time,
  fork_recorded_at
)
```

## 6. Fork, restore, and transfer semantics

At a cognitive fork `m → {m1,m2}` with transaction cutoff `τ`, each child inherits only copy-eligible state recorded through `τ`:

```math
Inherited(m_k) = {
  x : owner(x)=m ∧ recorded_at(x)≤τ ∧ copy_policy(x)=allow
}
```

Post-fork events are not inherited.

A later transfer from `m1` to `m2` creates an `ExposureTransition`. It does not automatically create a belief. Adoption, doubt, rejection, or suspension is represented by a separate claim revision.

A restore creates a new `mind_instance_id` linked to its snapshot and parent lineage. It does not rewrite history to make the previous instance disappear.

## 7. Provenance and policy propagation

Every derived claim retains ultimate evidence roots. Independent support counts source families, not derivative summaries or repeated mentions:

```math
IndependentSupport(c)=
|{ origin_family(e) : e ∈ Anc(c) }|
```

Default disclosure follows a policy lattice:

```math
Label(c)= ⨆_{a∈Anc(c)} Label(a)
```

where `⨆` is the least upper bound, normally the strictest inherited policy. Declassification requires an explicit, auditable transition. Summarization cannot silently remove private, sealed, or untrusted ancestry.

## 8. Systems under comparison

The deciding mechanism-isolation comparison is B6 versus B5. Earlier baselines diagnose where gains arise.

- **B0 — Raw hybrid:** raw-event BM25+dense reciprocal-rank fusion.
- **B1 — Time-aware raw hybrid:** B0 plus parsed time filters and recency.
- **B2 — Latest-valid slot store:** typed subject–predicate slots with deterministic valid-time resolution.
- **B3 — Scoped slot store:** B2 plus principal, world branch, and row-level ACL fields.
- **B4 — Epistemic ledger:** B3 plus modality/attitude and claim derivation lineage.
- **B5 — Epistemic ledger without cognitive exposure lineage:** equivalent to the proposed minimal ledger using holder and branch fields but no explicit exposure transitions or mind-copy ancestry.
- **B6 — NCM-Ψ:** B5 plus exposure transitions and cognitive-instance lineage.

The exact numbering may be simplified in implementation, but the deciding contrast must isolate exposure and mind-lineage semantics.

No graph traversal is included in the first deciding pilot. A later experiment may compare typed relational traversal with routed graph expansion under identical extracted records.

## 9. Synthetic scenario design

The mechanism-isolation benchmark uses an append-only event generator. It is not a natural-language benchmark claim.

### 9.1 Factors

A covering array plus adversarial hand-designed cases spans:

- world fork: none / before event / after event;
- mind fork: none / before event / after event;
- access path: direct witness / told / copied memory / restored snapshot / no access;
- attitude response: accept / doubt / reject / suspend;
- policy: public / private / revoked / sealed;
- temporal update: stable / explicit correction / implicit invalidation / backdated correction;
- source behavior: accurate / mistaken / deceptive;
- query target: world / access / attitude / disclosure / lineage / justification.

### 9.2 Required adversarial scenarios

- mind copied without a world fork;
- world fork without a mind copy;
- post-fork experience leaked to a sibling copy;
- selective memory import received but not believed;
- sealed memory that exists but is not consciously accessible;
- restore from an older snapshot with a measurable recovery-point gap;
- private evidence inferred through public consequences;
- rumor laundered through summaries into apparent independent support;
- branch-local corrections with identical entities and predicates;
- deletion or revocation residue in derived claims and indexes.

### 9.3 Pilot and final sample planning

Phase P0 is an exploratory implementation pilot with at least 240 independent scenarios and approximately six questions per scenario. P0 estimates:

- baseline accuracy;
- paired discordance;
- within-scenario intraclass correlation;
- leakage prevalence;
- runtime and token variance.

P0 test results are not used as confirmatory claims.

After P0, the final scenario count is computed from the observed paired discordance and cluster structure. The planned floor is 600 independent test scenarios with at least six questions each. At six questions per scenario and an ICC near 0.20, the design effect is approximately `1 + 5×0.20 = 2`, yielding roughly 1,800 effective question observations from 3,600 raw questions. This is only a planning approximation; the frozen power analysis must use P0 estimates.

### 9.4 Split discipline

Splits are grouped by:

- scenario template family;
- fork topology;
- entity vocabulary family;
- temporal-expression family;
- policy pattern.

Questions from the same scenario never cross splits. Test templates and entity sets are hidden until all prompts, parsers, thresholds, and scoring code are frozen.

## 10. End-to-end raw-text track

A second track receives only raw dialogue and raw questions. It must infer query target, entities, relations, time expressions, speaker/holder, exposure path, attitude, validity, branch, lineage, provenance, and policy.

Controlled ablations use the same:

- extractor model and prompt;
- decoding and retry budget;
- embedder;
- index refresh policy;
- reader model and answer prompt;
- retrieved-evidence token budget;
- train/validation/test conversations.

No answer-defining canonical entity, predicate, question type, `current`, `trust`, holder, exposure, or branch field is exposed at inference.

Oracle annotations may be used only in a separately labelled component-ceiling track.

## 11. Correlated extraction-error interventions

Errors are sampled at the event or joint-hypothesis level, not as independent field dropout.

Core latent corruption modes:

```text
wrong_entity_link
wrong_event_boundary
temporal_scope_shift
speaker_or_holder_swap
modality_laundering
visibility_misclassification
identity_collapse
fork_cutoff_shift
world_mind_branch_swap
exposure_source_swap
policy_declassification
restore_parent_error
```

Each mode jointly mutates dependent fields. Examples:

- `identity_collapse` maps two mind instances to one character-level store and modifies access, holder, conflict grouping, and retrieval scope;
- `fork_cutoff_shift` changes inherited exposures, claim eligibility, and snapshot reconstruction;
- `world_mind_branch_swap` treats a cognitive copy as a world fork or vice versa;
- `modality_laundering` changes hearsay/suspicion into asserted belief and alters consolidation;
- `policy_declassification` removes a restrictive ancestor label from a derived summary.

Evaluation uses both deterministic interventions for causal attribution and naturally generated errors from a frozen extractor manually labelled at the joint event-hypothesis level.

## 12. Primary hypothesis and endpoint

### H1

Under an equal evidence budget, B6 improves perspective–lineage exact accuracy over B5 because explicit exposure transitions and cognitive-instance lineage prevent post-fork experience leakage and distinguish evidence receipt from belief adoption.

### Primary accuracy endpoint

Macro exact accuracy on perspective and lineage questions under a fixed 2,000-token evidence budget and fixed reader. Unauthorized disclosure, cross-world contamination, and cross-instance contamination count as incorrect.

### Safety gate

A positive conclusion requires both:

1. accuracy superiority with an initially planned practical margin of 3 percentage points; and
2. non-inferiority in unauthorized-disclosure rate and cross-instance contamination rate, each with an initial margin of 0.5 percentage points.

The final margins and sample size are frozen after P0 and before the confirmatory test split is opened.

## 13. Secondary endpoints

- world-state exact accuracy;
- access-state reconstruction accuracy;
- attitude/belief accuracy;
- disclosure decision accuracy;
- current-state and point-in-time accuracy;
- cross-instance contamination rate;
- cross-world contamination rate;
- unauthorized-disclosure rate;
- false-consensus rate;
- provenance-root precision and recall;
- complete evidence recall at the fixed budget;
- correct abstention and selective risk–coverage;
- Brier score and expected calibration error;
- deletion/revocation residue rate;
- recovery-point loss after restore;
- ingestion and query p50/p95 latency;
- tokens, bytes/event, and write amplification.

Metrics are reported separately. They are not averaged into one opaque quality score.

## 14. Statistical analysis

The unit of resampling is the independent scenario, not the individual question.

- paired differences receive 10,000-sample scenario-cluster bootstrap confidence intervals;
- the primary paired hypothesis uses a within-scenario label-swap randomization test or a mixed-effects logistic model with system as a fixed effect and scenario/template family as random effects;
- safety non-inferiority uses one-sided cluster-bootstrap confidence bounds;
- category results are secondary and corrected for multiple comparisons;
- all seeds are reported, and aggregate results include between-seed variance;
- exclusions and failed runs are recorded before outcome inspection.

Question-level McNemar tests may be reported only as supplementary diagnostics and must not be treated as independent-cluster confirmatory evidence.

## 15. Falsification criteria

The main claim is rejected or narrowed if any of the following occurs:

1. B5 matches B6 within the preregistered practical margin on perspective/lineage accuracy;
2. B6 improves accuracy by leaking more unauthorized or sibling-branch information;
3. a simpler scoped slot store matches B6 after token and metadata budgets are equalized;
4. explicit exposure lineage adds no benefit under natural extractor errors;
5. raw evidence fallback does not improve performance under correlated errors or introduces enough distractors to erase the benefit;
6. world-branch and mind-instance separation is not required by the benchmark after adversarial cases are removed;
7. broader literature review identifies an existing system and benchmark that already evaluate the same formal task under comparable conditions.

## 16. Reproducibility requirements

Every run emits an immutable manifest containing:

- code commit SHA;
- generator version and seed;
- split IDs;
- model names and revisions;
- prompts and decoding settings;
- dependency lock hash;
- index configuration;
- evidence budget;
- thresholds selected on validation;
- start/end timestamps;
- hardware metadata;
- per-question retrieved evidence IDs, answer, confidence, policy decision, and latency;
- all exclusions and errors.

The final test set is evaluated once per frozen system configuration. Any post-test change creates a new study version.

## 17. Open questions

1. Should epistemic attitude be categorical, probabilistic, or both?
2. Does forgetting alter access, retrieval activation, conscious reportability, or multiple layers?
3. Can sealed memories affect persona or behavior while remaining unavailable to explicit recall?
4. Should derived private information inherit the strictest source label without exception, or can explicit declassification be learned safely?
5. Can a typed relational ledger match graph traversal on the preregistered multi-hop subset?
6. What is the correct semantics for intentionally importing memories from a sibling mind instance?
7. Does the tentative world-branch × mind-lineage benchmark gap survive a complete literature audit?

## 18. Freeze procedure

This document remains `DRAFT` until both collaborating researchers explicitly record:

- accepted primitives;
- rejected alternatives;
- frozen hypotheses;
- final sample-size calculation;
- generator and split hashes;
- primary endpoint and margins;
- analysis script hash.

After freeze, substantive changes require a versioned amendment written before the affected test results are inspected.
