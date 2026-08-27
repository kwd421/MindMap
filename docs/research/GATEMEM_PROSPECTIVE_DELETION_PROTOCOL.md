# Prospective deletion-speech and target-grounding protocol

**Protocol ID:** `GM-PD-001`  
**Version:** `0.1.0`  
**Machine record:** `EXP-20260828-011`  
**Status:** planned development design; no items generated, coded, or scored  
**Planning parent:** `93baef0acd022f1ae3e0251d1f1543fbedb1f3b4`  
**Planning freeze:** exact commit bound in the machine record after this file's freeze

## 1. Decision boundary

This protocol defines the minimum prospective evidence needed before changing
the PR #52 deletion parser in response to EXP-20260828-008/009. It is not a
confirmatory preregistration, a power calculation, an official GateMem run, or
permission to treat model-generated labels as human annotation.

Execution is blocked until two independent human coders and a separate
adjudicator are named in a private execution manifest. Until then, every model-
only result remains a development diagnostic and the parser-amendment gate is
closed.

## 2. Forbidden prior material

The confirmation population must exclude all 57 EXP-009 episode-turn
coordinates, all 55 exact current-turn text hashes, and their template
clusters. The exclusion manifest is derived only from committed coordinates
and hashes; protected raw text is not copied into this repository.

Disjointness is enforced at three levels before parser output is visible:

1. exact episode-turn coordinate;
2. normalized exact-text SHA-256;
3. a frozen template-cluster identifier produced by the item-authoring
   protocol.

Any collision invalidates the affected cluster. It is removed and replaced
before outcomes are inspected. A template cluster may appear in exactly one of
development or confirmation, never both.

## 3. Candidate design floor

The candidate floor is 420 independently identified item units: 14 cells with
30 items per cell. This is a balanced design floor, not a statistical power
justification. A binomial sensitivity or power analysis must be appended before
the study is promoted from planned development design to confirmatory work.

The seven speech-act families are crossed with `explicit_current_turn` and
`deictic_prior_context` target forms:

| Family | Intended operation | Role |
|---|---|---|
| information deletion | `DELETE` | positive |
| authorization revocation | `RESTRICT` | positive |
| physical/domain removal | `NONE` | adversarial negative |
| quoted deletion language | `NONE` | adversarial negative |
| negated deletion language | `NONE` | adversarial negative |
| hypothetical deletion language | `NONE` | adversarial negative |
| update-not-deletion | `NONE` | adversarial negative |

Each cell contains 10 development items and 20 sealed confirmation items:
140 development and 280 confirmation items in total. Split assignment is by
template cluster, not row. No percentage may be reported without the raw cell
numerator and denominator.

## 4. Item and gold schema

Every item contains a frozen episode context, current request, canonical
memory-object inventory, principal/role state, and expected operation. Positive
items carry a gold memory-object ID and a frozen target span or antecedent.
Negative items carry an explicit null target and require abstention from a
memory-governance operation.

Deictic items place the target antecedent only in prior context. Explicit items
contain the complete target in the current request. Items with multiple
plausible targets are invalid unless multi-target behavior is itself frozen in
a later protocol revision.

The candidate typed parser interface is evaluated as data, not supplied to
coders:

```text
operation: DELETE | RESTRICT | NONE
request_type: one of the seven frozen families
target_memory_object_ids: ordered tuple
target_spans: ordered tuple or frozen antecedent coordinates
abstention_reason: required when operation == NONE
```

The interface is a scoring contract. This protocol does not implement or
approve a parser amendment.

## 5. Blinded coding and adjudication

Two human coders independently label all 420 full rows. They are blinded to
parser outputs, intended design-cell labels, EXP-008/009 outcomes, each other's
labels, and confirmation results. Each coder manifest records request type,
operation, target ID/span or null, confidence, and a controlled note code.

Both manifests are hash-locked before comparison. Raw disagreements remain
retained. A separate adjudicator sees both locked manifests only after the
pre-adjudication agreement report is written. Adjudication may resolve gold;
it may not erase disagreement counts.

Before any parser development starts, development-set agreement must reach:

- Cohen's kappa at least `0.80` for request type and operation;
- exact target-ID/span agreement at least `0.90` on positive rows;
- manifest structural validation 100% for both coders.

If a threshold fails, the codebook is revised and every affected template
cluster is replaced or recoded under a new version. The failure and discarded
hashes remain in the deviation log. Confirmation labels stay sealed.

## 6. Development and confirmation gates

Parser changes may use only the 140 adjudicated development rows. After the
parser revision, typed-output schema, scorer, dependency lock, and analysis
script are frozen, the 280 confirmation rows are evaluated exactly once.

The prespecified confirmation gates are count based:

- each of four positive family-by-grounding cells: correct operation at least
  18/20 and exact target grounding at least 18/20;
- each of ten negative family-by-grounding cells: correct `NONE` abstention at
  least 19/20;
- no aggregate or macro average can override a failed cell;
- exact binomial 95% intervals and all 14 cell counts are reported, but the
  count gates, not interval fishing, determine pass/fail.

Secondary outcomes are macro operation accuracy, positive-cell target accuracy,
negative false-operation rate, confidence calibration, and explicit/deictic
paired differences. If inferential comparisons are later introduced, their
family and correction rule must be frozen before confirmation access.

## 7. Stopping, leakage, and claim boundary

Stop before item creation if human roles, protected retention, or the template
disjointness checker is unavailable. Stop before development if coder agreement
fails. Stop before confirmation if the parser, scorer, or artifact hashes are
not frozen. During confirmation, fail closed on any missing row, schema error,
hash mismatch, retry, or label exposure; do not repair and resume silently.

Passing this protocol would support only deletion-speech operation
classification and exact target grounding on the frozen independently coded
synthetic set. It would not be an official GateMem score or evidence of durable
state mutation, reader suppression, restart persistence, backup/cache removal,
or physical erasure. Those require separate official-scorer and lifecycle
experiments.
