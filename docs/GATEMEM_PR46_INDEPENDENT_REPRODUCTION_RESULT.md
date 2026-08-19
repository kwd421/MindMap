# GateMem PR #46 Independent Endpoint Reproduction

**Status:** accepted deterministic endpoint-control reproduction  
**Classification:** official GateMem B0/B1a controls only; not an architecture-effect result  
**Workflow run:** `32272755237`  
**Workflow artifact:** `9372852830`  
**Artifact ZIP SHA-256:** `ae4e2734468b8020885ee0da2c4cc26c3fa8b601b48cf936b748506d04cf1f8c`

## Frozen provenance

```text
Independent audit source:
0a4173a4bdf96fd51578ea17121f27de45029917

MindMap producing implementation:
8fd14b3e631a8faeae46f2e73273a94c11a129f4

Reference result snapshot:
5e877bf5e4bfffda700ae0b8b5634bc734ac7e65

GateMem:
603f9f4b4ba4b77f043c20f85687fa016fd720b0

Official scoring entrypoint:
bench/scripts/score_predictions.py

Official scoring entrypoint SHA-256:
3d546a21778202959a9df12bac44c196a7f20a248cf5a2cb34f0d9b9c2623d8a

Frozen reference rows SHA-256:
8d17aa6915f02e6abbc2f1c7b50410996ca354c2f177cec46c2cc5cfcd789212
```

The hash above binds the official scoring **entrypoint**, not
`bench/eval/scorer.py`. The earlier audit briefly hashed the latter path; that
run was rejected before result acceptance. The successful R0 and R1 use the
same entrypoint that PR #46 records in `run_metadata.json`.

## Execution

The independent workflow checked out the exact producing implementation and
GateMem revision in clean detached worktrees. It then required:

```text
independent reproduction tests:  2 passed
producing-commit suite:          67 passed

4 domains
× 2 deterministic methods
× 2 fresh opaque-key replicates
= 16 official scorer runs
```

Methods:

```text
always_no_memory
  zero-utility / zero-leakage endpoint
  emits the GateMem no_memory task action at every checkpoint

raw_lexical
  policy-unaware BM25 raw-context echo endpoint
  no answer reader and no policy filter
```

Each run was required to produce one method prediction, normalized prediction,
and official score row per checkpoint; to use the pinned official scorer
filenames; to match the frozen domain data hashes; and to preserve the opaque
method boundary.

## Exact reproduction checks

```text
official checkpoints:                         2,218
reference endpoint-row comparisons equal:     16/16
official summaries equal across fresh keys:    8/8
opaque key commitments changed:                8/8
opaque mapping commitments changed:            8/8
raw_lexical prediction hashes changed:          4/4
always_no_memory prediction hashes changed:     0/4
```

The raw lexical prediction files change because the protected audit contains
fresh opaque method identifiers. The official aggregate summaries remain
identical. Always-no-memory predictions contain no method-facing opaque memory
identifiers and therefore remain byte-identical.

## Official endpoint rows

Percentages below are display conversions of the exact committed decimal rows.
The CSV files remain authoritative.

| Domain | Endpoint | Checkpoints | Utility accuracy | Privacy e2e leakage | Deletion e2e leakage | Utility over-refusal | Compliance utility |
|---|---|---:|---:|---:|---:|---:|---:|
| Education | `always_no_memory` | 540 | 0.00% | 0.00% | 0.00% | 100.00% | 0.00% |
| Education | `raw_lexical` | 540 | 26.67% | 53.89% | 88.89% | 0.00% | 1.37% |
| Household | `always_no_memory` | 552 | 0.00% | 0.00% | 0.00% | 100.00% | 0.00% |
| Household | `raw_lexical` | 552 | 34.78% | 68.48% | 82.61% | 0.00% | 1.91% |
| Medical | `always_no_memory` | 579 | 0.00% | 0.00% | 0.00% | 100.00% | 0.00% |
| Medical | `raw_lexical` | 579 | 57.62% | 69.79% | 70.62% | 0.00% | 5.11% |
| Office | `always_no_memory` | 547 | 0.00% | 0.00% | 0.00% | 100.00% | 0.00% |
| Office | `raw_lexical` | 547 | 66.23% | 88.89% | 93.69% | 0.00% | 0.46% |

For these two degenerate controls, action accuracy is a class-prevalence sanity
check rather than evidence of action understanding:

```text
always_no_memory action accuracy = safety/no_memory prevalence
raw_lexical action accuracy      = utility/answer prevalence
```

It remains in the exact rows but should not be used as the headline metric.

## Public/protected artifact boundary

The independent workflow deliberately did not upload the protected prediction
or prompt-context tree. Before upload it deleted all raw predictions and raw
benchmark-text audits.

The downloaded artifact was independently inspected after the run:

```text
portable workflow SHA256SUMS verification:  6/6 OK
endpoint stdout logs:                       16/16 matched the six-field allowlist
endpoint stderr logs:                       16/16 empty
sensitive field-name scan:                  zero matches
protected output directory:                 absent
```

The only endpoint stdout fields were:

```text
output_dir
predictions
gatemem_commit
run_metadata_sha256
official_score_return_code
official_summary_sha256
```

The aggregate bundle committed here contains no source checkpoint, episode,
turn, principal, prompt, answer, relationship, `record_refs`, or `memory_ops`
values.

## Interpretation

The reproduced result establishes two external controls:

1. blanket `no_memory` is safe under the official leakage metrics but has zero
   utility and 100% utility over-refusal;
2. policy-unaware raw lexical retrieval recovers some required-pattern coverage
   but exposes severe privacy and deleted-memory leakage in every domain.

The result does **not** estimate:

- MindMap effectiveness;
- G-flat or T-normalized memory;
- pre-reader governance filtering;
- raw fallback;
- a shared answer reader;
- checkpoint-isolated stateful methods;
- native GateMem relationship-capability compatibility;
- a pooled cross-domain architecture effect.

No LLM judge, API key, action gating, model call, or inferential statistical test
was used. The two replicates are technical reproducibility checks, not
independent scientific samples.

## Next valid comparison

The next causal comparison must use one frozen answer reader and matched public
inputs, retrieval candidates, context-token budget, model calls, retries,
latency accounting, and monetary cost across:

```text
B1b  raw BM25 context -> shared reader
B2   raw candidates -> pre-reader governance filter -> shared reader
B3   G-flat memory -> same filter and reader
B4   T-normalized memory -> same filter and reader
B5   T-normalized + preregistered raw fallback -> same reader
```

Because prompt-context leakage is already counted end to end, changing only the
reader cannot erase forbidden text previously inserted into its context.

## Durable result namespace

The committed result namespace contains:

```text
STATUS.md
SHA256SUMS
WORKFLOW_PAYLOAD_SHA256SUMS
repeatability.json
replicate_1_rows.csv
replicate_2_rows.csv
run_commitments.csv
summary.json
```

`run_commitments.csv` preserves every prediction, opaque-key, opaque-mapping,
run-metadata, official-summary, episode, and checkpoint hash from all 16 runs.
`WORKFLOW_PAYLOAD_SHA256SUMS` binds the workflow artifact's full
`reproduction.json` and `run_records.json` without duplicating those verbose
files in Git. The workflow artifact ZIP SHA-256 binds the complete downloaded
archive.

Run `sha256sum -c SHA256SUMS` from the committed result directory to verify all
seven durable payload files. `SHA256SUMS` is intentionally not self-hashed.
