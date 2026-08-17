# Track X GateMem Public-Boundary Contract

**Status:** pre-outcome implementation contract  
**Upstream pin:** `rzhub/GateMem@603f9f4b4ba4b77f043c20f85687fa016fd720b0`  
**Result claim:** none

## 1. Purpose

The upstream GateMem runner is incremental, but its Python objects contain evaluator-only fields and the complete episode object. Track X therefore places a serialization boundary between the evaluator process and the memory-method process.

The boundary does not change GateMem's episode order, queries, official action space, prediction join key, or scorer. It restricts what the method can inspect.

## 2. Public reset object

The method receives:

```text
episode_id
domain
principal_id / role / display name
static relationships
```

It does not receive:

```text
episode.turns
episode.records
checkpoints
future material
record canonical values or regex matchers
```

Static relationships are copied into a method-side object. The session keeps a separate copy so method mutation cannot alter evaluator chronology or requester filtering.

## 3. Public turn object

The primary raw-language Track X condition exposes:

```text
turn_id
timestamp
speaker principal and role
turn_kind
text
```

It deliberately removes:

```text
record_refs
memory_ops
```

Those annotations may be useful in native GateMem baselines, but they would provide structured labels before the G-flat versus T-normalized extraction comparison. If a later compatibility condition includes them, it must be named separately and supplied identically to every matched system.

## 4. Public checkpoint object

The public allowlist is exactly:

```text
checkpoint_id
episode_id
as_of_turn_id
asker principal_id
asker role
query_text
```

Known scorer fields are removed and recorded in a path manifest. Any new upstream checkpoint field that is neither known-hidden nor public-allowlisted causes a hard failure and a new audit requirement.

Known hidden fields include:

```text
query_type
attack_type
expected_action
judge_spec
leak_targets
gold_answer_structured
gold_refusal_category
policy_snapshot
```

## 5. Chronology invariant

A checkpoint may be queried only when:

```text
checkpoint.episode_id == active episode
checkpoint.as_of_turn_id == last ingested turn_id
```

This rejects both under-ingestion and future over-ingestion. Duplicate turn IDs and role contradictions with static principal metadata also fail closed.

## 6. Method interface

```python
reset(PublicEpisode)
ingest(PublicTurn)
query(PublicCheckpoint) -> prediction mapping
```

The method receives dataclasses that have no evaluator-label or future-history attributes. Prompt wording is not the security boundary; object shape and process serialization are.

The confirmatory runner should serialize each public object to strict JSON and reconstruct it inside the method process. The original upstream `episode` and `Checkpoint` objects remain only in the evaluator process.

## 7. Prediction contract

Actions remain the official GateMem set:

```text
answer
answer_redacted
refuse
no_memory
```

The method emits:

```text
action
answer
answer_structured
used_record_ids
optional memory_audit
```

The outer evaluator attaches `checkpoint_id` and invokes the official scorer. Invalid actions, non-JSON payloads, and duplicate `used_record_ids` fail before scoring.

`used_record_ids` may refer to NCM's own auditable memory records. They must not be generated from hidden GateMem gold record identifiers in the raw-language condition.

## 8. Required artifacts

Per checkpoint:

```text
source checkpoint SHA-256
public checkpoint SHA-256
removed-path manifest
last ingested turn ID
prediction SHA-256
prompt-context / retrieved-memory audit when available
```

Per run:

```text
exact checkpoint-ID coverage
no duplicate predictions
upstream commit and data revision
method commit
model, prompt, token, retry, and retrieval budgets
official GateMem summary
supplemental Track X metrics in a separate namespace
```

## 9. Matched comparison boundary

A fair G-flat versus T-normalized run uses the same:

```text
public episode objects
public turns
public checkpoints
extractor and answer backbone
calls, retries, and tokens
retrieval context budget
latency and monetary accounting
```

Typed validation may reject or request repair only within a preregistered shared call budget. G-flat receives validators with equal access to the same event vocabulary and referential/lifecycle information.

## 10. Falsification

The boundary contributes no empirical evidence by itself. Its value is rejected if:

1. a probe method can read hidden labels or future turns through the public objects;
2. a checkpoint can be queried after a later turn has entered memory;
3. official predictions cannot be scored unchanged;
4. excluding `record_refs` or `memory_ops` accidentally differs across compared systems;
5. the wrapper changes official episode/query identity or action semantics.
