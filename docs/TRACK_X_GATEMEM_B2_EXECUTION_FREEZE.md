# Track X GateMem B2 — Protected Paired-Execution Freeze

**Status:** pre-dispatch execution contract; no B2 public outcome  
**Depends on:** PR #50 and PR #52 surface review  
**Issue:** #4

## 1. Dispatch gate

The public B2 matrix must not be dispatched until Session B explicitly reviews
and accepts or amends PR #52. Silence, green CI, and the synthetic surface audit
are not scientific approval.

Any method/parser/config change after the first protected B2 output creates a
new version and cannot replace the original result.

## 2. Exact paired methods

Each official domain job runs:

```text
B1a  raw_lexical
B1b  raw_lexical_reader
B2   raw_lexical_governed_reader
```

All use:

```text
top_k=5
BM25 k1=1.2
BM25 b=0.75
recency_weight=0.0
max_answer_characters=6000
```

B1b and B2 use the same frozen reader revision and reader budgets recorded in
PR #50. No GateMem-derived null-margin or parser tuning is allowed.

## 3. Shared protected opaque mapping

A fresh evaluator-owned binary key of at least 256 bits is generated inside
each protected domain job. The same key file is supplied to B1a, B1b, and B2
through:

```text
--opaque-id-secret-file /tmp/<protected-key>
```

The key file:

- is mode `0600`;
- is never printed;
- is never passed to the method process;
- is never copied into a result or artifact;
- is destroyed before upload;
- is represented publicly only by the existing one-way key and mapping
  commitments in run metadata.

This common mapping permits exact checkpoint-by-checkpoint comparison of opaque
candidate and prompt turn IDs without revealing source identifiers.

## 4. Pairing assertions

Before official result aggregation, the protected workflow requires:

1. identical checkpoint sets for B1a/B1b/B2;
2. exact equality of B1a/B1b retrieval-item lists;
3. exact equality of B1a/B2 retrieval-item lists, including ranks and scores;
4. exact B1a/B1b prompt hash and character equality;
5. every B2 prompt turn is a subset of its B1a top-k candidate turns;
6. B2 never retrieves a replacement after blocking;
7. B2 candidate count equals B1a top-k count;
8. B2 admitted plus blocked equals candidate count;
9. GateMem, scorer, reader, dependency, method-config, and surface-manifest pins
   match the frozen contract.

Any mismatch invalidates that domain run.

## 5. Protected evaluator-only analysis

After method execution, the evaluator may join predictions to hidden checkpoint
annotations only for scoring and aggregate stage analysis. Hidden fields remain
forbidden from the method.

Protected aggregate analysis may compute:

- B1a candidate required-evidence recall;
- B2 admitted-prompt required-evidence recall;
- false blocking where B1a contained required evidence and B2 removed it;
- privacy/deletion forbidden prompt exposure;
- reason-code and signal-coverage counts;
- utility, answer/context/end-to-end leakage, coverage, over-refusal, and cost.

No checkpoint text, query, principal, relationship, hidden label, pattern,
prediction, prompt, or source/opaque mapping is publishable.

## 6. Official and supplemental namespaces

The unmodified pinned GateMem scorer remains the official namespace. MindMap
stage/selective metrics are supplemental and must not replace or relabel
official metrics.

The publishable artifact contains only domain aggregates, immutable revision and
file hashes, method configurations, commitment hashes, pairing counts,
aggregate stage metrics, and reader costs.

## 7. Accepted interpretations

Possible outcomes include:

- **positive:** forbidden prompt exposure falls without unacceptable utility or
  permitted-evidence loss;
- **null:** public text contains too few identifiable policy signals to change
  the frontier;
- **negative:** the heuristic over-blocks, misses governance state, or is
  dominated by B1b/blanket refusal;
- **capability boundary:** relationship-aware native Policy-RAG outperforms the
  stricter public-text condition, demonstrating dependence on an authenticated
  policy capability rather than a generic memory-architecture effect.

None of these is automatically a MindMap, typed-ledger, leaderboard, or
production access-control result.