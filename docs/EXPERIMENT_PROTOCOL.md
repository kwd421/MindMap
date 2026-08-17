# NCM³-E Public Evaluation Protocol — Draft

## Research questions

1. Does separating actual acquisition from current read permission reduce false character knowledge and unintended disclosure while preserving useful answers?
2. Does worldline-scoped storage reduce contamination after branch switching or rollback?
3. Is the joint effect of epistemic projection and bitemporal state larger than either component alone?
4. Which errors originate in extraction, consolidation, retrieval, context assembly, or answer use?
5. When does repeated extraction help, and how is that benefit limited by correlated errors?

## Controlled systems

All systems use the same answer model, prompt, token budget, and decoding settings.

- full context
- recursive summary
- BM25
- dense retrieval
- lexical/dense fusion
- hierarchical event-turn retrieval
- graph or hypergraph memory
- bitemporal-only memory
- role-chain-only memory
- permission-only memory
- NCM³-E
- NCM³-E ablations for time, possession, permission, branch, provenance, retraction, and raw-evidence fallback

Where feasible, released implementations should be used instead of reconstructions from paper descriptions.

## Datasets

General memory:

- LoCoMo
- LongMemEval
- LoCoMo-Plus
- MemoryAgentBench
- HaluMem

Memory utilization:

- Mem2ActBench
- MemGym
- IFCMemoryBench, subject to release and license

Multi-principal and information-asymmetry evaluation:

- GateMem
- SOTOPIA-TOM
- released role-switching evaluations such as BEAM-SWITCH, when available

A role-playing extension should contain private/public channels, absent characters, hearsay, deliberate false claims, later corrections, identity forks, alternate timelines, memory sealing, branch conflicts, and explicit forget/rollback requests.

## Integrity controls

1. Split by conversation, user, scenario, or project, never by question alone.
2. Do not tune prompts, retrieval weights, or thresholds on the test set.
3. Record dataset repository, revision, path, SHA-256, license, and retrieval date.
4. Record exact answer, embedding, reranking, extraction, and judging model IDs.
5. Freeze prompts and scoring scripts before the final test.
6. Save query-level predictions, evidence IDs, token counts, latency, and failure labels.
7. Do not treat self-reported numbers from different papers as controlled head-to-head results.

## Four diagnostic conditions

**C0 — no memory:** current query only.

**C1 — gold evidence:** the answer model receives the annotated evidence. This estimates utilization ceiling.

**C2 — gold structure:** gold entity, time, branch, and role are supplied, but evidence must be retrieved. This isolates retrieval and state resolution.

**C3 — end to end:** raw interaction is ingested and all structure must be extracted.

Diagnostic gaps:

\[
G_{extract}=Score(C2)-Score(C3)
\]

\[
G_{retrieve}=Score(C1)-Score(C2)
\]

\[
G_{utilize}=Score_{max}-Score(C1)
\]

## Metrics

Answer and evidence:

- benchmark-native answer accuracy or F1
- Recall@k, Complete Evidence Recall@k, MRR, nDCG@k
- abstention precision, recall, and F1
- frozen LLM-judge score with a human-calibrated subset

Epistemic correctness:

- perspective accuracy
- false-knowledge rate: use of a fact the selected role never acquired
- source-attribution accuracy
- belief/truth separation accuracy

Governance:

- disallowed-disclosure rate
- hidden-memory-existence leakage rate
- deletion and revocation compliance
- legitimate-query utility under permission constraints

Branch and rollback:

- branch contamination rate
- rollback-consistent QA and summarization
- post-exposure noninterference between an exposed-then-restored agent and a never-exposed control

Efficiency:

- ingestion calls and tokens per turn
- retrieval and answer p50/p95 latency
- bytes per event and write amplification
- retrieved tokens per query
- logged monetary cost

## Statistical plan

1. Use paired bootstrap intervals over questions and cluster bootstrap intervals over conversations or scenarios.
2. Use McNemar's exact test for paired binary correctness.
3. Apply Holm correction across primary baseline comparisons.
4. Report raw counts, effect sizes, and confidence intervals.
5. Calibrate automated judges against at least 200 human-scored examples when the dataset is large enough.
6. Run at least three decoding seeds for stochastic systems.

For a paired binary comparison with discordant fraction 0.25, two-sided alpha 0.05, power 0.80, and target difference 5 percentage points:

\[
n\approx\frac{(1.96+0.84)^2(0.25)}{0.05^2}\approx784
\]

A 3-point difference under the same assumptions requires approximately 2,178 paired questions before allowing for clustering and multiple comparisons.

## Extraction-fault study

Measure field-level error and correlation for entity resolution, relation, valid time, transaction time, branch, acquisition audience, read permission, source identity, reliability, and correction/retraction links.

For independent binary error probability \(p\), three-pass majority has:

\[
p_{maj}=3p^2-2p^3
\]

This is a reference curve, not a deployment guarantee. The observed excess over this curve estimates the cost of correlated errors.

## Reporting rules

- Null and negative findings remain in the report.
- Graph retrieval is called useful only if it improves a preregistered subset or cost-adjusted total quality.
- Synthetic results are not described as public-benchmark state of the art.
- If governance improves while ordinary QA falls, report the trade-off frontier.
- If possession/permission separation only helps constructed cases, narrow the claim.

## Success targets

Targets are not forecasts.

- at least +5 percentage points on perspective-sensitive accuracy over the strongest controlled baseline;
- at least 50% relative reduction in disallowed disclosure and branch contamination;
- no more than 2 percentage points loss on ordinary factual QA;
- at least 40% fewer retrieved tokens than full context where full context is feasible;
- with measured 10% critical-field error, retain at least 85% of clean utility;
- post-exposure noninterference exact agreement above 90% on deterministic tasks.
