# Variable and metric registry

**Registry ID:** `MM-VR-001`  
**Version:** `0.1.0`  
**Rule:** an experiment manifest must either bind each applicable variable or
explain why it is not applicable.

## Independent variables

| ID | Variable | Examples | Manipulation rule |
|---|---|---|---|
| IV-01 | memory representation | generic event ledger, typed ledger | equal information unless information is the tested factor |
| IV-02 | retrieval method | no memory, BM25, vector, hybrid | same corpus and query |
| IV-03 | governance stage | none, post-reader, pre-reader | same candidates and reader |
| IV-04 | lifecycle mechanism | snapshot, restore, fork, merge, delete | event sequence frozen before evaluation |
| IV-05 | memory update method | append, replace, reconcile, abstain | update inputs fixed |
| IV-06 | evidence topology | single-hop, multi-hop, conflicting, stale | authored/frozen split |
| IV-07 | benchmark | GateMem, LongMemEval, HaluMem, MemoryAgentBench | official revision and license recorded |
| IV-08 | source revision | base/main, feature PR, remediation PR | exact revisions and executable-tree equality recorded |
| IV-09 | entity creation time relative to use | before, equal, after lineage/replication | all other event fields and query time fixed |
| IV-10 | deletion-speech family | information deletion, authorization revocation, physical removal, quoted, negated, hypothetical, update-not-delete | freeze cell and template cluster before parser output |
| IV-11 | target-expression form | explicit current turn, deictic prior context | same operation family and target inventory |

## Dependent variables

| ID | Metric | Unit / denominator | Direction |
|---|---|---|---|
| DV-01 | task accuracy | correct / eligible questions | higher |
| DV-02 | evidence/session recall | required evidence retrieved / required evidence | higher |
| DV-03 | abstention accuracy | correct abstentions / abstention-eligible questions | higher |
| DV-04 | update accuracy | correct latest-state answers / update questions | higher |
| DV-05 | hallucination rate | unsupported wrong outputs / evaluated outputs | lower |
| DV-06 | forbidden candidate exposure | forbidden candidates / privacy-deletion checkpoints | lower |
| DV-07 | forbidden prompt exposure | prompts containing forbidden evidence / checkpoints | lower |
| DV-08 | answer leakage | answers disclosing forbidden evidence / checkpoints | lower |
| DV-09 | end-to-end leakage | any forbidden exposure in pipeline / checkpoints | lower |
| DV-10 | false blocking | permitted evidence blocked / permitted evidence | lower |
| DV-11 | latency | wall-clock seconds, p50/p95 | lower |
| DV-12 | token cost | input/cached/output/reasoning tokens | lower at matched quality |
| DV-13 | monetary cost | USD per question and run | lower at matched quality |
| DV-14 | storage | bytes and memory items per user/session | lower at matched quality |
| DV-15 | audit completeness | decisions with reconstructable support / decisions | higher |
| DV-16 | deletion target grounding | exact gold memory-object ID or frozen target span matched / deletion-positive requests | higher |
| DV-17 | paired revision divergence | unequal answers / matched implementation-by-condition cells | lower when testing no-regression equivalence |
| DV-18 | typed operation accuracy | correct DELETE/RESTRICT/NONE outputs / items in each frozen speech-act cell | higher; report every cell |
| DV-19 | negative-operation abstention | correct NONE outputs / negative speech-act items in each cell | higher |
| DV-20 | independent annotation agreement | Cohen's kappa for nominal labels and exact target-ID/span agreement / positive rows | higher; before adjudication |

## Control variables

| ID | Variable | Required binding |
|---|---|---|
| CV-01 | source | git source head and dirty diff hash |
| CV-02 | actual checkout | checkout/synthetic merge revision plus tree comparison |
| CV-03 | dataset | repository, commit/revision, file SHA-256, split |
| CV-04 | sample | ordered question IDs or canonical hash |
| CV-05 | reader | provider/model/revision and prompt hash |
| CV-06 | judge | provider/model/revision, rubric hash, seeds |
| CV-07 | decoding | temperature, top-p, maximum output, thinking mode |
| CV-08 | retrieval budget | top-k, token/character cap, reranking budget |
| CV-09 | compute | OS, architecture, Python, dependencies, CPU/GPU |
| CV-10 | retry policy | retry count, backoff, timeout, failure handling |
| CV-11 | time | UTC execution window and provider status if relevant |
| CV-12 | cost ceiling | experiment and cumulative provider budget |

## Evaluator-only variables

The deployable method must not access these unless the experiment explicitly
tests privileged information:

```text
gold answer
answer-bearing session/turn labels
question category/type
privacy/deletion labels
official relationship graph
future turns
gold memory operations
record references
hidden source identifiers
judge decisions
test split outcomes
```

## Known nuisance variables and confounders

| ID | Threat | Required mitigation |
|---|---|---|
| NV-01 | mutable hosted-model alias | returned model/date and repeated sentinel cases |
| NV-02 | LLM judge variance/bias | frozen rubric, multiple seeds or audit sample |
| NV-03 | synthetic CI merge revision | record source and checkout separately; compare trees |
| NV-04 | question-specific prompt overrides | source audit and per-question prompt hash |
| NV-05 | development leakage | disjoint final split and outcome-access log |
| NV-06 | retries selecting favorable outputs | fixed retry/failure policy; retain all attempts |
| NV-07 | cache effects | record cached tokens and warm/cold condition |
| NV-08 | protected data unavailable to reviewers | aggregate artifact plus official scorer receipt/hash |
| NV-09 | percentage denominator drift | raw numerator/denominator in every table |
| NV-10 | parser overbreadth | adversarial non-memory negative controls |
| NV-11 | incomplete deletion | inspect store, retrieval, prompt, answer, backup, cache |
| NV-12 | cost-driven early stopping | preregister stopping rule and label truncation |
| NV-13 | parser undercoverage | freeze positive deletion-speech probes as well as physical-action negatives; report signal recall separately from benchmark score |
| NV-14 | future-reference time travel | reject references before entity creation or check entity creation time at every historical resolver |
| NV-15 | shared-validator common-mode confidence | count one semantic validator separately from constructor wiring and independently test accepted valid logs in each answer evaluator |
| NV-16 | exact-text or template-cluster overlap | hash prior material and split by frozen template cluster; invalidate collisions before outcome access |
| NV-17 | coder/adjudicator dependence | two blinded human manifests locked before comparison; preserve disagreement before separate adjudication |
