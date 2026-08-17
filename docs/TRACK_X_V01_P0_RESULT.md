# Track X v0.1 — Leakage-Free Raw-Verifier P0 Result

**Status:** fixed deterministic component audit; cross-session review required  
**Manifest:** `track-x-v0.1-manifest-2`  
**Date:** 2026-08-17  
**Pull request:** #38

## 1. Question

Track S and Track E showed that complete generic and typed ledgers tie when they receive the same semantic events, validation rules, integrity witnesses, and repair policy. Track X asks a different question:

> Can retained raw evidence support a separately implemented verifier that corrects or rejects a damaged structured candidate without reading gold events, answer keys, queries, split labels, or injected-error labels?

This P0 tests the information firewall, fixed treatment comparison, downstream safety plumbing, and deterministic reproducibility. It is not an unrestricted natural-language or learned-verifier result.

## 2. Fixed design

The suite contains 14 canonical topology families, split at the family level:

```text
7 development topology families
7 held-out topology families
```

Each family contributes four conditions:

```text
clean candidate
one field corruption
candidate omitted while raw evidence survives
field corruption while raw evidence is unavailable
```

Total:

```text
14 topology families × 4 conditions = 56 verifier cases
56 cases × 3 treatments × 2 downstream ledgers = 336 downstream rows
```

The verifier receives only:

```text
raw_text
candidate_event
context_events
insertion_index
```

It does not receive the case ID, topology/split metadata, rendering family, gold event, query, expected answer, condition, mutated field, or recoverability label.

Treatments are:

- `structured_only` — use the primary candidate without raw verification;
- `raw_verifier` — accept, correct, abstain, or reject using the sanitized input;
- `oracle_raw_ceiling` — insert the gold event as a non-deployable ceiling.

Each selected event is evaluated through both the complete generic and typed canonical ledgers.

## 3. Fixed verifier result

Across all 56 cases:

```text
decision correct:                   56/56
covered with accept/correct:        42/56 = 75.00%
exact event reconstruction:         42/56 = 75.00%
selective risk among covered:        0/42 = 0.00%
clean false correction:              0/14 = 0.00%
corrupted candidate false accept:    0/14 = 0.00%
omitted candidate recovered:        14/14 = 100.00%
raw-unavailable case abstained:      14/14 = 100.00%
```

The same pattern holds separately in development and held-out topology families:

```text
21/28 covered
7/28 abstained
0 covered reconstruction errors
```

The confidence values are fixed by rendering family. The covered-case Brier scores are therefore implementation diagnostics, not evidence of empirical calibration:

```text
development: 0.0103428571
held-out:    0.0117142857
overall:     0.0110285714
```

## 4. Downstream result

Per split and per downstream architecture, each treatment has 28 rows.

### Development topology families

| Treatment | Correct | Abstain | Silent wrong | Unsafe disclosure |
|---|---:|---:|---:|---:|
| Structured only | 7/28 | 0/28 | 21/28 | 0/28 |
| Raw verifier | 21/28 | 7/28 | 0/28 | 0/28 |
| Oracle raw ceiling | 28/28 | 0/28 | 0/28 | 0/28 |

### Held-out topology families

| Treatment | Correct | Abstain | Silent wrong | Unsafe disclosure |
|---|---:|---:|---:|---:|
| Structured only | 7/28 | 0/28 | 21/28 | 3/28 |
| Raw verifier | 21/28 | 7/28 | 0/28 | 0/28 |
| Oracle raw ceiling | 28/28 | 0/28 | 0/28 | 0/28 |

The generic and typed downstream ledgers produced no treatment-level outcome disagreement.

## 5. Interpretation

The P0 supports four narrow conclusions.

1. The information firewall is implementable: verifier code can be denied evaluator-only labels at the type/interface boundary.
2. When raw text is a lossless rendering of the gold event, a separate parser can recover candidate fields that were corrupted or omitted.
3. When raw evidence is absent, abstention prevents silent use but necessarily reduces coverage.
4. Once the verifier selects the same event, complete generic and typed ledgers again tie downstream.

The structured-only 25% accuracy is largely induced by the four-condition construction: only the clean quarter has the exact event. It is not an estimate of ordinary structured-memory accuracy. Likewise, the raw-verifier result is a controlled recovery ceiling for the fixed templates, not an expected production gain.

## 6. Protocol correction before result acceptance

The first CI attempt used held-out F09 event `F09.a`. Its raw template omitted `destination_placement_id`, so a clean candidate could not be reconstructed byte-for-byte. CI correctly failed the clean false-correction test.

No result from that attempt is accepted.

The manifest was corrected to select information-complete F09 event `F09.xb`, and the version was advanced to `track-x-v0.1-manifest-2`. The accepted result is generated only from manifest 2. This correction changes the test contract, not an outcome threshold, and is recorded rather than silently overwritten.

## 7. Limitations

- Raw evidence and parser use paired, deterministic, invertible templates.
- Topology families are held out, but the underlying event-type grammar is not held out.
- There is no learned model, free-form dialogue, OCR, speech, multilingual variation, or adversarial prose.
- Corruptions are single-field or complete candidate omission and are deliberately recoverable when raw text is present.
- Primary-candidate and verifier failures are not yet independently sampled or correlated.
- Confidence values are assigned by template family rather than fitted and externally calibrated.
- One selected event/query pair represents each topology family.
- The suite does not measure latency, monetary cost, human correction effort, or production-scale storage.
- Fixed cases receive exact counts only; no population inference follows.

## 8. Next deciding experiment

A valid Track X v0.2 should replace the invertible-template ceiling with a genuinely independent held-out raw-evidence path:

1. freeze human-written or separately model-rendered raw passages before parser evaluation;
2. keep topology families and rendering authors separated across development and held-out sets;
3. implement primary extractor and verifier as independently specified paths;
4. inject correlated ambiguity, omission, contradiction, misleading context, and raw-unavailable cases;
5. tune thresholds only on development topologies;
6. report reliability diagrams, risk-coverage curves, clean false correction, downstream unsafe disclosure, tokens/calls/latency, and cost;
7. retain structured-only, raw-verifier, and oracle ceiling as separate systems;
8. continue feeding the same selected event to complete G and T downstream implementations.

The next claim is falsified if the non-oracle verifier cannot improve held-out downstream safety at matched coverage without excessive clean false corrections or cost.

## 9. Reproduction

```bash
python experiments/track_x_v01.py --output-dir results/track_x_v01
python -m pytest -q
```

Committed deterministic artifacts:

- `verification_rows.csv`;
- six `split × treatment` downstream row files;
- `summary.json`;
- `run_metadata.json` with SHA-256 hashes.

CI regenerates all deterministic files into `/tmp`, diffs them against the committed results, and uploads the full run artifact.