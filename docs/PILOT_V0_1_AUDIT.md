# Audit of the Reported MindMapBench-Pilot v0.1

**Status:** independent review draft; implementation not yet available on `main`  
**Reviewer marker:** Session B  
**Date:** 2026-08-17

## 1. Reviewed claim

Issue #1 reports a symbolic component experiment with:

- 1,000 generated scenarios;
- 16 events per scenario;
- 25 questions per scenario;
- 25,000 clean questions;
- clean NCM-Ψ accuracy of 1.000 with zero reported leakage;
- structured-event corruption experiments with a confidence-gated simulated fallback channel.

The report explicitly states that this is a symbolic component test, not a natural-language benchmark. That caveat is necessary and should be retained.

## 2. Repository audit

At review time, `main` has two commits:

1. repository initialization adding `README.md`;
2. addition of `docs/PREREG_V0_2.md`.

The README names directories and commands for `src/`, `experiments/`, `tests/`, `results/`, and `benchmarks/`, but those artifacts are not present on `main` at the time of review.

Consequently, the following cannot yet be verified:

- generator behavior and template distribution;
- exact ablation semantics;
- scoring definitions;
- random seeds and splits;
- corruption implementation;
- fallback confidence model;
- the assumed 0.85 recovery process;
- bootstrap resampling unit;
- per-question or per-scenario outputs;
- reproducibility of aggregate tables.

Until the implementation is committed, the result should be described as:

> session-reported, unverified symbolic conformance output.

It should not be called reproducible solely because commands are listed in the README.

## 3. Main validity finding

The reported pilot appears to test an earlier model containing:

```text
world state by branch/time
agent belief/knowledge state by branch/time
audience/observation scope
branch ancestry
seal policy
```

The newer v0.2 hypothesis isolates a different increment:

```text
B5: strong epistemic/branch/principal/policy baseline without explicit exposure lineage
B6: B5 + exposure transitions + cognitive-instance lineage
```

The report does not establish that its dataset contains the required orthogonal mechanisms:

- cognitive copy without world fork;
- world fork without cognitive copy;
- explicit receipt followed by rejection versus adoption;
- historical exposure distinct from current availability;
- restore from a snapshot cutoff;
- typed same-principal replica versus new-principal identity fork;
- about-world branch preserved across cross-world transfer.

Therefore the existing run cannot be used as evidence or power input for H1 until the code and scenario definitions show that `PerspectiveNoLineage` is exactly the preregistered B5 and that the full system is exactly B6.

## 4. Interpretation of clean 100%

Clean 100% is at most a conformance result when:

- gold structured fields generate the hidden state;
- systems receive those same gold structures;
- deterministic queries directly exercise included fields;
- the evaluator derives answers from the same state machine.

This can prove that an implementation satisfies its own declared semantics. It does not prove empirical necessity, real-text extractability, public-benchmark benefit, or novelty.

The clean ablation gaps may reflect the fixed fraction of templates designed to require each removed primitive. Required reporting:

- accuracy and error type by scenario template;
- primitive-by-template requirement matrix;
- fraction of gold answers changed by each ablated primitive;
- errors on templates outside the primitive's expected causal scope;
- one-factor implementation diff for each ablation;
- held-out topology/template families.

## 5. Fallback audit

The reported fallback experiment assumes an independent raw-evidence recovery channel with probability 0.85. This creates a useful upper-bound simulator but does not establish that real raw-text fallback will repair correlated extraction errors.

### Required conditions

Compare:

1. same model and prompt family for extraction/fallback;
2. same model with a different prompt;
3. different model or deterministic lexical reconstruction;
4. idealized independent simulator.

Report fallback error correlation with the structured extractor.

### Clean fallback triggers

Fallback reportedly triggers for 13.45% of clean events while clean accuracy remains 1.000. The implementation must report:

- false-trigger rate;
- conditional accuracy on clean fallback cases;
- errors introduced by unnecessary fallback;
- extra tokens and latency;
- evidence distractor rate;
- threshold-swept accuracy–cost and risk–coverage curves.

### Calibration

Publish:

- confidence definition;
- score distribution by corruption mode;
- validation objective and chosen threshold;
- Brier score and ECE for corruption detection;
- whether confidence directly accesses injected error flags or gold structured fields.

The bootstrap interval under the idealized simulator is Monte Carlo precision conditional on simulator assumptions. It is not a general confidence interval for real-world fallback benefit.

## 6. Statistical audit

The independent unit is the scenario, not the question. Twenty-five questions sharing one hidden event log are clustered.

Required analysis:

```text
paired scenario-level comparison
scenario-cluster bootstrap
between-seed variance
stratification/reporting by template family
all exclusions and failed runs
```

Question-level bootstrap or McNemar analysis may be supplementary only.

## 7. Missing decisive baseline

The decisive baseline is a strong composition rather than a broad flat memory system:

```text
belief/attitude tracker
+ world-branch ancestry
+ principal/mind identifiers
+ row-level ACL/seal filters
+ attributed transfer records
```

but no explicit exposure-transition reconstruction or typed cognitive-lineage inheritance.

This is preregistered B5. The contribution fails if B5 matches B6 under equal evidence and metadata budgets.

`PerspectiveNoLineage` can serve as B5 only after the implementation demonstrates exact semantic equivalence.

## 8. Required aligned P0

Before another large run, implement a small auditable collision audit containing at least:

1. mind copy without world fork;
2. world fork without mind copy;
3. selective transfer received then rejected versus adopted;
4. prior exposure followed by sealing;
5. restore from an older snapshot and later witness report;
6. operational replica versus identity fork;
7. cross-world attributed report retaining its about-world scope;
8. delayed import separating assertion-event valid time from system time;
9. protected-only support revoked;
10. independent public justification surviving protected-source revocation;
11. rumor laundering through one source family;
12. ordinary temporal negative control where B5 and B6 must tie.

Compare B3 through B7 as defined in `PREREG_COLLISION_AUDIT.md` and publish per-scenario outputs.

## 9. Artifact checklist

Before accepting the original tables as reproduced, commit or publish:

- package/project configuration;
- deterministic generator;
- frozen scenario archetypes;
- systems B0–B6 or exact original equivalents;
- one-feature ablation controls;
- test suite for noninterference and state consistency;
- corruption and fallback code;
- validation/test seeds and split files;
- compact per-scenario result file;
- analysis script using scenario-cluster resampling;
- immutable run manifest;
- aggregate result tables generated from the committed result file.

README reproduction commands should fail clearly when artifacts are absent, or the README should be marked as a planned layout until the code lands.

## 10. Review decision

### Accepted

- The symbolic-conformance caveat is directionally correct.
- Perspective, branch, and policy semantics are worth testing separately from world truth.
- Event-level correlated corruption is preferable to independent field dropout.
- Accuracy–cost frontiers should be reported.

### Not accepted yet

- Reproducibility.
- The conclusion that the tested primitives are jointly necessary beyond the constructed generator.
- Use of the reported effect sizes to power or freeze the newer B6-versus-B5 hypothesis.
- Real-world raw-fallback robustness.

### Permitted current label

> Exploratory, unverified, symbolic branch/perspective/seal conformance observation predating the frozen perspective-lineage mechanism comparison.

This classification can be upgraded after code, data manifests, and an aligned rerun are available.