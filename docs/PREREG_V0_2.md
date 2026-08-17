# PREREG_V0_2 — NCM-Ψ / MindMapBench

## Registered claim

Under equal raw source evidence, extraction budget, reader model, and evidence-token budget, an explicit perspective × branch × bitemporal entitlement model will reduce false character knowledge, misinformation adoption, unauthorized disclosure, and unresolved-merge collapse relative to a scoped bitemporal slot store.

The term **Neural Cloud** is a system metaphor. The paper claim is not that hierarchical memory, temporal graphs, provenance, or version control are individually novel.

## Minimal durable schema

### EvidenceEvent

```text
event_id
raw_payload
source_span
speaker
witnesses/acquirers
valid_from
valid_to
recorded_at
branch_id
visibility_policy
integrity_hash
extractor_version
```

### ClaimRevision

```text
claim_id
revision_id
subject
predicate
object
modality
holder
valid_from
valid_to
recorded_at
branch_id
source_event_ids
derives_from_ids
supersedes_id
joint_hypothesis_id
calibrated_mass
```

Working, episodic, profile, graph, and snapshot representations are derived views or indexes until an ablation demonstrates that a separately writable physical hierarchy improves cost-adjusted performance.

## Non-negotiable distinctions

For proposition `phi`:

```text
WORLD(phi, branch, valid_time)
BELIEF(principal, phi, branch, valid_time, recorded_at)
DISCLOSE(requester, phi, branch, recorded_at)
```

These labels must not be collapsed into one answer target.

`recorded_at` is immutable database/system ingestion time. Mention time is not transaction time.

## Track A — oracle component study

Input may contain gold structured records. Results must be labelled an oracle or mechanism ceiling.

Baselines:

1. scoped latest slot;
2. modality without lineage;
3. lineage without modality;
4. modality plus lineage;
5. optional routed graph expansion only after the typed-ledger result is frozen.

Primary endpoint:

> Macro exact accuracy over world, belief, and disclosure queries, counting a protected disclosure or collapsed unresolved merge as wrong.

Secondary metrics:

- world-state accuracy;
- belief/perspective accuracy;
- disclosure accuracy;
- unauthorized-disclosure rate;
- merge-conflict accuracy;
- misinformation-adoption rate;
- transaction-time projection accuracy;
- latency, bytes/event, and write amplification.

## Track B — end to end

Each system receives only raw dialogue and raw questions.

Controlled constants:

- conversation-level train/validation/test split;
- extractor model, prompt, decoding, retries, and call budget;
- embedder and index-refresh policy;
- reader model and prompt;
- evidence-token budget;
- routing budget;
- ingestion and query hardware;
- judge and scoring scripts.

No answer-defining question type, canonical entity, predicate, current-state flag, trust label, or branch answer may be exposed at inference.

## Four diagnostic conditions

- C0: no memory;
- C1: gold evidence to the reader;
- C2: gold structure, system retrieval;
- C3: raw input end to end.

```text
Extraction gap = C2 - C3
Retrieval/state gap = C1 - C2
Reader-utilization gap = maximum - C1
```

## Factorial benchmark pilot

The frozen v0.1 mechanism pilot uses 200 scenarios selected for complete pairwise coverage across:

- direct / hearsay / no-access perspective;
- stable / explicit-correction / implicit-invalidation time;
- common / divergent / attempted-merge branch;
- reliable / mistaken / deceptive source;
- public / private / revoked disclosure;
- no derivation / same-policy duplicate / policy-laundered derivation.

Each scenario has world, belief, disclosure, and historical-transaction queries.

The generated pilot is not the final test set. Its purpose is to reject unnecessary primitives and locate component interactions before paying for end-to-end inference.

## Correlated extraction faults

Errors are sampled as joint event hypotheses rather than independent field deletion.

Registered modes:

- wrong entity/value;
- branch swap;
- holder/witness swap;
- modality laundering;
- visibility widening;
- transaction-time shift;
- lineage break;
- reliability inversion.

Report the entire utility/safety curve. A system that preserves answer accuracy by leaking protected information is not robust.

## Statistical plan

- paired query-level McNemar exact test;
- scenario/conversation-cluster bootstrap confidence intervals;
- Holm correction across primary baseline comparisons;
- effect sizes and raw discordant counts;
- ten synthetic dataset seeds for the pilot;
- at least three decoding seeds for stochastic end-to-end systems;
- human calibration of automated judges.

The public final test requires enough independent questions to detect the preregistered minimum effect. A 3-point target will be recomputed from pilot discordance and conversation clustering before test execution.

## Stop conditions

NCM-Ψ must be narrowed or rejected if:

1. scoped slots match it under the same non-oracle extractor;
2. lineage fails to improve disclosure/retraction outcomes;
3. its advantage disappears under empirically measured extraction errors;
4. graph expansion fails to improve the preregistered multi-hop subset;
5. reader utilization, not memory selection, dominates the remaining error;
6. the new benchmark does not alter system rankings relative to ordinary QA.

## Current pilot status

The first mechanism pilot is complete. See:

- `experiments/entitlement_lineage_pilot.py`
- `results/entitlement_lineage_*`
- `results/ENTITLEMENT_PILOT_REPORT.md`

Its clean result is a conformance study and is not the final Track B evidence.
