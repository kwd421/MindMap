# GateMem Official Endpoint Controls v0.1

**Status:** exploratory external endpoint controls; not a MindMap effectiveness result  
**Primary workflow:** `32219620639`  
**Repeat workflow:** `32220086173`  
**Primary MindMap head:** `8fd14b3e631a8faeae46f2e73273a94c11a129f4`  
**Pinned GateMem:** `603f9f4b4ba4b77f043c20f85687fa016fd720b0`  
**Official scorer SHA-256:** `3d546a21778202959a9df12bac44c196a7f20a248cf5a2cb34f0d9b9c2623d8a`

## Result boundary

These runs use GateMem’s unmodified deterministic official scorer with no LLM judge and no action gating. They establish two endpoints only:

- `always_no_memory`: zero-coverage, full-over-refusal safety edge;
- `raw_lexical`: policy-unaware BM25 raw-context echo, with no answer reader and no claim of capacity matching.

The method boundary uses per-run opaque episode, principal, turn, and query identifiers. Source identifiers, source `as_of_turn_id`, relationship-policy annotations, hidden checkpoint labels, `record_refs`, and `memory_ops` are evaluator-only. The official source checkpoint ID is restored after method return.

## Domain-level official metrics

| Domain | Endpoint | Utility accuracy | Privacy leakage | Deletion leakage | Over-refusal | Compliance utility |
|---|---|---:|---:|---:|---:|---:|
| Education | `always_no_memory` | 0.00% | 0.00% | 0.00% | 100.00% | 0.00% |
| Education | `raw_lexical` | 26.67% | 53.89% | 88.89% | 0.00% | 1.37% |
| Household | `always_no_memory` | 0.00% | 0.00% | 0.00% | 100.00% | 0.00% |
| Household | `raw_lexical` | 34.78% | 68.48% | 82.61% | 0.00% | 1.91% |
| Medical | `always_no_memory` | 0.00% | 0.00% | 0.00% | 100.00% | 0.00% |
| Medical | `raw_lexical` | 57.62% | 69.79% | 70.62% | 0.00% | 5.11% |
| Office | `always_no_memory` | 0.00% | 0.00% | 0.00% | 100.00% | 0.00% |
| Office | `raw_lexical` | 66.23% | 88.89% | 93.69% | 0.00% | 0.46% |

## Observations

1. `always_no_memory` has zero utility and 100% over-refusal in every domain, while producing zero privacy/deletion leakage.
2. Raw lexical context echo recovers utility, ranging from 26.67% in Education to 66.23% in Office, but privacy leakage ranges from 53.89% to 88.89% and deletion leakage from 70.62% to 93.69%.
3. The resulting compliance-utility score stays low in every domain: 0.46%–5.11%.
4. This is direct external evidence that unrestricted retrieval and blanket refusal are both poor endpoints for governed memory. It is not evidence that the full MindMap representation improves GateMem; a policy/availability/provenance method must still be run.
5. No cross-domain average, confidence interval, or hypothesis test is reported because domain aggregation and stochastic inference were not preregistered for these deterministic controls.

## Opaque-ID repeatability

The full 4-domain × 2-endpoint matrix was run again after committing the result files.

```text
official metric summaries equal:          8/8
opaque key commitments changed:           8/8
raw-lexical prediction hashes changed:    4/4
always-no-memory prediction hashes changed: 0/4
```

Raw-lexical prediction artifacts changed because evaluator-owned method audits contain newly randomized opaque turn identifiers. All eight official summaries remained byte-for-byte equivalent as parsed JSON. This demonstrates that the official endpoint metrics are invariant to the randomized opaque mapping in the repeated runs. Exact repeat artifact IDs and digests are recorded in `repeatability.json`.

## Reproducibility

- Eight matrix jobs completed successfully in primary workflow `32219620639` and again in repeat workflow `32220086173`.
- The official GateMem checkout, scorer, episodes, and checkpoints were pinned and hashed independently in every job.
- Only aggregate `publishable_summary.json` artifacts were retained from CI; raw benchmark text and prediction/audit bundles were not uploaded as public workflow artifacts.
- `results/gatemem_official_endpoints_v0_1/summary.json` records primary artifact IDs, digests, data hashes, prediction hashes, and opaque mapping commitments.
- `results/gatemem_official_endpoints_v0_1/repeatability.json` records the independent second-run comparisons.

## Next valid comparison

Add a shared answer reader and compare capacity-matched raw retrieval, policy/availability/provenance memory, G-flat, and T-normalized systems under the same raw input, retrieval budget, answer model, and official scorer. The endpoint results above must remain visible and cannot be relabelled as those systems.
