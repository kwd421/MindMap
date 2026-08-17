# GateMem Agent-Interface Audit

**Audited upstream:** `rzhub/GateMem@603f9f4b4ba4b77f043c20f85687fa016fd720b0`  
**Status:** pre-run leakage analysis  
**Result claim:** none

## 1. Finding

GateMem's documentation states that hidden labels are not shown to the agent, and the official prompting helpers avoid exposing them to a real answer-model call. However, the Python agent boundary itself is not capability-secure.

At the audited commit:

1. `checkpoint_from_raw(...)` constructs a `Checkpoint` containing:

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

2. `run_episode(...)` passes that complete object directly to:

```python
agent.query(ckpt)
```

3. `BaseMemoryAgent.reset(...)` receives and stores the complete episode object, including the full turn sequence and record annotations, before incremental ingestion begins.

Therefore an arbitrary custom agent can read hidden scorer labels or future episode material even though the intended protocol is incremental and label-blind.

This is not evidence that the published baselines intentionally cheat. It is an interface-level confound that an external implementation must close before claiming a fair result.

## 2. Additional boundary observations

### 2.1 Stub mode

`BaseMemoryAgent._run_llm(...)` passes `expected_action` to the local stub path while blanking it for a real provider. Stub-mode runs are useful for plumbing tests but cannot be treated as blinded benchmark evidence.

### 2.2 Full-episode reset

The official runner calls `agent.reset(episode)` with the complete episode and then incrementally invokes `ingest(turn)`. Incremental call order alone does not prevent future leakage if the implementation stores or inspects `episode["turns"]`.

### 2.3 Full-record matcher compilation

The base agent compiles record matchers from the episode's complete `records` collection during reset. The inferred record IDs are described as internal and are not directly shown to the LLM, but they can still affect policy gating, retrieval metadata, or debugging. A confirmatory NCM run should not rely on future gold record definitions unless that information is explicitly part of the official method input for every baseline.

### 2.4 Prediction artifacts

The official runner writes `query_type`, `attack_type`, and `expected_action` into prediction rows after `agent.query(...)`. This is acceptable for evaluator artifacts, but those rows must never be ingested into the memory system during resume, reflection, or later checkpoints.

## 3. Required NCM wrapper

Use an outer evaluator process and an inner method process separated by explicit public views.

### Public reset view

```text
episode_id
domain
static principal identities and roles
requester-relevant static relationships allowed by the official protocol
```

Exclude:

```text
future turns
full gold record catalog
checkpoint annotations
leak patterns
expected actions
```

### Public turn view

```text
turn_id
timestamp
speaker principal and role
turn kind
text
only method-visible operational metadata frozen in the preregistration
```

### Public checkpoint view

```text
checkpoint_id
episode_id
as_of_turn_id
asker principal and role
query_text
```

No scoring or attack labels cross this boundary.

### Private evaluator view

The outer process retains the complete checkpoint and reattaches hidden fields only after the method has returned a prediction. It then calls the official scorer unchanged.

## 4. Enforcement

Before any method call:

```text
sanitize source object
record source SHA-256
record removed paths
record public payload SHA-256
assert no hidden path remains
serialize/deserialize through the public schema
```

The serialization round trip is important: passing a sanitized dictionary alongside the original `Checkpoint` object would leave a covert capability to inspect hidden attributes.

Before final scoring:

```text
verify exact checkpoint-ID coverage
verify no duplicate predictions
verify as-of ordering
attach evaluator-only labels outside the method process
run the official scorer
```

## 5. Confirmatory reporting language

A valid result may state:

> The NCM adapter used GateMem's official episode order, action space, predictions format, and scorer, while inserting a capability-reducing wrapper that prevented the method from reading future turns and evaluator-only checkpoint attributes available on the upstream Python objects.

It must not state that this wrapper is part of the original benchmark or that every external baseline was automatically protected by the upstream interface.

## 6. Upstream compatibility test

The first adapter test should include a deliberately cheating agent that attempts to read:

```text
checkpoint.expected_action
checkpoint.query_type
episode.turns[-1]
episode.records
```

The protected wrapper passes only if all four accesses are impossible rather than merely discouraged by prompt wording.
