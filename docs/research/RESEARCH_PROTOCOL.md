# MindMap empirical research protocol

**Protocol ID:** `MM-RP-001`  
**Version:** `0.1.0`  
**Effective date:** 2026-08-27  
**Status:** living protocol; changes require a dated decision-log entry

## 1. Purpose

MindMap studies long-term agent memory as a governed, temporal, provenance-aware
state system. The research must measure not only whether an answer is correct,
but also whether the system stored, updated, retrieved, disclosed, forgot, and
reconstructed information through an allowed path.

The protocol follows the disclosure and reproducibility expectations of the
[NeurIPS checklist](https://neurips.cc/public/guides/PaperChecklist), the
artifact qualities used by [ACM](https://www.acm.org/publications/policies/artifact-review-and-badging-current),
and the before/after distinction encouraged by
[OSF preregistration](https://help.osf.io/article/330-welcome-to-registrations).

## 2. Research questions

- **RQ1 — semantic adequacy:** Can the representation distinguish world truth,
  exposure, current availability, belief, attribution, disclosure, and
  justification without internal contradiction?
- **RQ2 — lifecycle correctness:** Do copy, backup, restore, fork, merge,
  deletion, revocation, reacquisition, and reconstruction preserve their
  declared temporal and identity semantics?
- **RQ3 — governed retrieval:** Does a deployable pre-reader gate reduce
  forbidden prompt exposure and end-to-end leakage relative to information-
  matched raw retrieval without unacceptable utility loss?
- **RQ4 — external validity:** Do the mechanisms survive public long-term-memory
  tasks covering retrieval, updates, temporal reasoning, abstention,
  hallucination, and selective forgetting?
- **RQ5 — operational value:** What accuracy, safety, latency, storage, token,
  and monetary trade-offs arise under a fixed budget?

## 3. Standing hypotheses

- **H1:** Equal-information complete generic and typed implementations should
  agree on clean finite semantics. A disagreement is initially treated as a bug
  or underspecified contract, not proof of typed superiority.
- **H2:** A reader placed after unsafe retrieval can reduce answer-surface
  leakage while leaving prompt-context and end-to-end leakage unchanged.
- **H3:** A pre-reader gate using only deployable information can reduce
  forbidden prompt exposure; the effect and utility cost must be measured.
- **H4:** Explicit lineage, valid/system time, provenance, and terminal deletion
  improve fault detection and auditability under matched information.
- **H5:** No single benchmark is sufficient: retrieval/QA, dynamic update,
  abstention, hallucination, and selective forgetting must be reported
  separately.

H1 and H2 have current supporting evidence in the local deterministic and
GateMem negative-control studies. H3–H5 remain open or only partially tested.

## 4. Study classes and claim gates

| Class | Purpose | May tune? | Minimum repetition | Permitted claim |
|---|---|---:|---:|---|
| `smoke` | prove the harness runs | yes | 1 | execution only |
| `development` | debug and discover failure modes | yes | as needed | exploratory observation |
| `pilot` | estimate feasibility/variance/cost | limited, disclosed | 2 when stochastic | pilot only |
| `confirmatory` | test a frozen hypothesis | no after outcome access | preregistered | scoped empirical result |
| `reproduction` | same code/data, independent run | no silent changes | at least 2 where stochastic | reproduced result |
| `replication` | independent implementation or changed setting | preregistered | justified by design | external corroboration |

Promotion requires all of the following:

1. a manifest created before outcome inspection for confirmatory work;
2. exact source, data, model, prompt, judge, and environment identity;
3. raw predictions retained or a documented protected-data retention reason;
4. metrics recomputable from recorded inputs and outputs;
5. protocol deviations listed;
6. negative and null results preserved;
7. claim-evidence ledger updated with scope and counter-evidence;
8. an independent review or run for any externally presented main claim.

## 5. Experiment lifecycle

### 5.1 Before execution

Create `records/<experiment-id>.json` and freeze:

- research question and directional or non-directional hypothesis;
- study class, primary outcome, secondary outcomes, and stopping rule;
- dataset identity, license, split, inclusion/exclusion, sample IDs or their hash;
- independent, dependent, control, nuisance, and evaluator-only variables;
- method arms, budgets, random seeds, model IDs/revisions, decoding settings;
- prompts and judge rubric hashes;
- analysis plan, missing-data rules, and multiple-comparison treatment;
- anticipated cost ceiling and privacy constraints.

### 5.2 During execution

Record without editing earlier entries:

- UTC start/end, host/OS/Python, CPU/GPU, dependency lock/digest;
- git source head and actual checkout revision separately;
- every retry, timeout, API error, fallback, and manual intervention;
- input, cached-input, output, and reasoning tokens when available;
- wall-clock latency and monetary cost per arm;
- artifact paths and SHA-256 digests.

### 5.3 After execution

Report:

- counts and denominators before percentages;
- per-category results and aggregate weighting rule;
- point estimates plus uncertainty appropriate to the design;
- all preregistered outcomes, including unfavorable ones;
- sensitivity analysis for judge, seed, threshold, and retrieval budget when
  these can change the conclusion;
- deviations, validity threats, and the strongest defensible claim.

## 6. LLM-specific controls

- Treat provider aliases as mutable. Record the returned model identifier and
  date, and pin a revision when the provider exposes one.
- Freeze temperature, top-p, max output, reasoning/thinking mode, tool access,
  system prompt, answer prompt, and judge prompt.
- Separate the memory method from the answer reader and evaluator. The same
  reader and budget must be used across matched memory arms.
- Never expose gold answers, evidence labels, question type, future turns, or
  deletion/privacy annotations to the method unless that is the explicit
  experimental factor.
- Use deterministic metrics where valid. For LLM judges, retain judge outputs,
  test a blinded sample manually, and estimate seed/prompt sensitivity.
- Record abstention separately from wrong answers and infrastructure failures.
- API retries must not silently change prompts, models, or decoding parameters.

## 7. Privacy and protected benchmarks

- Secrets remain in the operating-system keychain or process environment.
- Protected raw data and opaque evaluator tokens stay outside git.
- Commit aggregates only when redistribution is prohibited.
- Hashes may prove artifact identity but do not grant redistribution rights.
- Deletion is evaluated at storage, retrieval, prompt, answer, backup, cache,
  and audit surfaces; passing one surface is not called complete deletion.

## 8. Statistics

- Fixed exhaustive semantic fixtures use exact counts, not inferential p-values.
- Sampled/stochastic results report the sampling unit, number of independent
  runs, seed source, mean/median as appropriate, dispersion, and confidence
  interval or a clear reason it is not meaningful.
- Paired designs retain pair identity and use paired differences.
- Development-set tuning and final evaluation must use disjoint outcome access.
- If many primary comparisons are introduced, freeze a correction method or
  label the analysis exploratory.
- Practical effect size and safety boundary take priority over a lone p-value.

## 9. Reproducibility target

Each result should ultimately be:

- **documented:** complete inventory and instructions;
- **consistent:** artifacts correspond to the stated source and claim;
- **complete:** all material components are present or exclusions are stated;
- **exercisable:** a fresh environment can run the declared command;
- **auditable:** outputs lead back to inputs and decisions;
- **independently checked:** main results are reproduced or replicated.

These are project targets inspired by ACM artifact criteria, not claimed badges.
