# GateMem PR #46 Independent Reproduction Protocol

**Status:** exact external endpoint reproduction gate  
**Coordination:** Issue #4  
**Implementation under reproduction:** PR #46  
**Audit branch:** `research/gatemem-official-repro-audit`

## 1. Purpose

This branch independently reproduces the two deterministic GateMem endpoint
controls already produced by PR #46. It does not rediscover a command in the
older PR #43, implement a second BM25 runner, or extend the result into a
MindMap effectiveness claim.

The accepted target is:

```text
MindMap producing commit:
8fd14b3e631a8faeae46f2e73273a94c11a129f4

Reference result snapshot:
5e877bf5e4bfffda700ae0b8b5634bc734ac7e65

GateMem:
603f9f4b4ba4b77f043c20f85687fa016fd720b0

Official scorer SHA-256:
3d546a21778202959a9df12bac44c196a7f20a248cf5a2cb34f0d9b9c2623d8a
```

The reference snapshot is used only to obtain the committed eight-row endpoint
table. Its byte SHA-256 is frozen as:

```text
8d17aa6915f02e6abbc2f1c7b50410996ca354c2f177cec46c2cc5cfcd789212
```

## 2. Why PR #43 discovery was superseded

PR #43 introduced the raw lexical and always-no-memory agent classes, but it
does not expose the official all-domain execution CLI. PR #46 subsequently
added the protected official harness, opaque identity firewall, exact
post-budget prompt accounting, and this reviewed command:

```bash
python experiments/gatemem_external.py \
  --gatemem-checkout <PINNED_CHECKOUT> \
  --domain <medical|office|education|household> \
  --method <always_no_memory|raw_lexical> \
  --output-dir <NEW_OUTPUT_DIR>
```

Therefore the earlier heuristic PR #43 command discovery is retained only as a
historical failed interface probe. It is not evidence that a stable runner is
missing.

## 3. R0 — source, scorer, data, implementation and capability audit

R0 performs no endpoint interpretation. It must:

1. check out the exact MindMap producing commit;
2. check out the exact GateMem commit;
3. verify the official scorer hash;
4. verify 2,218 unique official checkpoint IDs across the four domains;
5. verify the frozen reference-row file hash;
6. run the producing commit's complete test suite;
7. inventory GateMem-related executable entry points;
8. scan capability-boundary code for review-sensitive field names.

Static name hits are review leads, not automatic leaks. Tests and evaluator
adapters legitimately mention hidden fields. The actual boundary is tested by
PR #46 and then exercised in R1.

## 4. R1 — exact official B0/B1a reproduction

R1 invokes only PR #46's reviewed CLI. It executes:

```text
4 domains
× 2 deterministic methods
× 2 fresh opaque-key replicates
= 16 official scorer runs
```

Methods:

```text
always_no_memory
  deterministic task-action endpoint
  zero utility, zero leakage, full utility over-refusal

raw_lexical
  policy-unaware BM25 raw-context echo endpoint
  no answer reader
  not a capacity-matched QA baseline
```

For every run, R1 requires:

- a new output directory;
- the exact GateMem revision and official scorer hash;
- the exact domain episode/checkpoint hashes;
- a clean producing implementation and benchmark checkout;
- the opaque identity firewall enabled;
- source IDs, relationships, `record_refs`, `memory_ops`, source as-of
  chronology, and hidden checkpoint fields absent from method capability;
- exactly one method prediction, normalized prediction, and official score row
  per checkpoint;
- the pinned official scorer filenames:
  `predictions.normalized.jsonl`, `scores.jsonl`, and `summary.json`;
- all official metrics and denominators equal to the frozen eight-row table.

R1 reports disagreement and fails closed if any value differs.

## 5. R1b — fresh-key repeatability

The two independent replicates must satisfy:

```text
official summaries equal:                    8/8
opaque key commitments changed:              8/8
opaque mapping commitments changed:          8/8
raw_lexical prediction hashes changed:       4/4
always_no_memory prediction hashes changed:  0/4
```

The raw lexical prediction artifacts change because protected method audits
retain opaque turn identifiers. The official metric summary must remain
invariant.

## 6. Publishable versus protected material

Protected endpoint output contains raw benchmark text in predictions and audit
records. It is never uploaded by this branch.

The workflow destroys the protected output tree after validation and uploads
only:

```text
STATUS.md
reproduction.json
repeatability.json
replicate_1_rows.csv
replicate_2_rows.csv
run_records.json
SHA256SUMS
execution logs that contain no prediction rows
```

The old `results/gatemem_official_audit/` folder records the superseded PR #43
probe. It is not the current result namespace and must not be cited as a
benchmark result.

## 7. Interpretation boundary

A successful R1 establishes only that the published PR #46 deterministic
endpoint controls are independently reproducible on the pinned official
benchmark.

It does not estimate:

- MindMap effectiveness;
- G-flat or T-normalized memory;
- policy/availability/provenance filtering;
- raw fallback;
- a shared answer reader;
- checkpoint-isolated stateful methods;
- native GateMem relationship-capability compatibility;
- a cross-domain aggregate effect.

The next causal comparison must use one frozen answer reader and matched
retrieval, token, call, retry, latency, and cost budgets across raw retrieval,
pre-reader governance filtering, G-flat, T-normalized, and any T+raw fallback
condition.

## 8. Workflow and provenance policy

The active workflows are:

```text
GateMem PR46 R0 source and boundary audit
GateMem PR46 R1 exact endpoint reproduction
```

The previous self-mutating persistence workflow is removed. CI artifacts and
Issue #4 checkpoints bind the audit source commit to the execution. After a
successful run, a reviewed publishable artifact may be committed manually
under a new result namespace; the workflow does not advance its own source
branch.

No approval, scientific acceptance, or merge is inferred from silence.
