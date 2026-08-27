# Track X v0.2 — Independently Authored Raw-Passage Protocol

**Status:** development implementation freeze candidate; Session A held-out passages not yet supplied  
**Base:** PR #38 / `track-x-v0.1-manifest-2`  
**Branch:** `research/track-x-v0.2-independent-raw`  
**Coordination:** Issue #7

## 1. Research question

Track X v0.1 used invertible raw templates. Track X v0.2 asks:

> After the primary extractor and verifier policy are frozen on Session-B-authored development passages, can an independent verifier improve downstream safety and selective accuracy on Session-A-authored held-out passages whose wording and ambiguity were not visible during implementation?

The passages remain synthetic and topology-scoped, but their prose is authored independently from parser/verifier code.

## 2. Cross-session ownership

### Session B owns and freezes

- protocol, bundle schema, and validation;
- development passages for F01–F07;
- primary extractor and independent verifier;
- thresholds, budgets, evaluator, tests, and CI;
- files under `src/mindmap/track_x/v02_*`, `tests/test_track_x_v02.py`, and `data/track_x_v02/development/**`.

### Session A owns only

```text
data/track_x_v02/heldout/session_a.json
data/track_x_v02/heldout/AUTHORSHIP.md
```

Session A must not alter parser/verifier code, thresholds, development passages, evaluator, tests, protocol, or freeze metadata in the held-out authorship commit.

## 3. Freeze and evaluation sequence

1. Session B freezes development code/data/tests and records the aggregate commit and CI run in `data/track_x_v02/FREEZE_V02.json`.
2. Session B posts a marked handoff in Issue #7.
3. Session A branches from the freeze declaration commit and writes the two allowed held-out files.
4. Session A posts `ACCEPT WITH PASSAGE CONTRIBUTION`, branch, and commit.
5. Session B verifies that no frozen path changed.
6. Session B runs held-out evaluation without changing parser/verifier rules, thresholds, or treatment definitions.
7. Any post-result parser, threshold, or treatment change creates Track X v0.3 and cannot overwrite v0.2.

## 4. Frozen topology split

### Development — Session B

```text
F01 branch_visibility
F02 mind_copy_without_world_fork
F03 world_fork_without_mind_copy
F04 unsynchronized_same_principal_replicas
F05 identity_fork_copy_attribution
F06 receive_accept_reject
F07 exposure_policy_lifecycle
```

### Held-out — Session A

```text
F08 restore_manifest_gap
F09 cross_world_reference_context
F10 protected_only_revocation
F11 independent_public_survives
F12 same_origin_dedup
F13 authorized_replication
F14 temporal_negative_controls
```

No topology family crosses the split.

## 5. Compact authored-passage bundle

Each JSON file contains seven bundles. Development example:

```text
data/track_x_v02/development/session_b.json
```

Each bundle contains:

```text
RawPassageBundle(
  bundle_id,
  fixture_id,
  topology_family,
  event_id,
  query_id,
  author_session,
  complete_text,
  ambiguous_text,
  distractor_passages,
  candidate_mutation,
  notes
)
```

The evaluator expands each bundle into six raw-passage conditions:

1. `clean` — complete passage;
2. `field_corruption` — complete passage paired with one controlled candidate-field error;
3. `candidate_omitted` — complete passage paired with no controlled candidate;
4. `raw_unavailable` — controlled corrupted candidate with no raw passage;
5. `ambiguous_raw` — passage omits one material field, so abstention is correct;
6. `misleading_context` — complete selected passage plus a nearby distractor supporting the controlled candidate error.

Condition and mutation metadata are evaluator instructions. They are never included in primary-extractor or verifier input.

## 6. Information firewall

The primary extractor receives only the selected raw passage.

The verifier receives only:

```text
raw_text
context_passages
candidate_event
context_events
insertion_index
```

Neither path can access:

```text
bundle or passage ID
topology or split
gold event
query or expected answer
condition or candidate mutation
recoverability label
other path's parser trace or field confidence
```

Forbidden held-out data fields include:

```text
gold_event
expected_answer
answer
recoverable_from_raw
corrected_event
verification_status
confidence
unsafe_disclosure
```

## 7. Passage-writing requirements

Each complete passage must:

- be manually written rather than emitted by the v0.1 renderer;
- preserve every event field needed for exact reconstruction;
- avoid v0.1 template sentence structure;
- use natural narrative, dialogue, log, operator-note, or indirect-report form;
- state world, instance, source, timing, and policy scope when material;
- avoid explicit schema labels such as `about_world_branch_id=`;
- remain within the frozen character budget.

Each ambiguous passage intentionally omits one material field. Each bundle includes at least one misleading but non-authoritative nearby passage.

## 8. Independent primary and verifier paths

The primary extractor reads the selected raw passage without a candidate. The verifier reads raw passage plus candidate and context. They do not call the same event-specific parser, share event-specific regexes, or expose primary internal state.

Shared utilities are limited to orthographic normalization and primitive token/date handling.

Frozen verifier actions:

```text
complete raw supports candidate       -> accept
complete raw conflicts with candidate -> correct
complete raw and candidate missing    -> correct
raw unavailable                       -> abstain
material raw field ambiguous          -> abstain
candidate event identity conflict     -> reject
```

## 9. Two separate evaluation tracks

Track X v0.2 explicitly separates the deployable end-to-end path from the controlled mechanism audit.

### A. End-to-end primary path — primary comparison

```text
primary_extractor_only
primary_plus_verifier
oracle_raw_ceiling
```

`primary_extractor_only` uses exactly the event emitted by the independent primary extractor. When no event is emitted, it abstains. `primary_plus_verifier` gives that same primary event to the independent verifier. It does not substitute a gold-derived controlled candidate.

This is the primary held-out comparison.

### B. Controlled candidate path — secondary mechanism audit

```text
controlled_candidate_only
controlled_plus_verifier
oracle_raw_ceiling
```

The evaluator constructs a controlled exact, corrupted, or omitted candidate from the canonical fixture according to condition metadata. This isolates correction and omission behavior even when the primary extractor fails to parse the passage.

Controlled-path gains cannot be presented as end-to-end extractor gains.

## 10. Correlated-failure cases

Held-out authors should include wording where primary and verifier may fail together:

- ambiguous pronoun or source identity;
- implicit world branch with a conflicting distractor;
- system time and valid time in reversed order;
- cross-sentence negation or revocation scope;
- omitted source family or authorization;
- a nearby passage repeating the corrupted candidate;
- unavailable raw evidence.

The verifier is not assumed to be an independent perfect rescue channel.

## 11. Frozen budgets

`FREEZE_V02.json` records:

```text
max raw characters:     1200
max context passages:      3
max context characters: 1800
primary calls:              1
verifier calls:             1
```

No held-out result is valid after changing these budgets or frozen parser/verifier code.

## 12. Endpoints

### Primary

Held-out unsafe-use rate at matched non-abstained coverage for:

```text
primary_extractor_only
primary_plus_verifier
```

where:

```text
unsafe use = silent wrong answer OR unauthorized disclosure
```

The oracle ceiling is shown separately. The same selected event is given to complete generic and typed downstream ledgers; they are expected to agree.

### Secondary

- controlled-candidate correction and omission recovery;
- event and field exact match;
- clean false-correction and corrupted false-accept rates;
- appropriate abstention on ambiguous/raw-unavailable passages;
- correction precision/recall;
- Brier score, ECE, and risk-coverage;
- downstream answer accuracy, unsafe disclosure, false denial, and silent use;
- topology-family macro results;
- raw characters/tokens, calls, corrected fields, latency, and monetary cost;
- generic/typed downstream disagreements.

Fixed deterministic development checks use exact counts, not p-values. A later stochastic study clusters by topology/scenario rather than individual questions.

## 13. Falsification

The end-to-end verifier claim is rejected or narrowed if held-out evaluation shows any of:

- no safety improvement over the primary extractor at matched coverage;
- excessive clean false correction;
- confident wrong corrections;
- gains that depend on fields absent from raw text;
- gains disappearing on Session-A-authored wording;
- abstention hiding most hard cases without useful risk/coverage;
- verifier cost dominating benefit;
- unequal selected events or material G/T downstream divergence.

A controlled-candidate recovery result cannot rescue a failed end-to-end comparison.

## 14. Session A handoff

Use the compact development file as the schema example and complete:

```text
data/track_x_v02/heldout/AUTHORSHIP_TEMPLATE.md
```

The held-out contribution begins with:

```text
[Session A] ACCEPT WITH PASSAGE CONTRIBUTION
```

Silence does not count as protocol acceptance.