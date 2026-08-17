# Track X GateMem Official-Run Harness

**Status:** pre-outcome execution contract  
**Pinned upstream:** `rzhub/GateMem@603f9f4b4ba4b77f043c20f85687fa016fd720b0`  
**Benchmark result:** none in this document

## 1. Purpose

This harness connects the capability-reduced GateMem runner to a clean, pinned local checkout of GateMem and its unmodified official scorer. It is the final plumbing gate before exploratory external baseline runs.

It does not vendor or commit GateMem data. Episodes and checkpoints are read in place from the pinned checkout.

## 2. Checkout verification

Before any method call, the harness verifies:

```text
supported domain
required data and scorer files exist
Git HEAD exactly matches the preregistered 40-character commit
the tracked checkout is clean
SHA-256 of scorer, episodes, and checkpoints
```

A later upstream revision requires a new audit and an explicitly changed pin. `--allow-dirty-checkout` exists only for local debugging and must not be used in a confirmatory run.

## 3. Run path

```text
pinned episodes/checkpoints
  -> capability-reduced public stream
  -> one fresh method instance per episode
  -> exact checkpoint coverage
  -> scorer-facing predictions.jsonl
  -> unmodified official score_predictions.py
  -> official summary and per-checkpoint outputs
```

The method receives no hidden checkpoint labels, gold record catalog, `record_refs`, or `memory_ops` in the primary raw-language condition.

## 4. Result directory

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

Audit rows contain source/public hashes and removed path names, not complete source episodes or checkpoints. Predictions may contain method-generated answers or retrieved public-context excerpts, because those are required for official utility and context-leakage scoring. Result redistribution must therefore follow the benchmark's data terms even though the raw source files are not copied wholesale.

## 5. Metadata

`run_metadata.json` records:

```text
MindMap revision
GateMem expected and observed revision
tracked-dirty state
scorer/data hashes
method name and configuration
counts for episodes/checkpoints/predictions/audits
artifact hashes
official scorer command and output hashes
official aggregate summary
boundary flags
UTC creation time
```

The timestamp is descriptive. Scientific identity comes from revisions, method configuration, and hashes.

## 6. Official-score boundary

The scorer is invoked as:

```bash
python <pinned checkout>/bench/scripts/score_predictions.py \
  --data_dir <pinned checkout>/bench/data/<domain> \
  --predictions <result>/predictions.jsonl \
  --out_dir <result>/official_score
```

The optional official `--gate_by_action` mode must be declared in advance. The first deterministic baseline run should report both the default official score and, if desired, the action-gated result as a sensitivity analysis rather than choosing after inspection.

No LLM judge is enabled by this harness. A later judge run must pin judge provider/model/prompt, record all calls and costs, and manually calibrate a blinded subset.

## 7. CLI

```bash
python experiments/gatemem_external.py \
  --gatemem-checkout /path/to/GateMem \
  --domain medical \
  --method raw_lexical \
  --output-dir /tmp/gatemem-medical-raw
```

Available initial controls:

```text
raw_lexical
always_no_memory
```

For the raw lexical control, `top_k`, BM25 parameters, recency weight, and maximum answer length are written to metadata.

## 8. Required first external sequence

Run without changing code or data between methods:

```text
all four domains, always_no_memory
all four domains, raw_lexical with frozen defaults
```

The order of method execution should not affect results because each episode receives fresh state. Run directories remain separate and hash-addressed.

Report official domain-level metrics separately. Do not average domains into one memory score unless the aggregation rule is preregistered and all source metrics remain visible.

## 9. Interpretation

These runs establish only:

```text
official scorer compatibility
boundary and artifact integrity
zero-coverage and policy-unaware retrieval endpoints
external utility/governance behavior of those controls
```

They do not yet test G-flat versus T-normalized extraction, raw fallback, bitemporal consolidation, branch isolation beyond GateMem's task surface, or calibrated selective prediction.

## 10. Remaining confirmatory gates

- run the method in a filesystem/network sandbox rather than only a trusted subprocess;
- resolve GateMem dataset redistribution terms;
- freeze domain aggregation and action-gating policy;
- add token, memory-byte, and monetary cost accounting;
- add a raw+dense baseline;
- implement matched G-flat and T-normalized systems;
- freeze development thresholds before held-out evaluation;
- preserve official and supplemental metric namespaces.
