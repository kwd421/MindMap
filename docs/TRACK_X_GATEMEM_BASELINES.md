# Track X GateMem Baseline Agents

**Status:** pre-outcome method definitions  
**Benchmark result:** none  
**Execution boundary:** protected runner in PR #42

## 1. Purpose

Before evaluating a structured Neural-Cloud memory system, GateMem needs simple endpoints that expose the utility–governance frontier without hidden labels or gold record identifiers.

This module defines two deterministic extremes:

```text
RawLexicalGateMemAgent    high-coverage, policy-unaware raw retrieval
AlwaysNoMemoryGateMemAgent zero-coverage, zero-retrieval abstention
```

Neither is a competitive NCM implementation. They are controls.

---

## 2. Raw lexical baseline

The raw baseline stores only the public chronological turns received through the protected interface. It does not receive:

```text
query_type
attack_type
expected_action
judge rules
leak targets
gold records or record_refs
memory_ops
future turns
```

At query time it computes BM25 over turn text.

For query term `q` and turn `d`:

```text
IDF(q) = log(1 + (N - n(q) + 0.5) / (n(q) + 0.5))

BM25(d,q) = IDF(q) *
            tf(q,d) * (k1 + 1)
            / [tf(q,d) + k1 * (1 - b + b*|d|/avgdl)]
```

The total score is:

```text
score(d,q) = BM25(d,q) + lambda_recency * normalized_recency(d)
```

Frozen defaults are:

```text
top_k = 5
k1 = 1.2
b = 0.75
lambda_recency = 0
maximum answer characters = 6,000
```

Ties prefer later turns. This is deterministic and makes the zero-overlap fallback explicit.

The baseline always emits `action=answer` when at least one public turn exists. This is intentional: it measures how much utility and leakage arise when a memory system retrieves semantically relevant raw text without a governance layer. If the public journal is empty it emits `no_memory`.

It returns no GateMem `used_record_ids`, because those identifiers are hidden annotations in the raw-language condition. Instead it emits an auditable `memory_audit.items` list containing public turn IDs, speakers, text, ranks, and scores.

---

## 3. All-no-memory baseline

The abstention baseline always emits:

```text
action = no_memory
answer = empty
retrieved context = empty
```

This anchors the zero-coverage edge. It prevents a method from being described as “safe” merely because no explicit abstention control was shown.

It is not expected to maximize GateMem's official score, because utility questions require answers and over-refusal is measured.

---

## 4. Required reporting

For both controls report GateMem's official metrics unchanged:

```text
Utility U
Access-Control Violation A
Active-Forgetting Failure F
Over-Refusal OR
Memory Governance Score
answer/context/end-to-end leakage variants
```

Also report:

```text
checkpoint coverage
prompt-context character/token count
retrieved-turn count
query latency
memory bytes
method failures distinct from abstentions
```

Do not compare the raw baseline's internal turn IDs with GateMem gold record IDs as though they shared a namespace.

---

## 5. Interpretation

Expected qualitative endpoints are:

```text
Raw lexical:
  potentially useful
  high coverage
  likely privacy/deletion leakage
  no claim of calibrated or policy-aware behavior

Always no memory:
  zero retrieval exposure
  zero ordinary coverage
  maximal over-refusal
```

A structured NCM method is useful only if it occupies a better frontier position than both controls under the same public stream, model budget, retrieval budget, and scorer.

---

## 6. Next matched systems

The first comparative sequence should be:

```text
B0  AlwaysNoMemory
B1  RawLexical BM25
B2  Raw dense or matched BM25+dense retrieval
B3  G-flat extraction + capacity-matched lifecycle validation
B4  T-normalized extraction + typed lifecycle validation
B5  T+raw error-aware fallback
```

B3 and B4 must share the same event vocabulary, extractor/answer backbone, calls, tokens, retries, and validation information. B5 pays for every additional verifier or fallback call.

The central claim is rejected if B4 does not improve held-out calibrated safe coverage over B3 after those budgets are matched, or if B5 obtains safety only by collapsing governed coverage.
