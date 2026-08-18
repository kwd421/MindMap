# Track X v0.1 — Leakage-Free Raw-Evidence Verifier Protocol

**Status:** frozen protocol candidate; no confirmatory outcomes inspected  
**Date:** 2026-08-17  
**Coordination gate:** Issue #7  
**Branch:** `research/track-x-v0.1-raw-verifier`

## 1. Deciding question

Track S and the fixed Track E audits show that complete generic and typed ledgers tie when they receive the same semantic events, validation rules, integrity witnesses, and repair policy. Track X therefore asks a different question:

> When a primary structured candidate is incomplete or wrong, can retained raw evidence support a separately implemented verifier that improves calibrated downstream reconstruction without creating excessive false corrections, unsafe disclosure, or cost?

This track does **not** test whether a typed schema is more expressive than a generic event ledger. Both downstream implementations receive the same accepted or corrected event.

## 2. Claim boundary

### In scope

- raw evidence rendered independently from the structured candidate;
- a primary candidate and verifier implemented as separate paths;
- verifier decisions `accept`, `correct`, `abstain`, or `reject`;
- clean candidates, corrupted candidates, missing candidates, and raw-unavailable controls;
- topology-family held-out evaluation;
- calibrated confidence and selective risk/coverage;
- downstream semantic reconstruction and unsafe disclosure;
- equal-information generic and typed downstream ledgers;
- fixed character/token/model-call budgets and exact cost reporting.

### Out of scope for v0.1

- public benchmark or production claims;
- claims about an unconstrained natural-language distribution;
- use of gold events, answer keys, injected-error labels, or recoverability labels by the primary extractor or verifier;
- paraphrase-level random splits presented as topology generalization;
- tuning thresholds after held-out outcomes are observed;
- treating repeated renderings of one topology as independent samples;
- inferential p-values for the fixed deterministic component audit;
- a typed-versus-generic semantic advantage claim.

## 3. Information firewall

The evaluator may hold the complete `RawCandidateCase`, including gold and error metadata. The verifier receives only a sanitized `VerifierInput`:

```text
VerifierInput(
  raw_text,
  candidate_event,
  context_events,
  insertion_index
)
```

The verifier interface contains no:

- case identifier;
- topology split;
- rendering family;
- gold event;
- expected answer;
- query;
- error mode;
- recoverability label.

The downstream query is applied only after the verifier has emitted its decision.

## 4. Frozen split unit

The split unit is the canonical topology family, never a row or paraphrase.

### Development topology families

```text
F01 branch_visibility
F02 mind_copy_without_world_fork
F03 world_fork_without_mind_copy
F04 unsynchronized_same_principal_replicas
F05 identity_fork_copy_attribution
F06 receive_accept_reject
F07 exposure_policy_lifecycle
```

### Held-out topology families

```text
F08 restore_manifest_gap
F09 cross_world_reference_context
F10 protected_only_revocation
F11 independent_public_survives
F12 same_origin_dedup
F13 authorized_replication
F14 temporal_negative_controls
```

No threshold, parser rule, or correction policy may be changed after held-out results are generated without creating a new versioned manifest.

## 5. Rendering families

Each manifest entry declares one rendering family:

- `explicit`: complete journal-style prose with named roles and times;
- `conversational`: quoted or dialogue-like evidence with the same underlying content;
- `elliptical`: concise operational prose with omitted grammatical material but no omitted answer-defining field.

Rendering code is separate from candidate mutation code. The raw text is always rendered from the gold event before any candidate mutation is applied.

## 6. Candidate conditions

Each topology entry produces the following fixed conditions:

1. `clean` — candidate equals the gold event;
2. `field_corruption` — one answer- or invariant-relevant field is changed;
3. `candidate_omitted` — raw evidence exists but the candidate event is absent;
4. `raw_unavailable` — the same field corruption is present and the raw evidence is withheld.

The verifier must infer disagreement from raw evidence and context. It is never told which condition is active.

## 7. Systems

### Structured-only

The unverified primary candidate is inserted as-is. A missing candidate remains missing.

### Raw verifier

The verifier emits:

```text
VerificationDecision(
  status,
  output_event,
  confidence,
  field_evidence,
  reason_codes
)
```

- `accept`: use the candidate unchanged;
- `correct`: use the corrected event;
- `abstain`: do not insert an event and do not answer from unverified structure;
- `reject`: quarantine the candidate and do not answer from it.

### Oracle-raw ceiling

The evaluator inserts the gold event. This is a ceiling only and is never described as a deployable verifier.

Each treatment is evaluated through both complete downstream ledgers, G and T, with the same event selected by the treatment.

## 8. Primary metrics

All metrics are reported by split and topology family before any aggregate.

### Event verification

- exact event reconstruction rate;
- field-level exact match;
- clean false-correction rate;
- corrupted false-accept rate;
- missing-candidate recovery rate;
- raw-unavailable abstention rate;
- correction precision;
- correction recall.

### Calibration and selective prediction

- Brier score for the decision being correct;
- expected calibration error with bins frozen in the manifest;
- risk at fixed coverage levels;
- coverage at fixed risk thresholds;
- abstention appropriateness for recoverable versus unrecoverable cases.

### Downstream safety and utility

- exact target-answer accuracy;
- generic/typed downstream disagreement count;
- unsafe disclosure rate: predicted `True` when the gold disclosure decision is `False`;
- false denial rate for disclosure;
- silent wrong-use rate;
- verifier-caused regression rate on clean candidates.

### Cost

- raw characters and tokens read;
- parser/model calls;
- corrected fields written;
- downstream recomputations;
- latency and monetary cost when a model-backed implementation is later added.

The deterministic v0.1 parser reports operation counts and text length only. These are not portable performance measurements.

## 9. Stop and falsification rules

The raw-verifier hypothesis is weakened or rejected if any of the following holds on held-out topology families:

- downstream safety does not improve over structured-only at matched coverage;
- clean false-correction exceeds the frozen limit;
- correction gains disappear after excluding oracle-recoverable templates;
- the verifier mainly converts wrong answers into confident wrong corrections;
- gains require query or gold metadata unavailable at deployment;
- improvements are confined to renderings seen during development;
- generic and typed downstream systems diverge because they did not receive the same selected event;
- verifier cost dominates the recovered safety/utility under the frozen budget.

## 10. Reporting rules

- Fixed deterministic cases use exact counts, not p-values.
- Repeated renderings are nested within topology family.
- Any later stochastic study resamples or models topology/scenario clusters, not individual questions.
- Oracle-raw results are displayed separately from non-oracle systems.
- Negative results, false corrections, and abstentions remain in committed per-case artifacts.
- No merge or protocol freeze is inferred from silence; Session A must explicitly accept, amend, or reject the protocol in Issue #7.