# MindMap Public Benchmark Matrix

**Status:** execution policy  
**Coordination:** Issue #4

## 1. Selection standard

A public benchmark is admitted only when the study can identify and retain:

- a primary paper or official technical report;
- public data or an official protected evaluation interface;
- an official repository/toolkit or a precisely documented scoring contract;
- stable item/checkpoint identifiers;
- official per-task metrics;
- a license and reproducible prediction format;
- a frozen revision or release used by the experiment.

A recent specialized benchmark is not described as broadly established merely because it is public. A synthetic internal suite is never substituted for external validation.

## 2. Required external evidence stack

### B1 — LoCoMo

Role:

- established long-conversation and multi-session memory utility;
- factual, temporal, causal, and multi-hop recall;
- external validity for ordinary conversational memory.

Use:

- preserve the official split and answer metrics;
- compare raw retrieval, generic structured memory, normalized MindMap, and raw-fallback conditions under matched answer budgets;
- report retrieval evidence and answer metrics separately where possible.

Does not establish:

- multi-principal access control;
- deletion compliance;
- mind-instance lineage or first-person attribution.

### B2 — LongMemEval

Role:

- established multi-session memory evaluation;
- temporal reasoning, information updates, abstention, and long-range retrieval.

Use:

- preserve official task categories and metrics;
- report update/current-state cases separately from ordinary retrieval;
- freeze context and answer-model budgets across systems.

Does not establish:

- identity-fork semantics;
- requester-scoped disclosure;
- active deletion governance.

### B3 — GateMem

Role:

- specialized public governance evaluation;
- utility, access control, and active forgetting in multi-principal shared memory.

Use:

- official protected incremental boundary;
- official checkpoint IDs and category metrics;
- official summary metric where available;
- exact numerator/denominator for access and forgetting failures;
- answered/abstained counts and safe coverage as labelled supplements.

Does not establish by itself:

- broad adoption of the full MindMap concept;
- first-person memory attribution;
- identity forks, world forks, or snapshot identity continuity.

GateMem is therefore a required specialized complement, not the sole public proof.

## 3. Stage-localized supplements

### HaluMem

Use after the core B1–B3 runners are stable to localize extraction, updating, and answer-stage hallucination. Do not merge stage scores into one custom memory score.

### LoCoMo-Plus

Use for latent preference/constraint application under cue–trigger disconnect. Preserve its official constraint metric and separate it from ordinary recall.

### Additional benchmarks

EverMemBench, LongMemEval-V2, or later public suites enter only through a dated amendment that documents:

- the missing axis they add;
- official source and license;
- adapter leakage audit;
- incremental cost;
- why B1–B3 do not already answer the question.

## 4. Internal topology suite

The canonical NCM-Topo/MindMap topology suite remains necessary for axes that public benchmarks do not vary independently:

```text
mind copy without world fork
world fork without mind copy
same-principal unsynchronized replicas
restore recovery gap
identity fork and evidence-copy attribution
receipt versus belief adoption
first-person memory attribution
alternative public/protected support paths
```

Its role is mechanism discrimination and negative controls. It is not external evidence and receives exact fixed-suite counts, not public-benchmark status.

## 5. Cross-benchmark claim rules

A claim is supported only on the axes actually measured.

Examples:

```text
GateMem improvement
  -> supports governance/forgetting result
  -> does not prove identity-lineage value

LongMemEval update improvement
  -> supports temporal/update result
  -> does not prove requester-scoped policy

NCM-Topo attribution improvement
  -> supports first-person/lineage mechanism
  -> does not prove external conversational utility
```

No average across unrelated benchmark scores is reported as a universal MindMap score.

## 6. Matched systems

The common comparison ladder is:

```text
X0 raw retrieval / official raw baseline
X1 complete capacity-matched generic event representation
X2 normalized MindMap representation
X3 normalized MindMap + preregistered raw fallback
```

Optional component ablations:

```text
without bitemporal update
without policy/availability
without provenance closure
without mind-instance lineage/attribution
without raw fallback
```

G and T receive the same raw evidence, model family/revision, call/retry/token budget, retrieval budget, and answer model. Typed validators must be matched by computationally equivalent generic validators when the question is representation rather than enforcement ergonomics.

## 7. Primary reporting principle

The study seeks a decomposed result:

- temporal/update mechanisms on LongMemEval;
- general long-dialogue utility on LoCoMo;
- policy, availability, and deletion on GateMem;
- extraction/update/answer failure localization on HaluMem;
- mind-instance lineage and first-person attribution on NCM-Topo.

The desired conclusion is not that the full schema wins everywhere. The useful result identifies the smallest MindMap subset required for each failure class and records null or generic-favorable results unchanged.