# Falsification Result — Complete Relational Baseline

**Status:** fixed oracle-generator audit  
**Date:** 2026-08-17  
**Source pilot:** `MindMapBench-Entitlement-Pilot v0.1`  
**CI run:** `32011288073`

## Question

Does the reported 52.5 percentage-point advantage of `NCM-Psi` over `ScopedSlots` survive comparison with an information-complete relational baseline that receives the same structured event fields?

## Baseline

`CompleteRelationalRules` uses:

- observation/correction/supported-inference records for world state;
- one uniform `reliability × recency` rule for holder belief;
- explicit comparison of parent-branch states for unresolved merge;
- source-closure ACL and revocation checks for disclosure;
- no independent evidentiary credit for summaries.

It does not read `Query.factors` or gold answers and does not use NCM-Psi's modality-specific weight table.

## Exact result

| System | Primary | All queries | World | Belief | Disclosure | Historical | Unauthorized disclosure |
|---|---:|---:|---:|---:|---:|---:|---:|
| CompleteRelationalRules | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 0.00% |
| NCM-Psi | 99.33% | 99.50% | 100.00% | 98.00% | 100.00% | 100.00% | 0.00% |

The complete relational baseline solved all 800 fixed queries and corrected NCM-Psi's four residual belief errors.

## Decision

The original clean effect is falsified as an architecture-performance result.

> The +52.5-point NCM-Psi-versus-ScopedSlots gap shows that the fixed generator penalizes latest-row resolution when source type, source quality, provenance-policy closure, and merge semantics are omitted. It does not show that NCM-Psi outperforms an information-complete relational ledger.

The fixed pilot remains useful as a semantics regression suite. Its positive findings are that the generated task requires:

- separation of world, belief, disclosure, and historical targets;
- source-quality adjudication for its mistaken/deceptive cases;
- source-closure policy for its laundering cases;
- explicit merge conflict semantics.

## Mechanism-label audit

The original ablation labels are not one-factor mechanisms:

- `use_modality` also enables source reliability weighting, source-family deduplication, recency weighting, and parent-branch conflict logic;
- `use_lineage` enables both source-closure authorization and retraction propagation;
- `ScopedSlots` is deliberately denied the consequences needed to solve the generated labels.

## Statistical scope

The 200 scenarios are a deterministic greedy covering design. Exact counts are valid. A cluster bootstrap does not identify a population effect without a declared scenario-generating population, and question-level McNemar inference ignores within-scenario dependence.

## Remaining empirical questions

The architecture comparison moves to equal-information outcomes that representation normalization can affect operationally:

1. invalid-transition prevention and detection;
2. fault localization and repair;
3. deletion/revocation residue;
4. crash/replay consistency;
5. extraction calibration and held-out topology generalization;
6. ingestion/query/storage cost.

Raw-language and public-benchmark work must use a shared frozen extractor, reader, evidence budget, and target-conditioned scoring contract.
