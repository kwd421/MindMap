# Track X External-Benchmark Adapter Audit

**Status:** pre-outcome contract  
**Scope:** benchmark-boundary integrity, official-score preservation, and redistribution constraints  
**Result claim:** none

## 1. Why this document exists

Track X compares memory systems from the same raw evidence under matched model, token, retry, and retrieval budgets. External benchmarks are valuable only if their task semantics remain intact. A locally convenient conversion can otherwise leak scorer annotations, alter the official endpoint, or turn a benchmark into a new unvalidated dataset.

This audit therefore freezes four rules:

1. **The system never receives scorer-only annotations.**
2. **The official evaluator and official metrics remain the primary external result.**
3. **Track X diagnostics are supplemental and retain separate names.**
4. **Repository and dataset licenses are checked at pinned revisions before redistribution.**

The machine-readable pins and path rules live in `src/mindmap/track_x/benchmark_specs.py`. The recursive redaction, digest, and prediction-coverage checks live in `adapter_guard.py`.

---

## 2. Common adapter boundary

Each run must preserve four artifacts:

```text
source payload digest
removed-path manifest
model-visible payload digest
prediction-ID coverage report
```

The adapter must fail closed if:

```text
any declared hidden path remains
an expected item has no prediction
an unexpected item appears
an identifier is duplicated
an official evaluator version differs from the preregistered pin
```

Redaction occurs before prompt construction, indexing, extraction, or model calls. Removing hidden fields only after a prompt has been built is not an acceptable safeguard.

Path rules are explicit rather than recursive key-name searches. A field named `evidence` is model-visible in some tasks and judge-only in others; benchmark-specific location is therefore part of the contract.

---

## 3. Audited revisions

| Benchmark | Official repository | Audited revision | Integration mode |
|---|---|---|---|
| GateMem | `rzhub/GateMem` | `603f9f4b4ba4b77f043c20f85687fa016fd720b0` | official predictions + official scorer |
| HaluMem | `MemTensor/HaluMem` | `c29025f43b347f68fc36a06bee8ed29b4dc6c3fb` | local adapter + official evaluator |
| LoCoMo-Plus | `xjtuleeyf/Locomo-Plus` | `059f4e3d38f7f1f96765e8e2cb7de3097551bffb` | local adapter + official judge |
| LongMemEval-V2 | `xiaowu0162/LongMemEval-V2` | `2cc8c540bdb87fe6761629b585e727e1c4704520` | native `Memory` backend |

A later upstream commit is not silently adopted. Updating a pin requires a new audit diff and a recorded reason.

---

## 4. GateMem

### 4.1 Native task

GateMem evaluates incremental shared-memory use across multiple principals. Its official dimensions are:

```text
Utility U
Access-Control Violation A
Active-Forgetting Failure F
Over-Refusal OR
Memory Governance Score = U * (1 - A) * (1 - F)
```

The released scorer additionally distinguishes final-answer leakage, prompt-context exposure, and end-to-end leakage. This distinction is important for NCM: a final answer can be safe even though forbidden memory was retrieved into the answer model's context.

### 4.2 Model-visible input

The method may receive the chronological episode prefix, requester identity and role, policy/relationship context exposed by the official protocol, and query text.

It must not receive:

```text
query_type
attack_type
expected_action
judge_spec
leak_targets
```

These fields are scoring annotations. The Track X guard supports root checkpoint objects and wrapped checkpoint objects; adapters processing a whole list must apply the guard to each checkpoint before any model-facing merge.

### 4.3 Output

Preserve the official action space:

```text
answer
answer_redacted
refuse
no_memory
```

Preserve `checkpoint_id`, natural-language and structured answers, `used_record_ids`, and prompt-context audit material whenever retrieval-exposure scoring is claimed.

### 4.4 Reporting

GateMem's official metrics remain primary. Track X may additionally report:

```text
development-selected fixed-threshold coverage
ordinary risk
governance risk
governed coverage
retrieval-stage forbidden-evidence exposure
```

These do not replace MGS. Safe coverage must include a preregistered minimum governed coverage or a lexicographic governance endpoint; otherwise a system can look safe by refusing every governed request while answering ordinary requests.

### 4.5 Licensing boundary

The code repository carries an MIT license. The repository dataset card audited here does not itself state a dataset license. The pinned Hugging Face dataset revision and its terms must be rechecked before redistribution of data or derived annotations.

---

## 5. HaluMem

### 5.1 Native task

HaluMem separates memory-system hallucination into extraction, update, and question-answering stages. The official evaluator performs free-text/LLM-based comparisons for those native outputs and records timing information.

### 5.2 Model-visible input

Dialogue content, session chronology, persona information allowed by the official pipeline, and question text may be visible.

The following are gold/scorer layers and must be removed before ingestion or query:

```text
sessions[*].memory_points
sessions[*].questions[*].answer
sessions[*].questions[*].reference_answer
sessions[*].questions[*].evidence
```

### 5.3 Reporting

Run the official evaluator unchanged and report its extraction, update, and QA results under their official names. Track X event alignment may be run locally as a second diagnostic, but it is not the HaluMem extraction score and must not be substituted for it.

HaluMem is useful for locating the stage where a failure occurs. It does not by itself establish branch isolation, multi-principal access control, or deletion compliance.

### 5.4 Licensing boundary

The audited repository and dataset advertise CC BY-NC-ND 4.0 terms. The project therefore treats HaluMem as a local/native-evaluator input and does not publish transformed or derivative benchmark data without explicit permission or legal review.

---

## 6. LoCoMo-Plus

### 6.1 Native task

LoCoMo-Plus adds a Cognitive category to the original LoCoMo categories. A cue dialogue is inserted into an earlier session and a later trigger query tests whether the response uses the latent constraint despite weak direct lexical overlap.

### 6.2 Model-visible input

The stitched `input_prompt`, trigger query, category, and non-gold identifiers may be visible. The following fields are judge-only in the unified samples and must not enter the method:

```text
evidence
answer
ground_truth
```

### 6.3 Reporting

Preserve the official LLM-judge score and its category labels. The Cognitive judge asks whether the prediction is linked to the supplied evidence; it is not equivalent to evidence-retrieval recall, causal attribution, or calibrated safe coverage.

Track X may supplement the official score with evidence-access and evidence-use diagnostics. A response that merely paraphrases a cue can satisfy the native judge while failing a stronger action or constraint-consistency criterion, so the two results must remain separate.

### 6.4 Licensing boundary

No explicit `LICENSE` file was present in the audited tree, while the README refers readers back to repository license information. Until the maintainers and underlying LoCoMo terms are clarified, do not redistribute stitched contexts, transformed samples, or generated derivative datasets.

---

## 7. LongMemEval-V2

### 7.1 Native task

LongMemEval-V2 evaluates procedural and environment memory across large trajectory collections. The official integration surface is a native memory backend:

```text
Memory.insert(trajectory)
Memory.query(query, query_image=None) -> list[text/image context items]
```

The harness controls persistence/configuration, context-token budgets, answer evaluation, and query latency.

### 7.2 Integration rule

Implement NCM as a native `Memory` subclass. Do not transform evaluation questions into memory records, expose evaluator annotations, or exceed the official context budget. Preserve the official answer and latency metrics and any leaderboard frontier computation.

This benchmark is a later procedural/environment-memory track. It does not establish access-control or deletion-governance claims.

### 7.3 Licensing boundary

The audited code repository is Apache-2.0. Data preparation may combine multiple sources, so each downloaded source's terms must be checked before redistribution.

---

## 8. Official and supplemental score separation

Every result bundle must use namespaces similar to:

```text
official.gatemem.*
official.halumem.*
official.locomo_plus.*
official.longmemeval_v2.*
track_x.extraction_alignment.*
track_x.safe_coverage.*
track_x.cost.*
track_x.memory_audit.*
```

Never average official benchmark scores into a single unnamed “memory score.” A combined decision analysis may be performed later, but the source metrics, normalization, weighting, and benchmark scope must remain visible.

---

## 9. Evidence access and evidence use

The evaluation pipeline records two distinct stages:

```text
ACCESS: what memory entered the candidate set or answer context?
USE: what evidence was cited or causally used in the emitted answer/action?
```

This permits four outcomes:

| Access | Use | Interpretation |
|---|---|---|
| correct | correct | successful memory use |
| correct | incorrect | reasoning/attribution failure |
| forbidden | not disclosed | retrieval or prompt-exposure governance failure |
| forbidden | disclosed | end-to-end governance failure |

A benchmark that scores only the final answer cannot identify all four. Track X reports the additional stages only when the adapter can emit an auditable prompt-context/retrieval trace.

---

## 10. Acceptance checklist before the first model call

- [ ] Repository and data revisions are pinned by full SHA or immutable dataset revision.
- [ ] Licenses and redistribution boundaries are recorded.
- [ ] Hidden path rules have positive and negative unit tests.
- [ ] Source and model-visible payload digests are written.
- [ ] Removed paths are written without exposing removed values.
- [ ] Prediction identifiers have exact one-to-one coverage.
- [ ] Official evaluator runs on its native output format.
- [ ] Official and supplemental metrics use different namespaces.
- [ ] Model, prompt, schema, token, retry, retrieval, and cost budgets are frozen.
- [ ] Development threshold selection is separated from held-out evaluation.
- [ ] Governed coverage or an equivalent anti-evasion constraint is frozen.
- [ ] No unit-test fixture is presented as empirical benchmark evidence.
