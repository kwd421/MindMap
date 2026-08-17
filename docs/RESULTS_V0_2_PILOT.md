# NCM-Ψ v0.2 Mechanism-Isolation Pilot Results

**Status:** exploratory structured-oracle experiment  
**Date:** 2026-08-17  
**Interpretation:** conformance and failure-mode evidence only; not end-to-end conversational accuracy

## 1. Question tested

The pilot asks whether an explicit exposure-transition ledger and cognitive-instance lineage are necessary to satisfy the proposed semantics for copied/restored minds, world branches, belief states, and derivation-aware disclosure.

It compares:

- **B3 — global character memory:** copied minds and world branches collapse;
- **B5 — branch-scoped character memory:** world branches are isolated, but copied minds sharing one character identity still collapse and disclosure checks only the final claim row;
- **B5a — lineage only:** world and mind lineage plus exposure transitions, but final-row disclosure and naive source counting;
- **B5b — policy only:** derivation-aware policy and source-family grouping, but copied minds still collapse;
- **B6 — NCM-Ψ reference resolver:** separate world branch and mind-instance lineage, event-sourced exposure transitions, bitemporal claims, and policy propagation through provenance ancestry.

All systems receive gold structured records. The experiment does not test extraction from raw dialogue.

## 2. Dataset

- 11 adversarial scenario templates;
- 24 seeded variants per template;
- 264 independent scenarios;
- 6 questions per scenario;
- 1,584 questions per system.

Templates cover mind copy without world divergence, selective transfer, sealed memory, restore gaps, world divergence, cross-world reports, private derivations, rumor laundering, backdated corrections, world truth versus belief, and combined cases.

## 3. Clean structured results

| System | Accuracy | Cross-instance error | Cross-world error | Unauthorized disclosure | Provenance-laundering error |
|---|---:|---:|---:|---:|---:|
| B3 global character | 65.66% | 35.56% | 47.06% | 66.67% | 75.00% |
| B5 branch-scoped character | 76.26% | 35.56% | 5.88% | 66.67% | 75.00% |
| B5a lineage only | 92.42% | 0.00% | 0.00% | 66.67% | 75.00% |
| B5b policy only | 83.84% | 35.56% | 5.88% | 0.00% | 0.00% |
| B6 NCM-Ψ | 100.00% | 0.00% | 0.00% | 0.00% | 0.00% |

The strongest component ablation is B5a. The scenario-clustered B6 minus B5a accuracy difference is:

```text
+7.58 percentage points
95% scenario-cluster bootstrap CI: +6.06 to +9.22 points
Monte-Carlo within-scenario sign-flip p ≈ 1.0e-5
```

The p-value is bounded by the 100,000-repetition Monte-Carlo resolution and should not be interpreted more precisely.

## 4. What the clean result establishes

Within the benchmark semantics:

1. branch scoping fixes worldline contamination but not copied-mind contamination;
2. lineage/exposure semantics remove cross-instance errors but leave disclosure and provenance laundering unchanged;
3. derivation-aware policy removes disclosure/provenance errors but does not separate sibling minds;
4. factorial ablations attribute the remaining clean gain to the conjunction rather than one bundled feature;
5. a claim's about-world branch can differ from its assertion/holder context after a cross-world report;
6. historical exposure remains true after sealing even when current availability is false;
7. static ownership fields cannot represent receive, seal, forget, revoke, and restore transitions over time;
8. origin-family grouping is necessary to avoid counting derivative summaries as independent corroboration.

The 100% B6 score is expected for a deterministic reference resolver aligned with the generator. It is a conformance result, not evidence that an LLM extractor can construct the records correctly.

## 5. Correlated structured fault injection

Twenty dataset replications were run at each corrupted-scenario prevalence. Corruption acts on joint event/lineage hypotheses rather than independent field dropout.

| Corrupted scenarios | System | Accuracy, mean ± SD | Cross-instance error | Unauthorized disclosure |
|---:|---|---:|---:|---:|
| 0% | B5 | 76.26% ± 0.00% | 35.56% | 66.67% |
| 0% | B5a lineage only | 92.42% ± 0.00% | 0.00% | 66.67% |
| 0% | B5b policy only | 83.84% ± 0.00% | 35.56% | 0.00% |
| 0% | B6 | 100.00% ± 0.00% | 0.00% | 0.00% |
| 5% | B5 | 76.26% ± 0.05% | 35.54% | 66.67% |
| 5% | B5a lineage only | 92.11% ± 0.20% | 0.63% | 66.67% |
| 5% | B5b policy only | 83.80% ± 0.07% | 35.54% | 0.49% |
| 5% | B6 | 99.66% ± 0.19% | 0.63% | 0.49% |
| 10% | B5 | 76.23% ± 0.09% | 35.53% | 67.01% |
| 10% | B5a lineage only | 91.90% ± 0.19% | 1.02% | 67.01% |
| 10% | B5b policy only | 83.72% ± 0.13% | 35.53% | 1.32% |
| 10% | B6 | 99.40% ± 0.21% | 1.02% | 1.32% |
| 20% | B5 | 76.15% ± 0.13% | 35.53% | 66.74% |
| 20% | B5a lineage only | 91.10% ± 0.36% | 2.59% | 66.74% |
| 20% | B5b policy only | 83.58% ± 0.17% | 35.53% | 1.60% |
| 20% | B6 | 98.52% ± 0.41% | 2.59% | 1.60% |
| 30% | B5 | 76.07% ± 0.22% | 35.51% | 67.29% |
| 30% | B5a lineage only | 90.55% ± 0.48% | 3.51% | 67.29% |
| 30% | B5b policy only | 83.47% ± 0.19% | 35.51% | 3.06% |
| 30% | B6 | 97.95% ± 0.47% | 3.51% | 3.06% |

These aggregates are optimistic because some randomly selected corruptions are inapplicable to templates lacking the relevant structure. One-mode interventions are more diagnostic.

## 6. One-mode-at-a-time diagnostics for B6

| Corruption mode | B6 accuracy | Cross-instance error | Cross-world error | Unauthorized disclosure |
|---|---:|---:|---:|---:|
| identity collapse | 85.35% | 29.31% | 8.33% | 0.00% |
| fork-cutoff shift | 96.97% | 6.67% | 0.00% | 0.00% |
| world/mind branch swap | 97.92% | 0.28% | 7.84% | 0.00% |
| exposure-source swap | 93.94% | 13.33% | 0.00% | 0.00% |
| attitude laundering | 98.42% | 2.22% | 0.00% | 0.00% |
| policy declassification | 96.78% | 0.00% | 0.00% | **70.83%** |
| restore-parent error | 95.45% | 10.00% | 0.00% | 0.00% |
| temporal-scope shift | 96.65% | 1.94% | 1.72% | 0.00% |
| speaker/holder swap | 91.10% | 16.25% | 7.11% | 0.00% |

## 7. Main negative result

**Derivation-aware disclosure is brittle when the derivation edge or restrictive source label is lost.** Under targeted `policy_declassification`, general accuracy remains 96.78%, yet unauthorized disclosure rises to 70.83%. One overall QA score would largely hide the safety collapse.

This supports three changes for the end-to-end system:

1. policy labels and derivation roots need integrity protection independent of the extractor that writes semantic claims;
2. disclosure must remain a separate safety endpoint;
3. low-confidence or incomplete lineage should default to abstention or stricter policy rather than public disclosure.

## 8. Other important failure modes

- Identity collapse is the largest general-quality failure, reducing B6 to 85.35%.
- Speaker/holder swaps reduce accuracy to 91.10% and contaminate both mind and world scopes.
- Exposure-source swaps and restore-parent errors each create about 10% cross-instance error on relevant questions.
- World/mind branch swaps preserve high aggregate accuracy while causing 7.84% cross-world error.

## 9. Limitations

- The generator and B6 share the same formal semantics.
- There is no raw-language parsing, entity linking, temporal normalization, or LLM reader.
- Baselines are mechanism baselines, not reproductions of external memory systems.
- Templates are deliberately adversarial rather than sampled from real conversations.
- Noise interventions are hand-designed and do not yet match a measured extractor error distribution.
- The pilot is exploratory; hypotheses were not frozen before implementation.

## 10. Decisions supported for the next version

Retain orthogonal world and mind lineage, immutable evidence, claim revisions, exposure transitions, exposure-versus-availability separation, origin-family grouping, ancestry-aware policy, and separate leakage metrics.

Do not yet add always-on graph traversal, semantic identity merge, independently writable memory tiers, or one blended quality score.

## 11. Next falsification steps

1. Strengthen B5 with explicit snapshot cloning but no exposure ledger.
2. Run a frozen raw-text extractor and manually label joint event hypotheses.
3. Add conservative abstention when lineage or policy integrity is uncertain.
4. Measure natural rates of identity collapse, holder swap, temporal shift, and policy-lineage loss.
5. Test reproducible external systems where their APIs permit branch, speaker, and policy controls.
6. Freeze generator, split topology, margins, and analysis before opening a confirmatory test set.
