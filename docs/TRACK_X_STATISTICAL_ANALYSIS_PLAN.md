[Session B]

# Track X Statistical Analysis Plan

**Status:** pre-outcome proposal  
**Scope:** public Track X plus its synthetic mechanism controls  
**Rule:** no universal “MindMap score”; every inference remains tied to the axis and benchmark that measures it

## 1. Analysis goals

The study asks four separable questions:

1. **Pre-reader governance:** does a context gate prevent forbidden or deleted evidence from entering the reader prompt without destroying useful evidence coverage?
2. **Representation:** under equal raw evidence and equivalent validators, does normalized typed memory differ materially from a complete generic event representation?
3. **Error-aware fallback:** does an independent raw-evidence verifier/fallback improve the safe utility frontier under natural and correlated extraction errors?
4. **External generalization:** do mechanism directions observed in the synthetic topology suite recur on the relevant public benchmark axes?

These are not collapsed into one omnibus accuracy claim.

---

## 2. Frozen comparison ladder

```text
B0   AlwaysNoMemory endpoint
B1a  raw BM25 -> context echo endpoint
B1b  raw BM25 -> shared frozen reader
B2   raw candidates -> pre-reader context gate -> same reader
B3   complete G-flat memory -> semantically matched gate -> same reader
B4   T-normalized memory -> semantically matched gate -> same reader
B5   T-normalized + independent raw verifier/fallback -> same reader
```

All comparisons freeze, where applicable:

```text
raw input and capability condition
checkpoint isolation mode
candidate retrieval budget
reader and tokenizer
prompt and output-token budget
decoding and seed
call/retry budget
opaque run-group mapping
hardware/runtime accounting
```

An extra verifier, repair, classifier, or model call is charged.

---

## 3. Statistical units

The question row is not automatically an independent observation.

### GateMem

Primary cluster: episode.  
Strata: domain, then query class within episode.

All checkpoints from one episode remain together in bootstrap/permutation resamples. The released `2,218` checkpoints are not treated as 2,218 independent samples.

### LoCoMo

Primary cluster: complete conversation/history unit. All questions derived from one conversation remain together.

### LongMemEval

Primary cluster: the shared underlying history/session group when multiple questions use the same history; otherwise the benchmark item. Category is retained as a stratum.

### NCM-Topo / synthetic Track X

For a fixed exhaustive fixture suite, report exact counts only. Do not attach population p-values to alpha-renamings or deterministic rendering variants. For a sampled or model-rendered extension, the independently generated scenario/topology is the cluster.

### Repeated model executions

Repeated seeds, opaque keys, or provider calls are technical replicates, not new benchmark samples. They estimate execution sensitivity and are never counted as independent test items.

---

## 4. GateMem task semantics

GateMem actions are:

```text
answer
answer_redacted
refuse
no_memory
```

`refuse` and `no_memory` can be correct task decisions. They are not generic uncertainty abstentions.

A selective method must emit a separate frozen field:

```json
{
  "selection": {
    "confidence": 0.0,
    "accepted": true,
    "threshold_version": "dev-frozen-v1"
  }
}
```

Do not reconstruct `accepted` from the action string.

Per-checkpoint governed success is:

```text
utility
  official utility correctness

privacy / expected refuse
  action correct AND no answer/context/e2e leak

privacy / expected answer_redacted
  action correct AND permitted content correct/complete AND no leak

safety/deletion
  action correct AND no answer/context/e2e leak
```

---

## 5. Primary hypotheses

The confirmatory family contains at most three comparisons. Their exact margins and thresholds are frozen on development data before test outcomes are inspected.

### H1 — pre-reader context gate

Comparison:

```text
B1b versus B2
```

Primary mechanism endpoint:

```text
privacy/deletion prompt-context leakage
```

Utility safeguard:

```text
complete permitted-evidence recall under the same prompt-token budget
```

The claim is supported only if B2 reduces context leakage and satisfies a preregistered noninferiority margin on permitted-evidence recall. A reader-only answer improvement cannot satisfy H1.

### H2 — complete generic versus normalized typed memory

Comparison:

```text
B3 versus B4
```

The default hypothesis is not intrinsic typed superiority. Use an equivalence/noninferiority formulation on the primary task endpoint when both receive equal information and equivalent invariants.

Possible conclusion classes:

```text
T superior
G superior
practically equivalent within frozen margin
inconclusive
```

If task outcomes are equivalent, compare implementation-specific secondary endpoints such as diagnostic localization, write amplification, storage, migration complexity, and operator effort without relabelling them as semantic accuracy.

### H3 — independent raw verification/fallback

Comparison:

```text
B4 versus B5
```

Primary subset:

```text
natural extractor-error cases plus preregistered ambiguous/conflicting cases
```

The claim is supported only if B5 improves safe utility or governed task success without violating the governance bound or exceeding the frozen cost/call budget.

### Familywise error

Apply Holm correction at familywise `alpha = 0.05` across H1–H3. Domain/category analyses and ablations are secondary unless separately preregistered.

---

## 6. GateMem operating point

For utility selection threshold `tau`:

```math
UtilityCoverage(\tau)=
\frac{accepted\ utility\ checkpoints}{all\ utility\ checkpoints}
```

```math
UtilityRisk(\tau)=
\frac{incorrect\ accepted\ utility\ checkpoints}
{accepted\ utility\ checkpoints}.
```

Governance is evaluated over all governed checkpoints, not only content-bearing responses:

```math
PrivacyE2ELeak=
\frac{privacy\ checkpoints\ with\ answer\ or\ context\ leakage}
{all\ privacy\ checkpoints}
```

```math
DeletionE2ELeak=
\frac{safety\ checkpoints\ with\ answer\ or\ context\ leakage}
{all\ safety\ checkpoints}.
```

```math
GovernedTaskSuccess=
\frac{successful\ privacy+safety\ checkpoints}
{all\ privacy+safety\ checkpoints}.
```

A development-selected lexicographic operating point may maximize utility coverage subject to:

```math
UtilityRisk(\tau)\le r_u,
```

```math
PrivacyE2ELeak\le r_p,
\quad
DeletionE2ELeak\le r_d,
```

```math
GovernedTaskSuccess\ge g_0.
```

Suggested starting values for development sensitivity, not automatically frozen confirmatory values:

```text
r_u = 0.05
r_p = 0.01
r_d = 0.01
```

`g_0` and all noninferiority margins require development-only justification. If no threshold satisfies the frozen constraints, report failure rather than relaxing them after test inspection.

---

## 7. Effect estimands

For method pair `A,B` and checkpoint metric `Y`, the paired cluster estimand is:

```math
\Delta=E_{cluster}[Y_A-Y_B].
```

For GateMem, report:

```text
per-domain effects
pre-registered equal-domain macro effect, if used
checkpoint-weighted micro effect as descriptive only
```

An equal-domain macro effect is:

```math
\Delta_{macro}=\frac{1}{4}\sum_{d=1}^{4}\Delta_d.
```

Do not introduce this aggregate after viewing domain results. Domain rows remain visible because domain heterogeneity is scientifically meaningful.

Across unrelated benchmarks, do not average raw metric values. An exploratory meta-analysis may use directionally aligned standardized paired effects, but it cannot support an axis that a benchmark does not measure and is never the primary endpoint.

---

## 8. Confidence intervals and tests

### Cluster bootstrap

Use at least 10,000 paired cluster resamples, stratified by preregistered benchmark/domain strata. Within a resampled cluster, retain every checkpoint and both methods.

Use percentile or BCa intervals; freeze the choice before final evaluation.

### Cluster permutation

For a paired sharp-null test, swap method labels at the cluster level, not per checkpoint. Use exact enumeration when feasible, otherwise a large frozen Monte Carlo permutation count.

### Rare/zero violations

For zero observed violations among `n` eligible checkpoints, report an exact or Wilson one-sided 95% upper bound. The approximation:

```math
Upper_{95}\approx\frac{3}{n}
```

is descriptive only. A point estimate of zero is not proof of zero deployment risk.

### Equivalence

For B3 versus B4, use two one-sided tests or a confidence-interval inclusion rule with a frozen practical-equivalence margin `epsilon`:

```math
-\epsilon < \Delta_{B4-B3} < \epsilon.
```

The margin is justified from development variance, minimum meaningful effect, and cost of errors; it is not selected to make the test pass.

---

## 9. Power and effective sample size

For clustered data with mean cluster size `m_bar` and intracluster correlation `rho`, use the design-effect diagnostic:

```math
DE=1+(\bar m-1)\rho,
```

```math
n_{effective}\approx\frac{n_{rows}}{DE}.
```

Final power analysis should simulate paired cluster outcomes using development-only estimates of:

```text
cluster sizes
within-cluster correlation
baseline event rates
paired discordance
category/domain composition
```

Do not claim power from the raw checkpoint count alone. If the number of independent histories/episodes is too small for a narrow margin, report wide intervals or an inconclusive result rather than treating within-history questions as independent.

---

## 10. Capability-factor analysis

For architecture `A` under capability condition `C`, let the endpoint be `M(A,C)`.

Architecture effect within condition:

```math
\Delta_{arch}^{C}=M(T,C)-M(G,C).
```

Capability effect within architecture:

```math
\Delta_{cap}^{A}=
M(A,C_{relationship})-M(A,C_{raw}).
```

Interaction:

```math
\Delta_{int}=
[M(T,C_{relationship})-M(T,C_{raw})]
-
[M(G,C_{relationship})-M(G,C_{raw})].
```

A large capability effect and small architecture effect means supplied information, not representation, dominated the result.

Report performance by identifiability stratum:

```text
raw-identifiable
relationship-dependent
ambiguous-even-native
annotation-leaky
```

Do not treat relationship-dependent failure as pure memory failure.

---

## 11. Checkpoint interference

For stateful methods, compute isolated and upstream-sequential predictions:

```math
InterferenceRate=
\frac{\#\{c:Canon(Pred_{isolated}(c))\neq Canon(Pred_{sequential}(c))\}}
{\#checkpoints}.
```

The primary comparison uses checkpoint-isolated replay or verified snapshot clone. Sequential compatibility is secondary.

A missing or crashed prediction is not converted into `refuse`, `no_memory`, or any other task action. Exact checkpoint coverage is a precondition for an accepted run.

---

## 12. Opaque-key sensitivity

Within technical replicate `r`, paired methods share one opaque key `K_r`.

Across fresh-key replicates, report:

```text
official summary equality
canonical semantic-prediction equality
paired-effect variation
artifact-hash changes expected from opaque audit IDs
```

Technical replicate variation does not enlarge the benchmark sample size.

---

## 13. Cost and efficiency

Report separately:

```text
input/output tokens
model and verifier calls
retries
retrieval candidates and prompt tokens
ingest/query p50 and p95 latency
bytes per raw turn/event
write amplification
storage footprint
benchmark-isolation replay overhead
monetary cost using dated prices
```

Avoid a primary scalar cost-quality score with arbitrary weights. Use:

```text
Pareto dominance
incremental cost per additional successful checkpoint
incremental cost per prevented governance violation
```

An incremental cost-effectiveness ratio is:

```math
ICER_{A,B}=\frac{Cost_A-Cost_B}{Success_A-Success_B},
```

reported only when the denominator is nonzero and the methods are otherwise comparable.

---

## 14. Missing data, failures, and exclusions

- Exact official checkpoint coverage is required.
- Missing, duplicate, or unexpected predictions invalidate the run unless an exclusion was preregistered and is reported in every method.
- Method exceptions remain execution failures, not abstentions.
- Retry limits are frozen and charged.
- No item is removed because a method or judge failed on it.
- Benchmark/source parse failures are retained in the flow report and stop confirmatory scoring when they change the eligible set.

Report a checkpoint flow:

```text
official loaded
eligible under frozen task contract
executed
predicted exactly once
officially scored
supplementally scored
excluded with preregistered reason
```

---

## 15. Calibration and threshold discipline

Selection thresholds, raw-fallback thresholds, gate uncertainty thresholds, and confidence mappings are tuned on development data only.

Report:

```text
Brier score
ECE with frozen bins or adaptive method selected before test
risk-coverage curve
threshold and threshold-version hash
fallback frequency
```

Never tune a threshold on final test results or choose among multiple reported operating points after seeing them.

---

## 16. Human and LLM judges

When an official or supplemental LLM judge is used, freeze:

```text
provider/model/revision
prompt hash
reasoning/verbosity settings
temperature and output budget
retry policy
input normalization
```

Calibrate on a blinded, preregistered human-reviewed subset with two independent annotators and adjudication. Report agreement, judge-human confusion, and a judge-model sensitivity analysis. Deterministic official metrics remain in their own namespace.

---

## 17. Correlated extraction-error analysis

Natural extractor errors on public raw inputs are primary.

The synthetic stress model is fitted on development errors only and freezes latent modes such as:

```text
entity collapse/split
temporal scope shift
speaker or witness swap
modality laundering
branch misassignment
policy/visibility loss
source-family split
correction/retraction cascade
```

Corruption is applied at the joint event hypothesis and propagated to dependent records. Report an amplification function:

```math
Amp_R(z,\rho)=\frac{R_z(\rho)-R_{clean}}{\rho}
```

for answer error, context leakage, cross-branch contamination, false consensus, and deletion residue. Independent field dropout is not the realism baseline.

---

## 18. Reporting classes

Every result is labelled as one of:

```text
fixed deterministic component audit
synthetic sampled/model-rendered experiment
public deterministic endpoint control
public fixed-model experiment
confirmatory held-out comparison
exploratory sensitivity/ablation
```

Each table states:

```text
unit and cluster
numerator/denominator
capability condition
checkpoint mode
model/reader/judge condition
cost budget
official versus supplemental namespace
confidence interval/test status
```

Null, equivalence, generic-favourable, and inconclusive results remain visible.

---

## 19. Falsification outcomes

The broad architecture claim is narrowed or rejected when:

1. B2 captures the utility-governance improvement and B3/B4 add no benefit after costs;
2. B3 and B4 are practically equivalent under equal information and validators;
3. B5 helps only synthetic/oracle corruption but not natural public errors;
4. apparent gains disappear under matched capability or checkpoint isolation;
5. governance improvements arise only from near-total utility refusal;
6. cross-benchmark directions fail to replicate on the axis each benchmark actually measures;
7. effect uncertainty is too wide for the preregistered practical margin.

A useful paper may therefore conclude that only a pre-reader context gate, bitemporal update, or independent raw verifier is necessary for a specific failure class rather than claiming that the entire MindMap stack wins universally.
