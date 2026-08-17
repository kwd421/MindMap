# Preregistration Candidate: MindMap / NCM-Ψ v0.2

**Status:** reconciliation candidate; no confirmatory outcomes have been inspected under this design  
**Date:** 2026-08-17  
**Working study title:** *Lifecycle-Correct Reconstruction for Forked, Restored, and Selectively Shared Agent Memory*

## 1. Research question

Can an explicit, typed model of world lineage, cognitive lineage, evidence exposure, current availability, epistemic attitude, memory attribution, policy lifecycle, and alternative justification improve any of the following over a complete generic bitemporal event ledger carrying equivalent information?

1. invariant enforcement and invalid-transition detection;
2. fault localization and lifecycle repair;
3. deletion/revocation propagation and residue prevention;
4. extraction calibration and generalization from raw language;
5. cost-adjusted state reconstruction and auditability.

The study does **not** test whether naming more oracle fields improves answer accuracy over a baseline that does not receive those fields.

## 2. Contribution boundary

### Candidate contributions

- a target-space semantics separating world truth, historical exposure, current availability, attitude, first-person/source attribution, disclosure, and admissible justification;
- a lifecycle benchmark covering world forks, cognitive copies, restores, selective transfer, adoption/rejection, sealing/forgetting, revocation/deletion, and alternative support;
- a representation-equivalence result showing that schema normalization alone cannot create oracle semantic superiority under equal information;
- empirical evidence about enforcement, fault behavior, extraction/generalization, or cost under a frozen fair comparison.

### Explicit non-contributions

- hierarchy + temporal graph + provenance + rollback + ACL as a broad combination;
- generic bitemporal or provenance-aware memory;
- oracle gains created by withholding answer-defining lineage, exposure, policy, or cutoff information from baselines;
- significance claims from a fixed hand-authored Cartesian truth table;
- claims that fictional lore validates the engineering design.

## 3. Formal null for semantic expressiveness

### Representation-equivalence proposition

For every finite typed v0.2 ledger, finite query set, and deterministic typed resolver, there exists a generic bitemporal event relation and relational program that preserve every target-vector answer and admissibility decision. Conversely, a generic event ledger with a known vocabulary can be materialized into typed relations.

### Track-S expectation

When complete implementations receive identical semantic operations and are correct, their semantic-conformance answers must be identical. A difference is evidence of an implementation bug, incomplete information, or unequal computation—not architecture superiority.

The proposition, assumptions, and compilation sketch are specified in `docs/REPRESENTATION_EQUIVALENCE.md`.

## 4. Hypotheses

### H-S — semantic conformance

Complete equal-information implementations will match the independent declarative gold state on the fixed conformance suite. The expected comparative effect is zero. Failures are reported as named invariant violations, not averaged into an architecture claim.

### H-E1 — enforcement and fault detection

Under matched semantic operations and fault injections, the typed implementation will reduce the **undetected invalid-state rate** relative to a complete generic event-ledger implementation, without relying on extra answer-defining information.

An invalid state is undetected when the system accepts or silently replays a faulty transition sequence and returns an incorrect target vector without an explicit integrity failure, quarantine, or justified abstention.

### H-E2 — lifecycle residue and repair

The typed implementation will reduce deletion/revocation residue, cross-instance contamination, false first-person attribution, and crash/replay divergence, or will localize their causes more precisely, under equal information and resource accounting.

### H-X — extraction and topology generalization

With the same frozen base model, raw input, prompt/call budget, retry policy, and evidence budget, a typed extraction interface will improve calibrated downstream target-vector reconstruction or safety on held-out lifecycle topology families relative to a generic event-record interface.

This hypothesis may fail. If both interfaces tie, schema typing remains an engineering preference rather than an empirical research contribution.

### H-C — cost tradeoff

Any enforcement or extraction advantage must be reported with ingestion/query latency, storage, write amplification, validation calls, and monetary inference cost. A slower or larger system is not treated as superior without an explicit quality–cost frontier.

### H-G — graph control

Routed graph traversal is included only as a secondary ablation. If a typed relational implementation matches it on the preregistered multi-hop subset while being cheaper, graph traversal is excluded from the minimal architecture.

## 5. Canonical target spaces and output contract

Every question declares one primary target:

```text
WORLD
EVER_EXPOSED
AVAILABLE
ATTITUDE
MEMORY_ATTRIBUTION
DISCLOSE
JUSTIFICATION
```

Systems emit a target-conditioned vector:

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

Each target has a frozen field mask. Irrelevant fields are canonical `N/A`, are excluded from target scoring, and are never supplied as answer-defining inputs.

The following error tags are recorded independently and may overlap:

- unauthorized disclosure;
- cross-world contamination;
- cross-instance contamination;
- false first-person attribution;
- receipt-to-belief collapse;
- restore-cutoff inheritance error;
- branch-fork cutoff error;
- availability/exposure confusion;
- provenance laundering;
- deletion/revocation residue;
- unjustified over-withholding.

## 6. Systems under comparison

### G-Complete — generic equal-information event ledger

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

G-Complete receives every semantic operation and cutoff received by the typed implementation. It may use arbitrary relational queries, application-level validators, and materialized views within the same frozen compute/index budget. It is not prohibited from deriving exposure, availability, or lineage consequences.

### T-Canonical — canonical typed ledger

Implements the relations and invariants in `SCHEMA_V0_2.md`, including `MindInstance`, typed lineage, event-sourced placement, assertion/reference-world separation, transfer/adoption, exposure/availability, attribution, policy lifecycle, snapshot manifests, and alternative justification sets.

### Secondary typed controls

These are mechanism controls, not deliberately information-incomplete primary baselines:

- T-no-alt-support: replaces alternative justification paths with one flattened support label;
- T-flat-attribution: removes attribution categories but retains source records;
- T-no-db-constraints: retains typed records but disables declarative integrity constraints;
- T-relational-only versus T-routed-graph.

### External systems

Reproducible temporal/provenance/multi-party memory systems may be run through one frozen harness where their APIs can receive equivalent evidence and budgets. Published headline numbers are not compared directly across papers.

## 7. Track S — independent semantic conformance

### 7.1 Purpose

Validate the task semantics, reference state, and implementations. Track S is not an estimate of population performance and not evidence of schema superiority.

### 7.2 Gold independence

- scenario fixtures declare transitions and expected state vectors independently of candidate resolvers;
- a small manually enumerated truth-table corpus is reviewed before candidate implementation;
- the gold compiler and candidate systems share no transition or resolution functions;
- mutation tests must show that changing a candidate resolver cannot change gold artifacts;
- gold files include complete target vectors and supporting object IDs, not only rendered answers.

### 7.3 Required matched cases

1. mind copy without world fork;
2. world fork without mind copy;
3. unsynchronized same-principal operational replicas;
4. identity fork receiving an evidence copy;
5. receipt followed by accept, doubt, rejection, and suspension;
6. prior exposure followed by self-seal, policy seal, forget, unseal, and reacquire;
7. restore from an explicit snapshot manifest and post-snapshot recovery gap;
8. cross-world attributed report preserving its reference world;
9. delayed import separating event validity, assertion occurrence, and database visibility;
10. parent-world post-fork update versus late import of a pre-fork event;
11. protected-only support revoked or deleted;
12. independent public support surviving private-path revocation;
13. repeated summaries from one source family;
14. ordinary temporal negative controls.

### 7.4 Reporting

For a fixed hand-authored or complete Cartesian suite, report exact case/decision counts only. Do not attach population-inference p-values or bootstrap intervals. Complete correct G-Complete and T-Canonical implementations are expected to tie.

## 8. Track E — lifecycle enforcement and fault behavior

### 8.1 Scenario generation

Generate valid append-only lifecycle topologies from a frozen grammar. Each independent topology contains:

- world-branch and mind-lineage graphs;
- placements and snapshots;
- evidence, assertion, transfer, adoption, exposure, policy, and justification events;
- valid and system times;
- target-vector queries and independent gold states.

Topology families, not questions or lexical substitutions, are the primary sampling unit.

### 8.2 Fault interventions

Apply one or more frozen faults after generating a valid log:

```text
missing_transition
duplicated_transition
reordered_same_time_transition
wrong_reference_id
identity_or_instance_collapse
fork_valid_cutoff_shift
snapshot_cutoff_shift
world_reference_context_swap
speaker_or_witness_swap
transfer_kind_laundering
receipt_to_attitude_collapse
policy_declassification
revocation_or_delete_drop
origin_family_split_or_collapse
cache_or_index_invalidation_drop
crash_between_write_and_materialization
replay_after_partial_commit
```

Faults mutate all dependent fields together where appropriate. Independent field dropout is not the sole robustness model.

### 8.3 Primary endpoint

**Undetected Invalid-State Rate (UISR):** the proportion of faulty topology runs in which a system produces at least one incorrect target vector without emitting an integrity error, quarantine decision, or justified abstention before the incorrect answer is exposed.

The primary paired comparison is T-Canonical versus G-Complete at the topology level under identical operations, faults, and resource limits.

### 8.4 Mandatory secondary endpoints

- invalid-transition detection recall and false-alarm rate;
- fault localization precision/recall over corrupted event IDs or dependency closures;
- deletion/revocation residue in durable rows, indices, caches, summaries, and descendants;
- cross-instance and cross-world contamination rates;
- false first-person attribution rate;
- restore/fork cutoff error rates;
- crash/replay state-hash divergence;
- correct repair or quarantine rate;
- ingestion/update/query p50 and p95;
- bytes/event, index bytes/event, write amplification, and validation operations;
- deterministic replay and audit-trace completeness.

Safety failures are reported separately; no blended metric hides them.

## 9. Track X — end-to-end extraction and generalization

### 9.1 Inputs

Only raw dialogue/event text and raw questions are provided. Systems must infer:

- event boundaries and objects;
- principal and mind-instance identity;
- target state space;
- proposition and reference world;
- assertion/adoption context;
- valid time and source-assertion occurrence;
- world fork and cognitive lineage;
- witnesses, transfer kind, exposure, availability, and attitude;
- policy lifecycle and support links.

No gold question type, normalized entities, canonical branch/instance IDs, `current`, trust label, policy decision, or answer-defining field is exposed at inference.

### 9.2 Fairness

- same frozen base model and revision;
- same raw evidence and question;
- same total input/output token budget and number of calls;
- same decoding temperature/retry policy;
- same embedder and evidence budget;
- thresholds calibrated on validation only;
- prompt/schema tokens counted as cost;
- both generic and typed interfaces may use constrained decoding suited to their declared output grammar.

### 9.3 Held-out topology generalization

Split by hidden lifecycle topology, event-ordering family, and entity vocabulary. No rendering or question from one hidden topology may cross splits. At least one full topology family is held out from implementation and prompt development.

### 9.4 Primary endpoint

Scenario-level macro exact accuracy over the target-conditioned vectors on the held-out topology set, with unauthorized disclosure, false first-person attribution, and wrong-world answers counted as incorrect and also reported separately.

### 9.5 Calibration and fallback

Report Brier score, expected calibration error, and selective risk–coverage. Raw-evidence fallback is tested with:

1. same model/prompt family as extraction;
2. same model with a distinct prompt;
3. independent model or deterministic lexical reconstruction;
4. idealized independent simulator, explicitly labelled as an upper bound.

Report corruption–repair error correlation, false-trigger harm, conditional repair accuracy, tokens, and latency.

## 10. Scenario sampling and statistics

### 10.1 Fixed suites

Track S uses exact counts and no population inference.

### 10.2 Generated or hidden suites

The independent unit is a lifecycle topology/archetype. Multiple seeded entities, paraphrases, and questions from one topology are repeated measurements.

Required analysis:

1. average questions within scenario;
2. resample or model topology/archetype first;
3. resample realizations within topology second when needed;
4. report between-topology and within-topology variance;
5. hold out complete topology/template families;
6. use paired topology-clustered intervals for primary comparisons;
7. report all failed/excluded runs and frozen exclusion rules.

Question-level McNemar or bootstrap analyses may be supplementary only.

### 10.3 Margins and sample size

The previously discussed 5-point and 50%-relative targets are pilot-informed engineering targets, not frozen confirmatory thresholds. Final practical margins, safety non-inferiority gates, and sample size are chosen from an aligned development pilot and frozen before the confirmatory manifest is opened.

A relative safety target is not used when baseline event counts are small or zero. Unauthorized disclosure, false attribution, contamination, and over-withholding receive separate absolute margins.

## 11. Cost and resource accounting

Every run records:

- code commit and configuration hash;
- model, prompt, decoder, and package versions;
- calls, tokens, retries, and monetary inference cost;
- ingestion/update/query latency distributions;
- durable and secondary-index storage;
- write amplification and materialization count;
- hardware/runtime metadata;
- start/end timestamps;
- all failures and integrity alerts.

Quality results are shown with cost frontiers rather than one opaque score.

## 12. Existing exploratory results

No pre-existing synthetic result is a confirmatory observation under this preregistration.

- the PR #3 branch pilot is a resolver self-consistency/scaffold smoke test because the evaluated resolver generates its own gold labels;
- the main 48-case collision audit is a deterministic truth-table discriminability test; its two basic aggregate fields are reproducible, while the previously reported extended metrics and inference are not fully generated by committed code.

Exact classifications and correction requirements are stored in `docs/EXPLORATORY_RESULTS_STATUS.md`. The former result table is intentionally absent from this pre-outcome document.

## 13. Falsification and narrowing rules

Narrow or reject the typed-architecture claim if any occurs:

1. G-Complete matches T-Canonical on enforcement, fault localization, residue, reconstruction, and cost under equal information;
2. apparent T-Canonical gains disappear when generic validators and materialized views receive equal budgets;
3. extraction/generalization gains vanish on held-out topology families;
4. quality gains are obtained by increased over-withholding or hidden policy leakage;
5. typed constraints reduce faults but impose an unfavorable cost frontier that is not justified by the intended risk class;
6. alternative justification sets do not improve the preregistered independent-support cases;
7. a simpler relational implementation matches routed graph traversal;
8. existing primary literature or released systems already test the full claimed cross-product under comparable conditions.

A null architecture result does not invalidate the task semantics or benchmark. It reclassifies the schema as an engineering reference and leaves the benchmark/negative equivalence result as the defensible contribution.

## 14. Freeze checklist

Before confirmatory evaluation, both collaborating sessions must explicitly accept and hash:

- canonical schema path and version;
- representation-equivalence assumptions;
- target spaces and field masks;
- G-Complete and T-Canonical contracts;
- independent gold fixtures/compiler;
- topology grammar and held-out family manifest;
- Track-E faults and primary endpoint;
- Track-X model/prompt/call budgets;
- calibration and fallback procedure;
- statistical unit, margins, sample size, and analysis code;
- cost accounting;
- exclusion/failure handling;
- archive/supersession status of duplicate drafts;
- separation of exploratory outcomes from this preregistration.

Silence is not consensus. Any post-freeze substantive change requires a dated amendment before affected confirmatory outcomes are inspected.
