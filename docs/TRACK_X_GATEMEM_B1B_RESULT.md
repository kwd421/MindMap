# Track X GateMem B1b — Official Paired Shared-Reader Result

**Status:** fixed deterministic external endpoint result; cross-session review required  
**PR:** #50  
**Producing head:** `1389a87fac9355e06e67ec85f7a4bf9c0a1a3ff6`  
**Frozen base:** `e6bef675c43e77ae0a922b8461aa3ac403a32dfd`  
**Workflow:** `33074043413`  
**GateMem:** `603f9f4b4ba4b77f043c20f85687fa016fd720b0`

## 1. Question

B1a is the policy-unaware raw BM25 context-echo endpoint. B1b keeps the exact
same B1a retrieval candidates and prompt text but sends that text to one frozen
public extractive reader.

The isolated question is:

> Does changing only answer use, after the raw context is already exposed,
> improve utility or end-to-end governance?

This is not a MindMap architecture comparison. It does not test a pre-reader
permission, deletion, provenance, or temporal gate.

## 2. Fixed reader

```text
model:        deepset/minilm-uncased-squad2
revision:     934656cdda79824eabf503ed56e15c01ddbdbe3f
runtime:      CPU inference
max length:   384 tokens
stride:       128 tokens
max answer:   30 tokens
null margin:  0.0, not calibrated on GateMem
packages:     torch 2.13.0+cpu
              transformers 5.15.0
              safetensors 0.8.0
```

The immutable model revision passed a public smoke question before protected
GateMem execution.

## 3. Paired retrieval proof

The protected workflow ran B1a and B1b in the same job for each of the four
official domains. Before scoring any reader difference, it compared the prompt
context SHA-256 and character count at every checkpoint.

```text
medical       579 / 579 equal
education     540 / 540 equal
household     552 / 552 equal
office        547 / 547 equal
--------------------------------
total        2218 / 2218 equal
hash mismatches:       0
character mismatches:  0
```

Thus B1a and B1b differ in reader/use only, not retrieval or prompt exposure.

## 4. Exact pooled counts

These are exact micro counts over the four domain files, not independent
replicates or a new pooled inferential test.

| Outcome | Denominator | B1a context echo | B1b shared reader |
|---|---:|---:|---:|
| Answers emitted | 2,218 | 2,218 | 824 |
| `no_memory` emitted | 2,218 | 0 | 1,394 |
| Utility answers correct | 728 | 335 | 41 |
| Privacy answer leaks | 727 | 509 | 45 |
| Privacy context leaks | 727 | 509 | 509 |
| Privacy end-to-end leaks | 727 | 509 | 509 |
| Deletion answer leaks | 763 | 646 | 96 |
| Deletion context leaks | 763 | 645 | 645 |
| Deletion end-to-end leaks | 763 | 646 | 645 |

Equivalent descriptive rates:

```text
answer coverage
  B1a: 100.00%
  B1b:  37.15%

utility accuracy on all utility checkpoints
  B1a: 46.02%
  B1b:  5.63%

privacy answer leakage
  B1a: 70.01%
  B1b:  6.19%

privacy context / end-to-end leakage
  B1a: 70.01% / 70.01%
  B1b: 70.01% / 70.01%

deletion answer leakage
  B1a: 84.67%
  B1b: 12.58%

deletion context / end-to-end leakage
  B1a: 84.53% / 84.67%
  B1b: 84.53% / 84.53%
```

Every domain and both methods had fixed-operating-point `safe_coverage = 0`
under the prespecified ordinary and governance risk limits.

## 5. Official per-domain result

### Medical

| Metric | B1a | B1b |
|---|---:|---:|
| Utility accuracy | 0.5762 | 0.1762 |
| Privacy answer leakage | 0.6979 | 0.1094 |
| Privacy context/e2e leakage | 0.6979 | 0.6979 |
| Deletion answer leakage | 0.7062 | 0.0847 |
| Deletion context/e2e leakage | 0.7062 | 0.7062 |
| Coverage | 1.0000 | 0.4301 |

### Education

| Metric | B1a | B1b |
|---|---:|---:|
| Utility accuracy | 0.2667 | 0.0056 |
| Privacy answer leakage | 0.5389 | 0.0278 |
| Privacy context/e2e leakage | 0.5389 | 0.5389 |
| Deletion answer leakage | 0.8889 | 0.1500 |
| Deletion context/e2e leakage | 0.8889 | 0.8889 |
| Coverage | 1.0000 | 0.3241 |

### Household

| Metric | B1a | B1b |
|---|---:|---:|
| Utility accuracy | 0.3478 | 0.0000 |
| Privacy answer leakage | 0.6848 | 0.0380 |
| Privacy context/e2e leakage | 0.6848 | 0.6848 |
| Deletion answer leakage | 0.8315 | 0.2391 |
| Deletion context leakage | 0.8261 | 0.8261 |
| Deletion end-to-end leakage | 0.8315 | 0.8261 |
| Coverage | 1.0000 | 0.3659 |

### Office

| Metric | B1a | B1b |
|---|---:|---:|
| Utility accuracy | 0.6623 | 0.0195 |
| Privacy answer leakage | 0.8889 | 0.0702 |
| Privacy context/e2e leakage | 0.8889 | 0.8889 |
| Deletion answer leakage | 0.9369 | 0.0450 |
| Deletion context/e2e leakage | 0.9369 | 0.9369 |
| Coverage | 1.0000 | 0.3620 |

## 6. Interpretation

B1b lowered final-answer leakage primarily because its native no-answer behavior
returned `no_memory` on 1,394 checkpoints. That is not a calibrated GateMem
selective policy. Utility correct answers simultaneously fell from 335 to 41.

More importantly, context exposure was fixed by design. The reader saw exactly
the same private and deleted raw text as B1a. Therefore answer-level suppression
could not reduce privacy end-to-end leakage below 509/727 or deletion
end-to-end leakage below 645/763.

The result supports a narrow causal conclusion:

> A reader placed after policy-unaware retrieval can suppress some final answer
> strings, but it cannot undo forbidden context exposure and, in this fixed
> configuration, it destroys most utility.

This negative result is retained. It does not imply that all extractive readers
or thresholds behave identically. The null margin was not calibrated on
GateMem, and no threshold sweep is accepted from this confirmatory run.

## 7. Cost

```text
reader calls:         2,218
forward calls:        2,218
windows:              2,218
input tokens:       428,127
summed reader time: 266.40 seconds across four parallel domain jobs
```

The summed time is not end-to-end serial benchmark latency. Domain jobs ran in
parallel and official runner/scorer overhead is separate.

## 8. Artifact provenance

| Domain | Artifact ID | ZIP SHA-256 |
|---|---:|---|
| Medical | 9647126296 | `0425e411f60230cc227885a143c55d899c8d94932d3f05556da3137f0ae75b38` |
| Education | 9647129082 | `c53350ddb3e8febe4310799862a34d677c1d70b5ad98d8d557c9b6b86af26b38` |
| Household | 9647137923 | `a48af0d09b6ea112d065d238ba10313a3121c86d123b2bbaa0e81baab3252768` |
| Office | 9647138038 | `5fd656dfb9eef9f5126d3d2c783e4330cc120df7fa522ce09aa873855e81d713` |

Each ZIP contains exactly one aggregate JSON. Independent inspection found no
checkpoint, episode, turn, principal, query-text, prompt-context, relationship,
`record_refs`, or `memory_ops` key. Protected predictions, prompt text, and
per-checkpoint scores were not uploaded.

The machine-readable compact result is:

```text
results/gatemem_b1b_v0_1/summary.json
```

## 9. Next deciding experiment

B2 keeps the same raw candidates and same frozen reader, but inserts a
pre-reader governance mechanism:

```text
B1b
raw BM25 candidates
-> raw context
-> frozen reader

B2
same raw BM25 candidates
-> permission / deletion / provenance gate
-> admitted context only
-> same frozen reader
```

B2 must report candidate recall, permitted prompt recall, forbidden prompt
exposure, utility, answer leakage, context leakage, reader cost, and
false-blocking. It is falsified if it cannot reduce prompt-level governance risk
at a useful matched-coverage point without relying on evaluator-only labels.
