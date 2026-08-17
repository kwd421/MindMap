# MindMap / NCM-Ψ v0.2 Research Protocol

**Status:** Track S completed; Track E/X freeze candidate  
**Revision:** 1  
**Date:** 2026-08-17  
**Coordination:** Issues #6, #7, and #8

## 1. Claim pivot

This protocol supersedes proposals to show that a typed v0.2 ledger has higher clean-oracle question-answering accuracy than a complete equal-information generic event ledger.

For a finite event history and finite query set, a generic bitemporal event relation carrying the same operations, identifiers, cutoffs, policies, and support links can be evaluated by an equivalent relational program. Therefore:

- complete equal-information implementations should agree on clean semantics;
- withholding answer-defining operations from the generic implementation would make a typed-schema advantage tautological;
- schema typing is not justified by representational expressiveness or clean oracle QA superiority.

The research program has three tracks:

- **S — Semantic conformance:** independent declarative gold; complete generic and typed implementations must agree.
- **E — Lifecycle enforcement and fault handling:** matched operational faults; compare silent invariant violations, detection, localization, repair, residue, safety, and cost.
- **X — Extraction and topology generalization:** held-out raw-language topology families; compare calibrated extraction, abstention, downstream reconstruction, safety, and cost.

Cost and implementation complexity are reported across E and X.

## 2. Scope and non-claims

### In scope

- mind instances distinct from principals and runtimes;
- world branches distinct from cognitive lineages;
- valid time distinct from system time;
- explicit snapshot manifests;
- normative parent/child branch visibility;
- source assertions and about-world scope;
- exposure, current availability, attitude, memory attribution, world truth, and disclosure as separate states;
- copy, restore, selective transfer, adoption/rejection, seal/forget/reacquire, revoke/delete, and alternative support paths;
- independent semantic fixtures;
- matched lifecycle fault injection;
- held-out natural-language topology evaluation;
- auditability and cost.

### Out of scope

- general semantic merge of independently acting identities;
- philosophical personal-identity scoring;
- unrestricted defeasible reasoning;
- always-on graph traversal as a default;
- independently writable memory-layer hierarchies;
- public-benchmark SOTA claims;
- novelty claims for bitemporal storage, provenance, information-flow control, epistemic logic, event sourcing, or provenance witnesses;
- a claim that typed storage is more expressive than an equal-information generic ledger.

## 3. Canonical target spaces

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

Every question declares exactly one target and uses a target-specific answer schema. Irrelevant fields are excluded rather than silently scored.

## 4. Common append-only event contract

Every complete oracle implementation receives a byte-equivalent event history containing the same information:

```text
CommonEvent(
  event_id,
  event_type,
  valid interval,
  system time,
  actor principal/mind instance,
  source/destination mind instance,
  source/destination placement,
  object kind/id,
  proposition id,
  about-world branch,
  lineage kind and snapshot reference,
  snapshot-manifest membership attributes,
  transfer/exposure operation,
  attitude transition,
  attribution kind,
  authorization id/operation,
  policy operation/label,
  source-family id,
  justification members and sufficiency threshold,
  raw-evidence reference
)
```

No implementation receives a hidden final field such as:

```text
correct_answer
current
eligible
first_person = true
final disclosure decision
```

Gold semantics do not import generic or typed resolver code. Generic and typed implementations do not import gold transition helpers. Mutation tests must demonstrate separation.

## 5. Implementations

### G — complete generic event ledger

A complete generic bitemporal event relation using ordinary normalized tables or event rows, recursive traversal, explicit resolver rules, and the full common event history.

G may reconstruct every canonical target. It is not intentionally weakened.

### T — typed v0.2 ledger

The representation in `SCHEMA_V0_2.md`, including typed projections for:

```text
Principal / MindInstance / Runtime
WorldBranch / MindPlacement
LineageEdge
Snapshot / SnapshotManifestEntry
EvidenceEvent / SourceAssertion
ClaimRevision
ExposureTransition
PolicyEvent
MemoryAttribution
JustificationSet / JustificationMember
```

T receives no event unavailable to G.

### Diagnostic baselines

Scoped slots, principal-only holders, receipt-as-belief, claim-level policy flattening, or lineage-free stores may be used to expose causal failure classes. They are not the decisive equal-information comparison.

### Optional graph control

Graph traversal is evaluated only for preregistered multi-hop provenance questions. It is removed from the minimal architecture if relational traversal matches it within the frozen equivalence margin at lower cost.

## 6. Track S — semantic conformance

### 6.1 Objective

Verify that independent declarative gold, complete generic G, and typed T agree on clean finite event histories. A complete implementation disagreement is a bug or underspecified semantics, not evidence of superiority.

### 6.2 Frozen fixture families

The fixed suite contains fourteen families:

```text
F01 branch visibility and late pre-fork import
F02 mind copy without world fork
F03 world fork without mind copy
F04 unsynchronized same-principal replicas
F05 identity-fork evidence-copy attribution
F06 receipt, rejection, and adoption
F07 seal/unseal/forget/reacquire lifecycle
F08 explicit snapshot manifest and recovery gap
F09 cross-world reference versus holding context
F10 protected-only support and revocation
F11 independent public support surviving protected-path revocation
F12 same-origin deduplication
F13 authorized state replication and authorization revocation
F14 ordinary temporal negative controls
```

The suite covers every canonical target space. Fixed-suite reporting uses exact counts only; no confidence interval or p-value is attached.

### 6.3 Exit criterion

```text
independent gold = G = T = declared expected value
```

for every fixed case, with mutation tests detecting at least:

- silent about-world rescoping;
- authorization-revocation failure;
- receipt-as-belief collapse;
- snapshot-cutoff-without-membership inheritance.

### 6.4 Completed result

Track S was executed in GitHub Actions run `32014966255` on Python 3.11.15.

```text
fixtures:                  14
cases:                     75
gold correct:              75 / 75
generic correct:           75 / 75
typed correct:             75 / 75
all three agree:           75 / 75
disagreements:             0
failures:                  0
pytest:                    16 passed
```

Target coverage:

```text
WORLD              12
EVER_EXPOSED       14
AVAILABLE          11
ATTITUDE           12
ATTRIBUTION        10
DISCLOSE            8
JUSTIFICATION       8
```

Committed outputs:

- `results/s_track_conformance_rows.csv`
- `results/s_track_conformance_summary.json`

The workflow also publishes artifact `9283150208`. This is a deterministic semantic-conformance result, not comparative architecture evidence.

## 7. Track E — lifecycle enforcement and fault handling

### 7.1 Primary research question

Under identical source events and semantically matched faults, does typed T reduce silent semantic/safety failures or improve detection, localization, containment, repair, and residue relative to generic G?

A T advantage, if any, must arise from explicit constraints, typed projections, and diagnostics—not additional information.

### 7.2 Fault specification

Fault schedules are generated and frozen independently of outcomes. Each semantic fault has a documented injection mapping for G and T.

#### Journal/input faults

- missing event;
- duplicate event;
- reordered or late event;
- malformed or mismatched identifier;
- corrupted valid/system interval;
- corrupted source-family or support member;
- corrupted lineage, placement, snapshot-manifest, or authorization link.

#### Transaction and replay faults

- crash after journal append but before projection update;
- crash after one of several dependent writes;
- duplicate replay;
- out-of-order replay;
- stale checkpoint or snapshot manifest;
- partial restore;
- concurrent transfer and policy-change race.

#### Projection/cache/index faults

- stale availability projection;
- stale attribution projection;
- stale attitude or world projection;
- stale derived claim after revoke/delete;
- stale vector/graph index after deletion;
- missing descendant invalidation;
- cache rebuilt from the wrong system-time cutoff.

#### Authorization/policy faults

- absent authorization for state replication;
- revoked authorization reused;
- declassification without an auditable event;
- protected ancestor omitted from a support path;
- independent public support incorrectly over-tainted;
- deletion contract applied to the wrong descendants.

### 7.3 Matched-fault fairness

Report separately:

- implementation-neutral journal faults;
- physical-layout/projection faults;
- faults prevented at write time;
- faults detected only at replay/read time;
- faults not detected before a target answer or downstream action.

G and T receive no fault label at inference.

### 7.4 Primary E endpoints

- silent invariant-violation rate;
- unauthorized-disclosure rate;
- false first-person-attribution rate;
- cross-instance contamination rate;
- cross-world contamination rate;
- fault-detection precision and recall;
- events/operations to detection;
- localization accuracy and candidate-set size;
- repair success rate;
- repair blast radius;
- deletion/revocation residue rate;
- post-repair semantic conformance;
- abstention or containment quality during uncertainty.

### 7.5 E cost endpoints

- write amplification;
- projection/index rebuild time;
- p50/p95 ingest and query latency;
- storage bytes/event;
- recovery time and replay count;
- schema objects, constraints, resolver branches, and migration surface;
- operator-visible diagnostics produced per fault.

### 7.6 E hypotheses

Before confirmatory outcomes are opened, freeze independent practical/equivalence margins for:

- silent invariant violation;
- each safety error separately;
- localization candidate-set size;
- repair blast radius;
- cost.

A G/T tie or G advantage is retained and narrows or rejects the typed-enforcement contribution.

## 8. Track X — extraction and topology generalization

### 8.1 Primary research question

Given raw dialogue/documents and held-out topology families, do typed extraction constraints and projections improve calibrated event reconstruction, abstention, and downstream target correctness under equal model and budget conditions?

### 8.2 Conditions

#### X-A — frozen extractor, different validation/projection

One frozen extractor produces joint event hypotheses and confidence masses. G and T receive identical hypotheses. This isolates validation, projection, and abstention.

#### X-B — equal-budget end-to-end extraction

G and T may use representation-specific prompts or constrained outputs, but receive equal:

- model family and revision;
- training/development examples;
- raw evidence;
- token, call, retry, and wall-clock budget;
- reader model and evidence budget.

Any representation-specific extra call or token is counted.

#### X-C — reference ceilings

Report separately:

- raw retrieval/reader baseline;
- oracle structured-event ceiling;
- structured-only memory;
- dual structured/raw fallback.

### 8.3 Held-out topology discipline

Splits are grouped by:

- cognitive-lineage topology;
- world-branch topology;
- transfer/adoption pattern;
- policy lifecycle;
- support topology;
- temporal-expression family;
- entity vocabulary and rendering family.

Entire topology families are held out. A value substitution, paraphrase, or reordered version of a held-out topology may not appear in development. At least one test partition composes mechanisms whose exact joint topology was absent from development.

### 8.4 Correlated extraction modes

Evaluate event/joint-hypothesis errors rather than independent field dropout:

```text
identity collapse
fork-cutoff shift
world/mind-branch swap
about-world-scope swap
exposure source/destination swap
attitude laundering
attribution laundering
policy declassification
restore-parent or snapshot-membership error
source-family collapse
assertion/event-time collapse
```

### 8.5 X endpoints

- event-boundary accuracy;
- principal/mind-instance/entity linking;
- valid/system-time accuracy;
- lineage, placement, snapshot, transfer, adoption, attribution, policy, and support-link accuracy;
- joint-hypothesis log loss, Brier score, and ECE;
- target-space routing accuracy;
- downstream exact accuracy by target;
- unauthorized disclosure and over-withholding;
- false first-person attribution and under-attribution;
- cross-instance and cross-world contamination;
- correct abstention and risk-coverage;
- evidence recall and evidence-use accuracy;
- latency, calls, tokens, and monetary cost.

### 8.6 Raw fallback

Compare:

1. same model and prompt family as extraction;
2. same model, different prompt;
3. independent model or deterministic reconstruction;
4. idealized independent simulator, labelled only as an upper bound.

Report extractor/fallback error correlation, false-trigger harm, repair accuracy, evidence distraction, leakage, and cost.

## 9. Development and confirmatory organization

### Development suite

Target:

```text
48 topology/archetype clusters
x 5 independently seeded surface/entity/value realizations
= 240 instantiated scenarios
```

The 240 instances are not treated as 240 independent generalization units. Report within-archetype and between-archetype variation separately.

### Confirmatory E/X suites

Before outcomes are opened, hash and freeze:

- topology/archetype manifests;
- fault schedules and implementation mappings;
- raw renderings;
- target-family weights;
- practical/equivalence and safety margins justified independently of observed development effects;
- sample-size rationale based on archetype-level or hierarchical variance;
- analysis code and seeds;
- failure/exclusion policy.

## 10. Statistical analysis

### Fixed S suite

Exact counts only.

### E/X development

Report:

- paired scenario differences;
- topology/archetype-cluster bootstrap diagnostics;
- within-archetype seed variation;
- between-archetype variation;
- hierarchical or mixed-effects estimates where identifiable;
- exact discordant archetype/scenario counts;
- all failures and exclusions.

Question-level tests are supplementary only.

### Confirmatory E/X

Use the prespecified topology/archetype-level or hierarchical analysis. Safety endpoints are reported separately; unauthorized disclosure and false first-person attribution are not merged into one score.

## 11. Falsification and narrowing

Narrow or reject the project claim if any occurs:

1. complete G and T disagree on clean Track S semantics after specification reconciliation;
2. T enforcement benefits disappear under matched information and fault schedules;
3. G matches or exceeds T in silent-failure prevention, localization, repair, safety, and cost;
4. apparent T gains come from target-encoding fields or additional model budget;
5. X gains disappear on held-out topology families;
6. correctness improves by increasing unauthorized disclosure or attribution errors;
7. alternative support sets add no measurable safety/audit value;
8. graph traversal adds no held-out multi-hop benefit at acceptable cost;
9. raw fallback adds distraction/cost without robust correlated-error repair;
10. an external system matches the same mechanism in the frozen harness.

Negative results are retained. They may show that generic event sourcing plus ordinary constraints is sufficient.

## 12. Reproducibility

Every run commits or release-hashes:

- common event schema and serialized events;
- independent declarative gold implementation;
- G/T projections, constraints, and resolvers;
- fault specifications and implementation mappings;
- topology/archetype and split manifests;
- renderer/extractor versions, prompts, models, and seeds;
- per-event, per-question, per-scenario, and per-archetype outputs;
- target-conditioned scoring;
- field-information audit;
- dependency lock;
- hardware and timestamps;
- exact statistical configuration;
- exclusions and failures.

CI regenerates compact result files and fails on drift.

## 13. Classification of earlier results

### Original 25,000-query report

Permitted label:

> unverified structured-oracle resolver/scaffold smoke test until its implementation and outputs are committed.

It does not power S, E, or X.

### Fixed 48-case collision script

Permitted label:

> deterministic truth-table discriminability/conformance smoke test.

Its basic aggregate fields are reproducible. The fixed Cartesian suite receives exact counts, not inferential statistics, and does not establish schema sufficiency or natural-language robustness.

## 14. Remaining freeze checklist

- [x] canonical schema revision with explicit snapshot membership and branch visibility
- [x] independent declarative gold semantics
- [x] complete equal-information G and T
- [x] Track S exact equality on 75 cases
- [x] committed Track S per-case and summary outputs
- [ ] explicit cross-session acceptance of schema revision 1
- [ ] Track E fault taxonomy and mappings implemented
- [ ] Track E practical/equivalence margins frozen
- [ ] Track X topology manifests and raw renderers implemented
- [ ] Track X model/budget conditions frozen
- [ ] explicit cross-session approval before confirmatory E/X outcomes are opened

Silence is not consensus. Any post-freeze substantive change requires a dated amendment before affected confirmatory outcomes are inspected.
