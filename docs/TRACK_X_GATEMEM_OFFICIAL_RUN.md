# Track X GateMem Official-Run Harness

**Status:** pre-outcome execution contract; opaque-firewall CI required  
**Pinned upstream:** `rzhub/GateMem@603f9f4b4ba4b77f043c20f85687fa016fd720b0`  
**Benchmark result:** none in this document

## 1. Purpose

This harness connects a capability-reduced GateMem runner to a clean, pinned local checkout of GateMem and its unmodified official scorer.

It does not vendor or commit GateMem data. Episodes and checkpoints are read in place from the pinned checkout.

No benchmark outcome is valid unless the v0.7 opaque method firewall is enabled and its source-ID, relationship-policy, chronology, RPC, and fresh-key invariance tests pass.

## 2. Checkout verification

Before any method call, the harness verifies:

```text
supported domain
required data and scorer files exist
Git HEAD exactly matches the preregistered 40-character commit
the tracked checkout is clean
SHA-256 of scorer, episodes, and checkpoints
```

A later upstream revision requires a new audit and an explicitly changed pin. `--allow-dirty-checkout` exists only for local debugging and must not be used in a reported run.

## 3. Opaque method boundary

The evaluator creates a fresh secret for every benchmark run and maps source identifiers into non-sequential HMAC surrogates:

```text
source episode ID    -> method episode ID
source principal ID  -> method principal ID
source turn ID       -> method turn ID
source checkpoint ID -> method query ID
```

The method receives only opaque identifiers. The secret and mapping are never passed to the method subprocess, prompt, prediction, or method audit and are never serialized. `run_metadata.json` records only key/mapping commitments and the mapping count.

The primary raw-language method capability excludes:

```text
source checkpoint / episode / turn / principal IDs
source as_of_turn_id or dataset turn position
entities.relationships policy annotations
future turns and checkpoints
gold records, record_refs, and memory_ops
query_type, attack_type, expected_action, judge_spec,
leak_targets, policy_snapshot, gold answers, and refusal labels
```

The evaluator retains source chronology outside the method boundary, ingests exactly through the source checkpoint's as-of turn, invokes the method with an opaque query object, and restores the official source checkpoint ID only after method return.

A method output containing a known source dataset identifier is a hard boundary failure rather than a scored prediction.

## 4. Run path

```text
pinned episodes/checkpoints
  -> evaluator-owned source chronology
  -> opaque capability-reduced public stream
  -> one fresh method instance per episode
  -> exact checkpoint coverage
  -> evaluator restores source checkpoint IDs
  -> scorer-facing predictions.jsonl
  -> unmodified official score_predictions.py
  -> official summary and per-checkpoint outputs
```

## 5. Result directory

The harness writes:

```text
predictions.jsonl
episode_audit.jsonl
turn_audit.jsonl
checkpoint_audit.jsonl
run_metadata.json
official_score/summary.json
official_score/per_checkpoint.jsonl
```

Audit rows are evaluator-owned and contain source IDs, hashes, counts, timings, and removed path names. They do not contain the source↔method mapping or complete source episodes/checkpoints. The method never reads the result directory.

Predictions may contain method-generated answers or exact prompt-context excerpts because the official utility and context-leakage scorers require them. Redistribution must follow GateMem's dataset terms.

## 6. Metadata

`run_metadata.json` records:

```text
MindMap revision
GateMem expected and observed revision
tracked-dirty state
scorer/data hashes
method name and configuration
counts for episodes/checkpoints/predictions/audits
opaque key and mapping commitments, never the secret/mapping
artifact hashes
official scorer command and output hashes
official aggregate summary
boundary flags
UTC creation time
```

The timestamp is descriptive. Scientific identity comes from revisions, configuration, hashes, and boundary commitments.

## 7. Official-score boundary

The scorer is invoked unmodified:

```bash
python <pinned checkout>/bench/scripts/score_predictions.py \
  --data_dir <pinned checkout>/bench/data/<domain> \
  --predictions <result>/predictions.jsonl \
  --out_dir <result>/official_score
```

The optional official `--gate_by_action` mode must be declared in advance. The first deterministic control run reports the default official score; action-gated output, when run, is a labelled sensitivity analysis rather than an outcome-selected replacement.

No LLM judge is enabled. A later judge run must pin provider/model/prompt, record calls and cost, and manually calibrate a blinded subset.

## 8. CLI

```bash
python experiments/gatemem_external.py \
  --gatemem-checkout /path/to/GateMem \
  --domain medical \
  --method raw_lexical \
  --output-dir /tmp/gatemem-medical-raw
```

Initial endpoint controls:

```text
always_no_memory     # zero-coverage safety edge
raw_lexical          # BM25 raw-context echo; no answer reader
```

The raw lexical control is explicitly **not** a capacity-matched QA baseline. It always echoes exact retrieved context when public turns exist and is used to expose the policy-unaware high-coverage/leakage endpoint. Prompt audit rows describe only the post-truncation text actually returned/scored, with source and prompt character spans and a context hash.

`top_k`, BM25 parameters, recency weight, and maximum context characters are written to metadata. The primary recency weight is zero.

## 9. Required first external sequence

Run without changing code or data between methods:

```text
all four domains, always_no_memory
all four domains, raw_lexical with frozen defaults
```

The order should not affect semantic predictions because each episode receives fresh state and opaque IDs never enter answer text. Run directories remain separate and hash-addressed.

Report official domain-level metrics separately. Do not average domains unless an aggregation rule is preregistered and every source metric remains visible.

## 10. Interpretation

These runs establish only:

```text
official scorer compatibility
opaque boundary and artifact integrity
zero-coverage and policy-unaware raw-context endpoints
external utility/governance behavior of those controls
```

They do not test a matched answer reader, G-flat versus T-normalized extraction, raw fallback, bitemporal consolidation, MindInstance lineage beyond GateMem's task surface, or calibrated selective prediction.

## 11. Remaining confirmatory gates

- run method code in a filesystem/network sandbox rather than only trusted subprocess isolation;
- resolve GateMem dataset/result redistribution terms;
- freeze domain aggregation and action-gating policy;
- add tokenizer-based context budget and token/call/cost accounting;
- add matched raw+dense retrieval and a shared answer reader;
- implement capacity/validator-matched G-flat and T-normalized systems;
- freeze development thresholds before held-out evaluation;
- preserve official and supplemental metric namespaces;
- add eligible-denominator safety metrics and source-span attribution outside the official namespace.
