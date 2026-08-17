# Preregistration Draft: MindMap / NCM-Ψ v0.2

**Status:** provisional preregistration for adversarial review; not yet frozen  
**Date:** 2026-08-17  
**Working study title:** *Policy- and Modality-Correct Reconstruction after Selective Cross-Lineage Memory Transfer*

## 1. Primary research question

Under equal raw evidence, extractor, reader, token budget, and index budget, does an explicit lineage–transfer–adoption–justification model improve reconstruction of world state, principal belief, first-person attribution, and requester-disclosable knowledge after selective memory transfer, revocation, or deletion?

## 2. Hypotheses

### H1 — primary quality hypothesis

Compared with the strongest simple composition—branch/principal filters, attributed transfer records, explicit belief adoption, and one flattened claim policy—the full model will improve **Lineage-Epistemic Reconstruction Accuracy (LERA)** by at least **5 absolute percentage points** on the held-out collision benchmark.

### H2 — safety/attribution hypothesis

The full model will reduce the combined rate of unauthorized disclosure and false first-person attribution by at least **50% relative**, without increasing over-withholding by more than 2 absolute points.

### H3 — non-branch control hypothesis

The full model will lose no more than **2 absolute points** on ordinary non-branch temporal/update controls relative to the strongest simple baseline.

### H4 — graph hypothesis

Routed graph expansion will not improve aggregate LERA unless it yields a preregistered benefit on multi-hop provenance questions. If a typed relational implementation matches it within the equivalence margin while being cheaper, graph traversal will be excluded from the minimal architecture.

## 3. Target state spaces

Every question is labelled as exactly one target:

1. `WORLD`: objective branch-local world state.
2. `SOURCE_BELIEF`: source principal's belief or stance.
3. `DESTINATION_BELIEF`: receiving principal's adopted stance.
4. `REMEMBER_1P`: whether the destination may claim first-person memory.
5. `DISCLOSE`: what the requester may receive under the active policy.
6. `PROVENANCE`: an admissible active justification or required abstention.

The confirmatory primary metric uses the first five target spaces. Provenance exactness is a mandatory secondary metric because several alternative support paths may be valid.

## 4. Study tracks

### Track A — oracle component study

Inputs are gold structured events and queries. Purpose: test whether the semantics distinguish the intended cases. Results are explicitly labelled **oracle/component ceilings**.

### Track B — end-to-end natural-language study

Inputs are only raw dialogues/events and raw questions. The system must infer:

- event boundaries;
- entities and principal identities;
- target state space;
- relation and negation/modality;
- valid time and source assertion event;
- branch and lineage type;
- witnesses/audience;
- transfer kind and belief adoption;
- policy lifecycle;
- support/derivation links.

No answer-defining canonical entities, gold question type, `current`, `trust`, branch eligibility, or policy decision may be exposed at inference.

## 5. Scenario design

### 5.1 Core factors

- **Lineage:** identity fork / operational replica / restore.
- **Transfer:** no transfer / attributed report / evidence copy / state replication request.
- **Adoption:** accepted / doubted / rejected / quarantined.
- **Policy lifecycle:** public / private→shared / shared→revoked / source deleted.
- **Support topology:** protected-only / independent public support / duplicated same-source support.
- **Query target:** world / source belief / destination belief / first-person / disclosure / provenance.

A covering array will cover all pairwise factor interactions. Hand-written adversarial scenarios will cover higher-order interactions:

- attempted state replication into an identity fork;
- receipt followed by explicit rejection;
- secret-only derivation followed by revocation;
- secret and genuinely independent public support paths;
- copied summary that launders hearsay;
- restored runtime with an explicit recovery gap;
- sealed existence versus sealed content;
- same-principal replica merge versus new-principal coexistence.

### 5.2 Natural-language rendering

Each hidden event log will be rendered through multiple templates and paraphrase models. Split boundaries are by hidden scenario template, event ordering family, and entity vocabulary—not by individual questions. Near-duplicate renderings of one hidden world may not cross splits.

### 5.3 Controls

At least 20% of the final questions are ordinary temporal/update controls with no fork, transfer, or restricted evidence. This prevents a system from appearing safer merely by refusing to answer.

## 6. Baselines

1. Full transcript truncated to the same evidence-token budget.
2. Raw BM25+dense reciprocal-rank fusion.
3. RRF + branch/principal/current-policy filters.
4. Filters + attributed transfer records.
5. Filters + transfer + explicit adoption/modality.
6. Model 5 + lineage-aware first-person rules, but flattened claim policy.
7. Model 5 + alternative support sets, but no lineage-aware replication rule.
8. **NCM-Ψ v0.2:** lineage + transfer/adoption + alternative justification sets + policy lifecycle.
9. NCM-Ψ + routed graph expansion, tested as a secondary ablation.
10. Reproducible external systems where one frozen harness can supply equal evidence, reader, and budgets.

The critical falsifier is baseline 5, 6, or 7 matching baseline 8.

## 7. Primary endpoint

### 7.1 Lineage-Epistemic Reconstruction Accuracy (LERA)

For each query, the reader must produce a structured answer tuple:

```text
(answer,
 target_state_space,
 holder,
 epistemic_modality,
 first_person_status,
 disclosure_decision)
```

LERA is macro exact accuracy across scenario families and target state spaces. Unauthorized disclosure, false first-person attribution, or wrong-branch answers are incorrect even when the proposition is globally true.

### 7.2 Evidence budget

Primary comparison uses a fixed maximum of **2,000 retrieved evidence tokens per query** and the same frozen answer model/prompt. Systems that need fewer tokens retain that efficiency advantage; unused tokens are not backfilled with unrelated evidence.

## 8. Mandatory secondary metrics

- unauthorized disclosure rate;
- false first-person attribution rate;
- cross-lineage contamination rate;
- revocation/deletion residue rate;
- over-withholding rate;
- belief-adoption error rate;
- provenance precision and complete evidence recall;
- correct abstention and selective risk–coverage;
- Brier score and expected calibration error;
- p50/p95 ingestion and query latency;
- tokens/query, bytes/event, write amplification, and monetary inference cost.

No single composite “memory score” will hide these error classes.

## 9. Correlated extraction errors

Independent field dropout is prohibited as the only robustness test. Each event receives a latent corruption mode:

```text
clean
wrong_entity_or_principal_link
wrong_event_boundary
temporal_scope_shift
speaker_or_witness_swap
branch_or_lineage_misattribution
modality_or_negation_laundering
visibility_misclassification
transfer_or_adoption_confusion
source_family_duplication
```

One mode jointly mutates dependent fields and downstream derivations. Two robustness tracks are reported:

1. deterministic interventions for causal attribution;
2. naturally produced errors from one frozen extractor, manually labelled at the joint event-hypothesis level.

A verifier outputs a distribution over joint extraction hypotheses. Field confidences may be reported diagnostically but are not multiplied as if independent.

## 10. Raw-evidence fallback

Structured-only, raw-only, and dual-path systems are compared. The fallback threshold is selected on validation data only.

Two fallback conditions are required:

- the fallback reader is independent from the extractor;
- the fallback reader reuses the extractor model.

The gap estimates the cost of correlated model failure. Accuracy, safety errors, fallback rate, and latency are reported as a frontier.

## 11. Sample size and splits

The final confirmatory set will contain at least **800 independent hidden scenarios**, based on detecting an approximately 5-point paired difference under a conservative discordant-pair rate near 0.25 with 80% power and two-sided 5% error. Each scenario produces several target-space questions, but statistical resampling clusters by scenario.

Provisional split:

- train/development: 400 scenarios;
- calibration/validation: 200 scenarios;
- confirmatory test: 800 scenarios.

The exact size will be recomputed from end-to-end pilot variance before freezing the test manifest.

## 12. Statistical analysis

- Primary: paired difference in scenario-level LERA with a scenario-clustered bootstrap 95% confidence interval.
- Secondary paired binary comparison: McNemar exact test.
- Error-class comparisons: clustered bootstrap intervals and rate ratios.
- Calibration: Brier, ECE, and risk–coverage curves.
- Secondary endpoint multiplicity: Holm correction within each metric family.
- Random seed, prompts, model revisions, package versions, and per-query outputs are recorded in an immutable run manifest.

The primary claim is accepted only when the preregistered direction holds and the confidence interval excludes zero. A practically smaller gain is reported as a failed effect-size target even if nominally significant.

## 13. Acceptance and rejection rules

The architecture claim is narrowed or rejected when any of the following occurs:

1. Baseline 5, 6, or 7 is statistically equivalent to full v0.2 within the predefined equivalence margin.
2. Improvement is below 5 points or safety error reduction is below 50% relative.
3. Ordinary temporal controls lose more than 2 points.
4. Raw fallback adds enough distraction/cost to erase its robustness benefit.
5. A simple typed relational index matches graph expansion on the preregistered multi-hop subset.
6. External temporal/provenance systems match or exceed v0.2 in the frozen harness.
7. Natural-language extraction errors eliminate the oracle component advantage.

## 14. Completed exploratory collision audit

A 48-scenario, 192-decision symbolic unit test was run before this preregistration. It crossed six lineage/transfer/adoption cases, four policy lifecycles, and two support topologies.

| System | Decision accuracy | All-four-correct scenarios |
|---|---:|---:|
| NCM-Ψ v0.2 | 100.00% | 100.00% |
| Alternative support, no lineage | 93.75% | 83.33% |
| Lineage, no alternative support | 87.50% | 75.00% |
| Transfer + adoption | 81.25% | 62.50% |
| Attributed transfer | 72.92% | 37.50% |
| Branch/principal/ACL only | 39.58% | 0.00% |

Against the strongest ablation, the full rule set improved decision accuracy by 6.25 points; scenario-clustered bootstrap interval approximately 2.60–10.42 points; paired exact p=0.000488.

**Interpretation restriction:** the full model directly implements the hidden-world rules, so this is a discriminability/unit test, not an estimate of real-world LLM performance or publication-ready confirmatory evidence.

## 15. Freeze checklist

Before the confirmatory run, commit and hash:

- schema and task definitions;
- generator and rendering code;
- split manifest;
- scoring code;
- prompts and model versions;
- token/call budgets;
- extraction-error interventions;
- fallback threshold selection procedure;
- primary and secondary analyses;
- exclusion and failure handling rules.
