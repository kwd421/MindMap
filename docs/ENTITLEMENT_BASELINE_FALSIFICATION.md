# Equal-Information Entitlement Baseline Falsification

**Status:** clear fixed-generator result  
**Date:** 2026-08-17  
**Source:** PR #32, GitHub Actions run `32011288073`

## Result

A compact `CompleteRelationalRules` baseline was added on top of the exact 200-scenario entitlement generator from PR #3. It receives the same structured events as `NCM-Psi` and does not inspect `Query.factors` or gold answers.

| System | Primary | All 800 | World | Belief | Disclosure | Historical | Unauthorized disclosure |
|---|---:|---:|---:|---:|---:|---:|---:|
| CompleteRelationalRules | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 0.00% |
| NCM-Psi | 99.33% | 99.50% | 100.00% | 98.00% | 100.00% | 100.00% | 0.00% |

The complete relational baseline uses observation/correction/supported-inference state, one uniform reliability×recency belief rule, parent-branch conflict comparison, source-closure authorization, and no independent credit for summaries. It corrects NCM-Psi's four residual errors.

## Decision

The reported +52.5-point NCM-Psi-versus-ScopedSlots gap is an incomplete-baseline discriminability result, not an architecture-performance result.

> Under equal structured information, the fixed generator is exactly solvable by a compact generic relational policy. It demonstrates that its labels require source-quality adjudication, provenance-policy closure, and merge semantics relative to latest-row resolution; it does not demonstrate NCM-Psi superiority over a complete ledger.

This is the empirical counterpart of the finite-query representation-equivalence proposition. Track S should expect complete systems to tie. Comparative research now belongs to lifecycle enforcement/fault behavior, raw-language extraction/generalization, or cost.

## Scope

This is an exact result on a fixed oracle-structured generator. It is not a population effect estimate, raw-language result, reader-model result, lifecycle-fault result, or public-benchmark result.
