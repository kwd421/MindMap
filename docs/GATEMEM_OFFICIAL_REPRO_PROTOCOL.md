# GateMem Official Public-Benchmark Reproducibility Gate

**Status:** pre-result execution gate  
**Coordination:** Issue #4  
**Upstream:** `rzhub/GateMem`  
**Local prior work:** PRs #40–#43

## 1. Purpose

GateMem is the first external benchmark used for the MindMap governance subset because its official toolkit measures three deployment-relevant quantities:

- utility for authorized requests;
- access-control violations;
- active-forgetting failures after deletion.

This gate prevents a local smoke test, a synthetic fixture, or a capability-reduced adapter test from being reported as an official public-benchmark result.

## 2. Source-of-truth hierarchy

The execution must preserve and identify:

1. an exact upstream GateMem Git commit;
2. the official public data tree from that commit;
3. the official prediction/evaluation contract from that commit;
4. the exact MindMap method commit;
5. the exact model, prompt, retrieval, and cost configuration when model calls are used.

The upstream repository and its own evaluator take precedence over copied metric code. Additional MindMap diagnostics are supplementary and must not replace official category metrics.

## 3. Staged execution

### R0 — source and boundary audit

No API keys or model calls.

- resolve and record the upstream `main` commit;
- clone and hash the official repository/data tree;
- verify the official README/toolkit identifies the four domains and the advertised episode/checkpoint scale;
- fetch PR #43's exact head commit;
- install and test the protected runner/BM25/always-abstain code;
- inventory executable GateMem entry points and candidate commands;
- scan method-facing code for forbidden evaluator-only field dependencies;
- publish a machine-readable artifact and Issue #4 checkpoint.

R0 is not a benchmark score.

### R1 — no-API public baseline

- run the always-abstain and raw-BM25 methods on the actual official public data;
- generate one prediction row per official checkpoint;
- verify IDs, row count, duplicates, and missing checkpoints against the official loader;
- run every deterministic official metric available without a model judge;
- preserve official per-domain/per-category counts;
- report our safe-coverage diagnostics separately;
- report CPU/runtime, bytes indexed, and retrieval operations.

### R2 — fixed-model evaluation

Only after R1 passes.

Freeze:

- model provider and immutable revision where available;
- system/user prompts;
- temperature/decoding;
- maximum calls, retries, input/output tokens;
- retrieval and answer-context budgets;
- judge model and prompt if the official protocol requires a judge;
- dated monetary prices.

Run capacity-matched systems on identical checkpoint order and raw inputs.

## 4. Method boundary

The memory method must not receive evaluator-only information, including hidden labels, future turns, gold records, answer labels, deletion targets unavailable at that point, or official scoring annotations.

The protected incremental runner must expose only the information causally available at each checkpoint. Any capability reduction relative to the official public task is documented as a separate condition rather than silently replacing the benchmark.

## 5. Required baselines

Minimum first run:

```text
A0 always abstain
A1 raw BM25
A2 official long-context or official raw baseline, when its required model is fixed
G  complete generic event representation
T  normalized MindMap representation
T+raw normalized representation plus preregistered raw fallback
```

A0 and A1 are pipeline/safety references, not competitive memory systems.

## 6. Reporting

Always report:

- exact upstream and method commits;
- official domains, episodes, and checkpoints actually loaded;
- missing/duplicate prediction counts;
- official utility, access-control, active-forgetting, and summary metric where available;
- numerator and denominator for every violation rate;
- answered/abstained counts and safe coverage;
- per-domain and per-category results;
- all failures, retries, and exclusions;
- runtime, tokens/calls, and dated cost;
- whether an LLM judge was used.

Do not merge utility and governance into an unlabelled custom score. Do not interpret all-checkpoint abstention as safety success without its zero utility/coverage cost.

## 7. MindMap claim boundary

GateMem can test the governance subset:

```text
principal/requester scope
AVAILABLE versus historical exposure
revoke/delete/seal lifecycle
DISCLOSE eligibility
provenance and deletion propagation
```

It does not, by itself, establish the value of:

```text
identity fork semantics
same-principal unsynchronized replicas
snapshot identity continuity
first-person memory attribution
world-branch versus mind-lineage separation
```

Those require the canonical topology suite or another benchmark that directly varies them.

## 8. Acceptance criteria

A result may be called an official GateMem public-benchmark run only when:

- the upstream commit and data manifest are immutable in the artifact;
- official IDs/checkpoint coverage are complete or exclusions are explicitly reported;
- the official evaluator or a byte-for-byte validated equivalent produced the official metrics;
- the method boundary audit passes;
- result rows, configuration, logs, and costs are retained;
- CI can regenerate the deterministic portions.

Silence or a passing unit test is not benchmark evidence.