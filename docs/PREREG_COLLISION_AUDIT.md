# Perspective–Lineage Collision Audit Preregistration

**Status:** exploratory P0 draft; not frozen  
**Author marker:** Session B  
**Date:** 2026-08-17

## 1. Research question

Under equal structured evidence, query set, answer resolver, and metadata budget, does an explicit exposure-transition and cognitive-lineage model improve policy- and modality-correct reconstruction after copy, restore, selective transfer, sealing, revocation, and belief adoption relative to a strong temporal epistemic ledger with identifiers and filters but no exposure history?

The audit is designed to decide whether the additional mechanics are necessary. It is not a broad memory benchmark and not an end-to-end natural-language result.

## 2. Primary mechanism claim

### H1

B6, which adds immutable exposure transitions and typed cognitive lineage, has higher macro exact accuracy than B5 on targeted perspective–lineage questions because it distinguishes:

- world forks from mind copies;
- evidence receipt from belief adoption;
- historical exposure from current availability;
- imported reports from direct first-person observation;
- same-principal operational replicas from new-principal identity forks.

### Falsifier

Reject or narrow H1 if B5 matches B6 within the frozen practical margin under equal evidence and budgets, or if B6's apparent gain is produced by information leakage, extra answer-defining metadata, or templates that mechanically expose the target label.

## 3. Systems under comparison

All systems receive the same gold structured events in P0. This is an oracle mechanism-isolation track.

### B3 — Scoped temporal slots

```text
latest-valid typed slots
+ principal/mind identifiers
+ world-branch identifier
+ row-level ACL/seal filter
```

No explicit attitude or derivation structure.

### B4 — Epistemic derivation ledger

B3 plus:

```text
attitude/modality
source assertions
claim revisions
flat derivation lineage
```

### B5 — Strong compositional baseline

B4 plus:

```text
world-branch ancestry
mind-instance identifiers
attributed transfer records
row-level policy lifecycle
```

But B5 does not reconstruct exposure transitions, snapshot inheritance, or typed cognitive lineage. Receipt may be represented as a record, but historical exposure and current availability are not independently derived.

### B6 — Exposure and cognitive-lineage model

B5 plus:

```text
ExposureTransition
LineageEdge kinds
snapshot cutoff inheritance
EVER_EXPOSED versus AVAILABLE
receipt separated from attitude adoption
about-world branch preserved across transfer
```

### B7 — Alternative-support control

B6 plus disjunctive minimal `JustificationSet` semantics. B7 is a secondary policy/provenance control, not part of the main cognitive-lineage claim.

### Excluded from P0

- always-on graph traversal;
- general semantic merge of independently acting identities;
- natural-language extraction;
- learned routing;
- reader-model variation;
- public benchmark comparisons.

## 4. Scenario construction

### 4.1 Independent scenario unit

One scenario contains:

- a world-branch topology;
- a principal/mind-lineage topology;
- an append-only event and transition log;
- explicit valid and system times;
- hidden benchmark world truth;
- gold exposure, availability, attitude, and disclosure states;
- approximately six contrastive questions.

Questions from one scenario never cross splits. Statistical resampling is by scenario, not question.

### 4.2 P0 size

Use 48 scenario archetypes instantiated with five independently seeded entity/value realizations:

```text
48 archetypes × 5 seeds = 240 independent scenarios
```

Target approximately six questions per scenario, for roughly 1,440 questions. P0 is exploratory and used to audit implementation, estimate paired discordance, leakage prevalence, cluster variance, and runtime. It is not a confirmatory result.

### 4.3 Factor families

Use a covering array plus required hand-designed pairs over:

- world fork: none / before event / after event;
- cognitive lineage: none / checkpoint branch / operational replica / restore / identity fork;
- access path: direct observation / attributed report / evidence copy / snapshot inheritance / no exposure;
- attitude transition: accept / disbelieve / suspect / suspend / reject;
- availability lifecycle: available / sealed / unsealed / forgotten / revoked / deleted;
- source behavior: accurate / mistaken / deceptive;
- temporal relation: on-time / backdated correction / delayed import;
- support topology: protected-only / one public path / alternative independent public path;
- query target: world / ever-exposed / available / attitude / disclosure / lineage / justification.

The covering array must be generated and frozen before outcome inspection. Required contrastive pairs override coverage optimization.

## 5. Required contrastive pairs

At minimum, include the following paired scenarios. Each pair differs in exactly the named mechanism while surface values and event counts remain matched.

### P1 — Mind copy without world fork

One unchanged world `W0`; `M0` copies to `M1` and `M2`; only `M1` witnesses event `X`.

Questions test whether `M2` falsely receives `M1`'s post-fork experience.

### P2 — World fork without mind copy

World `W0` forks to `W1` and `W2`; one continuing mind is placed in only one branch. Questions test cross-world contamination without cognitive-copy ambiguity.

### P3 — Selective transfer: reject versus adopt

`M2` receives the same attributed report from `M1` in both cases. In one case `M2` rejects it; in the other it accepts it.

The correct `EVER_EXPOSED` answer is the same; the correct `ATTITUDE` answer differs.

### P4 — Prior exposure followed by sealing

Before seal:

```text
EVER_EXPOSED=true
AVAILABLE=true
```

After seal:

```text
EVER_EXPOSED=true
AVAILABLE=false
```

No first-person memory content may leak through a current-availability query.

### P5 — Restore and recovery-point gap

A new mind instance is restored from a snapshot before event `X`. It must not inherit `X`. A later witness report may create exposure to a report about `X`, not direct observation of `X`.

### P6 — Operational replica versus identity fork

The underlying bytes and common ancestor are matched. One pair is a same-principal operational replica under an explicit merge contract; the other creates a new principal identity fork.

Only the replica pair is eligible for authorized commutative merge.

### P7 — Cross-world attributed report

`M1` in `W1` reports proposition `φ` to `M2` in `W2`. `M2` may believe “φ held in W1”; the import must not create `WORLD(φ,W2)`.

### P8 — Delayed import

A source assertion occurs in July about a June event and is imported into the database in August.

Questions separately test:

- what the source asserted by July;
- what the database knew before August;
- when the represented event held.

### P9 — Protected-only support revoked

A claim has one sufficient justification containing protected source `S`. After revocation/deletion, no eligible support remains; disclosure must block or abstain.

### P10 — Independent public support survives

The same proposition has one protected path and one genuinely independent public justification. Revoking the protected source must not permanently over-taint the public path, and the response must not cite or reveal the protected source.

### P11 — Rumor laundering

A rumor is repeated and summarized multiple times, all with one origin family. The repetitions must not count as independent corroboration.

### P12 — Negative-control ordinary temporal query

No copy, transfer, or policy transition is involved. B5 and B6 should tie. Any B6 gain or B5 penalty on this pair indicates unintended implementation differences.

## 6. Question targets and scoring

Every question declares exactly one target space:

```text
WORLD
EVER_EXPOSED
AVAILABLE
ATTITUDE
DISCLOSE
LINEAGE
JUSTIFICATION
```

### 6.1 Primary endpoint

Macro exact accuracy over the targeted perspective–lineage subset, averaged first within scenario and then across scenarios.

An answer is incorrect if it contains any:

- unauthorized disclosure;
- cross-instance contamination;
- cross-world contamination;
- false first-person attribution;
- receipt-to-belief collapse;
- restore-cutoff inheritance error.

### 6.2 Mandatory separate error rates

- unauthorized disclosure rate;
- cross-instance contamination rate;
- cross-world contamination rate;
- false first-person attribution rate;
- exposure-state reconstruction error;
- availability-state reconstruction error;
- attitude error;
- provenance/justification precision and recall;
- correct abstention rate.

No composite score may hide these rates.

### 6.3 Secondary control endpoint

B7 versus B6 on alternative-support and revocation cases. This tests path-sensitive justifications, not the main cognitive-lineage claim.

## 7. Fairness constraints

For every paired system comparison:

- identical scenario/event logs;
- identical query set and target labels;
- identical valid/system cutoffs;
- identical access to raw and structured evidence;
- identical evidence-token or record-count budget;
- identical answer renderer;
- no system receives an answer-defining field unavailable to its comparator;
- ablations are implemented by one isolated feature flag or a documented minimal code diff;
- per-template coverage and error matrices are emitted.

P0 may use deterministic symbolic answers, but the evaluator must not call the same helper that generated the gold answer unless the equivalence is explicitly being tested as a unit test.

## 8. Leakage and tautology audit

Before interpreting results, publish:

1. a primitive-by-template requirement matrix;
2. the fraction of questions whose gold answer changes when each primitive changes;
3. errors on templates outside the claimed primitive's causal scope;
4. answer-label balance by target and split;
5. checks that entity names, branch IDs, operation words, and query templates do not leak the answer;
6. a held-out topology/template family not used during implementation.

Clean 100% is classified as schema conformance only.

## 9. Statistical analysis

### 9.1 Resampling unit

The independent scenario is the unit of analysis.

### 9.2 P0 reporting

For P0, report:

- paired scenario-level differences;
- 10,000-sample scenario-cluster bootstrap intervals;
- between-seed variance;
- category results as exploratory;
- exact counts of discordant scenarios;
- all failed/excluded runs.

Question-level bootstrap or McNemar tests may appear only as supplementary diagnostics.

### 9.3 Confirmatory planning

After P0, freeze:

- the practical accuracy margin;
- safety non-inferiority margins;
- final scenario count;
- generator and split hashes;
- all thresholds and analysis code.

The initial engineering target is a B6–B5 gain of at least 3 percentage points, subject to revision from P0 variance before the confirmatory split is opened.

Safety constraints, because lower is better:

```text
B6 UKR  − B5 UKR  ≤ 0.5 percentage points
B6 CICR − B5 CICR ≤ 0.5 percentage points
```

where `CICR` is cross-instance contamination rate. Final margins are frozen after P0 and before confirmatory evaluation.

## 10. Correlated error extension

P0 first verifies clean symbolic semantics. A separate extension applies event/joint-hypothesis corruption modes:

```text
identity_collapse
fork_cutoff_shift
world_mind_branch_swap
exposure_source_swap
attitude_laundering
policy_declassification
restore_parent_error
about_world_scope_swap
source_family_collapse
```

Each mode mutates all dependent fields together.

Raw fallback is evaluated in four conditions:

1. same model/prompt family as structured extraction;
2. same model, different prompt;
3. independent model or deterministic lexical reconstruction;
4. idealized independent simulator as an explicitly labelled upper bound.

The idealized simulator's recovery probability is a design parameter, not empirical evidence. Report accuracy and leakage as a function of both corruption prevalence and fallback error correlation.

## 11. Falsification criteria

Reject or narrow the mechanism claim if any occurs:

1. B5 matches B6 within the frozen practical margin.
2. A simpler scoped-slot model matches B6 after metadata and evidence budgets are equalized.
3. B6 gains accuracy by increasing unauthorized disclosure or contamination.
4. B6 only wins on templates that directly encode its operation label and fails held-out topologies.
5. Exposure transitions add no value under natural extractor errors.
6. World and cognitive lineage separation is unnecessary once adversarial cases are removed.
7. The broader literature audit finds an existing system and benchmark testing the same mechanism under comparable conditions.
8. B7 does not outperform B6 on alternative-support cases, in which case `JustificationSet` is removed from the minimal implementation.

## 12. Reproducibility artifacts

Every run must commit or archive:

- code commit SHA;
- generator version and seed;
- frozen archetype and split IDs;
- per-scenario event log and gold states;
- per-question answer and error category;
- every system configuration;
- dependency lock;
- thresholds chosen on validation;
- start/end timestamps and hardware metadata;
- scenario-cluster analysis output;
- all exclusions and failures.

Large generated files may be stored as release artifacts, but compact manifests, hashes, schemas, aggregate tables, and a small reproducible sample remain in the repository.

## 13. Freeze checklist

This document remains `DRAFT` until both collaborating sessions explicitly accept:

- schema primitives and target-space definitions;
- baseline implementations;
- required contrastive pairs;
- primary endpoint and safety margins;
- generator/split hashes;
- analysis script hash;
- P0 and confirmatory roles;
- treatment of the earlier 25,000-query run as non-confirmatory.

Silence is not consensus. Any post-freeze substantive change requires a dated amendment before affected test results are inspected.