[Session B]

# GateMem Finite-Sample and Safety-Certification Limits

**Status:** pre-outcome statistical constraint  
**Pinned public data:** `rzhub/GateMem@603f9f4b4ba4b77f043c20f85687fa016fd720b0`  
**Purpose:** distinguish an operational leakage target from what one benchmark run can statistically certify

## 1. Observed evaluation structure

The pinned public release contains:

```text
91 episodes
20,293 dialogue turns
2,218 checkpoints
```

Checkpoint composition used by the deterministic official endpoint controls:

| Domain | Utility | Privacy | Safety/deletion | Total |
|---|---:|---:|---:|---:|
| Education | 180 | 180 | 180 | 540 |
| Household | 184 | 184 | 184 | 552 |
| Medical | 210 | 192 | 177 | 579 |
| Office | 154 | 171 | 222 | 547 |
| **Total** | **728** | **727** | **763** | **2,218** |

The average is approximately:

```math
2218/91=24.37
```

checkpoints per episode. These checkpoints are not independent because they share episode history, principals, policy state, and generation templates.

---

## 2. Zero observed violations do not imply zero risk

For `n` independent Bernoulli opportunities and zero observed violations, the exact one-sided 95% upper confidence bound is:

```math
p_{upper}=1-0.05^{1/n}.
```

The common rule-of-three approximation is:

```math
p_{upper}\approx 3/n.
```

### Privacy checkpoint bound with zero violations

| Domain | n | Exact one-sided 95% upper bound |
|---|---:|---:|
| Education | 180 | 1.651% |
| Household | 184 | 1.615% |
| Medical | 192 | 1.548% |
| Office | 171 | 1.737% |
| **All domains pooled** | **727** | **0.411%** |

### Safety/deletion checkpoint bound with zero violations

| Domain | n | Exact one-sided 95% upper bound |
|---|---:|---:|
| Education | 180 | 1.651% |
| Household | 184 | 1.615% |
| Medical | 177 | 1.678% |
| Office | 222 | 1.340% |
| **All domains pooled** | **763** | **0.392%** |

Therefore a single zero-violation run cannot statistically establish a checkpoint-level rate below 1% **within any individual domain**. It can establish a sub-1% checkpoint-level upper bound only after pooling privacy or deletion checkpoints across domains, and that pooled statement assumes the pooled estimand was preregistered and meaningful.

---

## 3. Minimum zero-event sample for a 1% bound

To make the one-sided 95% zero-event upper bound less than 1%:

```math
1-0.05^{1/n}<0.01.
```

Equivalently:

```math
n>\frac{\log(0.05)}{\log(0.99)}=298.07.
```

At least **299 independent eligible opportunities** with zero violations are required.

Every GateMem domain has fewer than 299 privacy checkpoints and fewer than 299 safety/deletion checkpoints.

This has two consequences:

1. `privacy leakage <= 1%` and `deletion leakage <= 1%` may be useful **operating requirements**;
2. the benchmark cannot automatically provide a per-domain **95% statistical certification** of those requirements from one run.

The paper must not conflate the two.

---

## 4. Episode-level safety is a different estimand

A deployment-relevant question is whether an episode experiences at least one violation.

With 91 episodes and zero affected episodes, the independent-cluster one-sided 95% upper bound would be:

```math
1-0.05^{1/91}=3.238\%.
```

Thus even a perfect checkpoint table cannot certify that fewer than 1% of conversations/episodes would experience any violation.

Report both:

```text
checkpoint-level violation rate
percentage of episodes with at least one violation
violations per affected episode
maximum violations in one episode
```

The episode-level measure is not obtained by treating 2,218 checkpoints as independent.

---

## 5. Correlation makes checkpoint-only bounds optimistic

The zero-event calculations above are exact only under independent Bernoulli trials for the chosen estimand.

GateMem checkpoints within one episode share:

```text
same principals and relationships
same evolving memory state
same deletion/policy operations
same lexical templates and domain
same method instance under sequential compatibility mode
```

Positive intracluster correlation reduces effective sample size. Use the episode as the primary resampling cluster.

A design-effect diagnostic is:

```math
DE=1+(\bar m-1)\rho,
```

where `m_bar` is average checkpoint count and `rho` is intracluster correlation. With `m_bar = 24.37`, even modest `rho` can sharply reduce effective information.

Estimate `rho` from development/pilot outputs by metric and domain. Do not substitute an arbitrary value in the confirmatory analysis.

---

## 6. Domain pooling requirements

A pooled privacy or deletion rate is valid only when all of the following are frozen before test inspection:

```text
common metric definition
common capability condition
common checkpoint isolation mode
common method/read/gate configuration
predefined domain weights
complete domain reporting
```

Two distinct estimands are:

```math
p_{micro}=\frac{\sum_d violations_d}{\sum_d eligible_d}
```

and:

```math
p_{macro}=\frac{1}{4}\sum_d p_d.
```

The micro rate weights domains by checkpoint count. The macro rate weights domains equally. They answer different questions and must not be selected after viewing results.

Regardless of the chosen aggregate, retain all four domain rows and confidence bounds.

---

## 7. Leakage targets as constrained decision rules

A development-frozen operating rule may require:

```math
PrivacyE2ELeak\le 0.01,
\quad
DeletionE2ELeak\le 0.01.
```

On test, report separately:

```text
point estimate satisfies target? yes/no
one-sided upper confidence bound satisfies target? yes/no
episode-cluster interval
per-domain interval
```

Possible outcome:

```text
0 observed violations
point estimate = 0
operating target met on the observed set
95% per-domain certification not achieved because n is insufficient
```

This is not a contradiction. It is the correct finite-sample interpretation.

---

## 8. Comparing methods with rare violations

When paired methods have few violations, do not rely only on asymptotic normal tests.

Use:

```text
paired episode-cluster bootstrap
cluster-level permutation of method labels
exact discordant-count summaries
one-sided upper bounds for each method
```

Report the paired contingency at both checkpoint and episode level:

```text
A safe / B safe
A safe / B violation
A violation / B safe
A violation / B violation
```

A method with zero events is not automatically significantly safer than one with one event; the cluster and discordance structure matters.

---

## 9. Power consequences

GateMem is strong for detecting the very high leakage rates seen in the raw context-echo endpoint. It is much less powerful for distinguishing two already-safe methods near zero.

Before a confirmatory B2/B3/B4/B5 comparison:

1. estimate episode-level baseline rates and intracluster correlation on development runs;
2. simulate paired episode clusters under candidate effect sizes;
3. estimate power for the frozen leakage and governed-success endpoints;
4. widen the practical margin or add independent benchmark histories if power is insufficient;
5. retain an `inconclusive` conclusion class.

Repeated model seeds on the same 91 episodes do not create new independent deployment histories.

---

## 10. Recommended reporting block

For every GateMem privacy and deletion result, include:

```text
violations / eligible checkpoints
point rate
one-sided 95% upper bound
episodes affected / 91 eligible episodes
episode-level cluster interval
capability condition
checkpoint mode
reader/gate/method configuration
```

Example template:

```text
Privacy e2e leakage: x / n checkpoints (p%),
one-sided 95% upper bound u%;
y / e episodes affected.
The preregistered 1% operating target was [met/not met] on the observed set;
[was/was not] statistically certified at the stated confidence level.
```

---

## 11. Claim boundary

The pinned GateMem suite can falsify unsafe systems and measure substantial utility-governance tradeoffs. It cannot, by itself, prove arbitrarily small deployment risk.

A defensible conclusion distinguishes:

```text
observed benchmark performance
confidence bound under the benchmark sampling unit
operating requirement
external deployment guarantee
```

Only the first two are directly estimated here.
