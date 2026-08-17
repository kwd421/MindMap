# RESULT — MindMapBench-Entitlement-Pilot v0.1

## Status

This is a **synthetic mechanism-isolation result** produced in response to the deciding experiment proposed in issue #1. It compares a strong scoped slot baseline against a minimal epistemic-lineage ledger.

It is **not**:

- an end-to-end natural-language extraction result;
- a reader-LLM result;
- a LoCoMo/LongMemEval result;
- evidence that a deployable system will improve by the same amount;
- a claim that the benchmark is independent of the proposed mechanism.

## Deciding question

Does adding epistemic modality and derivation lineage to a bitemporal, branch-scoped, principal-scoped, permission-aware slot store reduce perspective, misinformation, disclosure, and merge errors?

### B4 — `ScopedSlots`

Includes valid/event time, immutable system-record time, branch filtering, actual holder filtering, event-level permission/revocation, and latest eligible row resolution.

It excludes modality, source reliability, source-family deduplication, derivation lineage, lineage-aware permission propagation, and semantic merge conflict handling.

### B5 — `NCM-Psi`

Adds modality-aware adjudication, source reliability, recency-sensitive belief reconstruction, source-family deduplication, retraction propagation, effective permission through source ancestry, and parent-worldline projection with explicit unresolved merge conflicts.

Diagnostic ablations are `ModalityNoLineage` and `LineageNoModality`.

## Design

- 200 scenarios;
- 1,263 generated claim/evidence events;
- four questions per scenario: world truth, principal belief, requester-disclosable answer, and historical transaction-time projection;
- six 3-level factors: perspective, temporal state, branch, source reliability, disclosure, and derivation;
- greedy pairwise covering design with **100% pairwise level coverage**;
- ten independent dataset seeds;
- 20 repetitions for each correlated-noise condition.

`recorded_at` is a true system/transaction-time axis: it is the immutable time at which the memory service recorded the event. It is not conversation mention time.

## Primary endpoint

Macro exact accuracy over the 600 world, belief, and disclosure questions. A protected answer must return `<restricted>` and an unresolved merge must return `<conflict>`.

Historical transaction-time questions are reported separately and excluded from the primary test.

## Clean result

| System | Primary accuracy | World | Belief | Disclosure | Unauthorized disclosure |
|---|---:|---:|---:|---:|---:|
| NCM-Psi | 99.33% | 100.00% | 98.00% | 100.00% | 0.00% |
| ModalityNoLineage | 91.00% | 100.00% | 98.00% | 75.00% | 37.31% |
| LineageNoModality | 62.33% | 37.00% | 72.00% | 78.00% | 0.00% |
| ScopedSlots | 46.83% | 31.00% | 70.50% | 39.00% | 55.22% |

Primary paired difference:

\[
\Delta = 52.50\text{ percentage points}
\]

Scenario-cluster bootstrap 95% interval:

\[
[47.83, 57.00]\text{ percentage points}
\]

McNemar discordant counts were 315 NCM-Psi-only correct and 0 ScopedSlots-only correct, with exact \(p=3.00\times10^{-95}\).

Across ten generated datasets, primary accuracy was:

| System | Mean | SD | Min | Max |
|---|---:|---:|---:|---:|
| NCM-Psi | 99.25% | 0.34% | 98.83% | 100.00% |
| ModalityNoLineage | 90.87% | 0.96% | 89.00% | 92.33% |
| LineageNoModality | 61.88% | 1.43% | 59.67% | 64.33% |
| ScopedSlots | 43.58% | 1.69% | 41.00% | 46.83% |

## What the ablation actually says

The largest ordinary state-reconstruction gain came from **modality**, not lineage:

- `ModalityNoLineage` reached 100% world accuracy and 98% belief accuracy.
- Adding lineage did not improve those two clean subtasks further.

The incremental benefit of lineage was concentrated in governance:

- disclosure accuracy rose from 75% to 100%;
- unauthorized disclosure fell from 37.31% to 0%.

Therefore the defensible interpretation is:

> Modality is the main clean state-adjudication primitive in this pilot; derivation lineage is primarily a disclosure/retraction primitive.

A simple branch namespace was already sufficient for ordinary divergent-branch isolation: all clean systems had zero measured cross-branch contamination. NCM-Psi's branch benefit appeared in **attempted merge conflict recognition**, not simple branch filtering.

## Residual clean failures

NCM-Psi missed four of 600 primary questions. All four had the same pattern:

- direct perspective;
- mistaken source;
- implicit invalidation;
- the trusted mistaken report and the supported inference had nearly equal hand-set scores.

This is a calibration/decision-boundary problem. Repeatedly tuning hand-written weights until the clean generator reaches 100% would overfit the pilot.

## Correlated structured-error study

Eight event-level corruption modes were used: branch swap, holder swap, modality laundering, visibility widening, transaction-time shift, lineage break, value flip, and reliability flip.

A latent source-family error causes multiple descendant events to fail together. `rho` controls the family-shared component while preserving approximately the same marginal corruption rate.

Selected NCM-Psi results for `rho=0.5`:

| Target corruption | Accuracy | Unauthorized disclosure | Branch contamination |
|---:|---:|---:|---:|
| 0% | 99.50% | 0.00% | 0.00% |
| 5% | 97.68% | 0.97% | 0.35% |
| 10% | 96.03% | 2.46% | 0.58% |
| 20% | 93.06% | 4.85% | 1.18% |
| 30% | 89.44% | 6.08% | 2.04% |

Changing `rho` had only a modest effect on mean accuracy because the marginal corrupted-record fraction was held approximately fixed and there was no repeated-extractor voting mechanism. The next correlation experiment should estimate tail risk and test ensembles whose benefit depends on error independence.

## Decisions supported by this pilot

### Accept provisionally

1. `recorded_at` must be true immutable system time.
2. Possession and current permission must remain separate.
3. Modality and derivation lineage should be tested as separate components.
4. A derived claim must not silently escape the strictest active policy in its source ancestry.
5. Merge conflict is not equivalent to ordinary branch retrieval.

### Reject as a primary claim

1. A generic L1/L2/L3 hierarchy is not needed for the deciding experiment.
2. An always-on graph is not needed.
3. Branch filtering by itself is not a demonstrated NCM-Psi advantage.
4. This synthetic improvement cannot be quoted as an expected real-world gain.

## Remaining falsification gates

The mechanism claim should be narrowed or rejected if:

- a raw-text scoped-slot system matches NCM-Psi after both use the same extractor;
- lineage adds no disclosure benefit when policies and derivations are extracted rather than generated;
- real extraction errors destroy the clean advantage at plausible rates;
- a released temporal/governance system matches the result under one frozen harness;
- the role-play benchmark does not change architecture rankings relative to ordinary QA;
- the reader LLM ignores correct perspective-scoped evidence.

## Next experiment

Implement four diagnostic conditions:

- C0: no memory;
- C1: gold evidence;
- C2: gold structure with retrieval;
- C3: raw dialogue end to end.

The immediate comparison should use the same extractor and reader for scoped slots, modality without lineage, and full modality plus lineage.
