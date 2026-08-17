# Track X GateMem Protected Runner

**Status:** pre-outcome execution scaffold  
**Upstream pin:** `rzhub/GateMem@603f9f4b4ba4b77f043c20f85687fa016fd720b0`  
**Empirical result:** none

## 1. Objective

GateMem's official runner is incremental, but the method-facing Python objects contain complete episode data and evaluator-only checkpoint attributes. The protected runner preserves GateMem's chronological protocol and external prediction format while replacing those objects with capability-reduced public views.

The implementation is split into two trust domains:

```text
outer evaluator
  owns raw episodes, raw checkpoints, hidden labels, and official scoring

method process
  receives PublicEpisode, PublicTurn, and PublicCheckpoint JSON only
```

The method never receives the raw `episode` or upstream `Checkpoint` objects.

## 2. Native behavior retained

The runner retains:

```text
one reset per episode
incremental ingestion through each checkpoint's as-of turn
stable source order for checkpoints sharing an as-of turn
fresh method state per episode
official action vocabulary
external prediction join by checkpoint_id
```

Unlike the upstream runner, an unknown `as_of_turn_id` is a hard failure rather than a silently skipped checkpoint. Exact prediction-ID coverage is verified before a run is accepted.

The emitted scorer-facing row follows GateMem's documented external format:

```json
{
  "checkpoint_id": "...",
  "output": {
    "action": "answer_redacted",
    "answer": "...",
    "answer_structured": {},
    "used_record_ids": [],
    "memory_audit": {}
  }
}
```

Hidden `query_type`, `attack_type`, `expected_action`, judge instructions, leak targets, gold answers, and policy snapshots are not copied into the prediction artifact. The official evaluator joins its private annotations by `checkpoint_id`.

## 3. Boundary audits

### Episode

The method reset view includes only:

```text
episode_id
domain
static principals
static relationships
```

The audit records hashes of the complete source episode and public reset view plus dropped root paths such as `turns`, `records`, and checkpoint material.

### Turn

The primary raw-language condition includes:

```text
turn_id
timestamp
speaker principal and role
turn kind
text
```

`record_refs` and `memory_ops` are omitted for every compared system. Their source and public hashes and dropped root paths are retained in the outer audit.

### Checkpoint

The method query view includes only:

```text
checkpoint_id
episode_id
as_of_turn_id
asker principal and role
query text
```

The audit stores:

```text
source checkpoint hash
public checkpoint hash
removed paths
prediction hash
ingested-turn count
incremental ingest count
ingest/query wall time
```

Removed values are not copied into the method audit.

## 4. Chronology and identity checks

The runner rejects:

```text
duplicate episode IDs
duplicate turn IDs
duplicate checkpoint IDs, locally or globally
checkpoint/episode mismatches
unknown as-of turns
query before or after the exact as-of turn
speaker or asker role contradictions with static principal metadata
missing predictions, extra predictions, or duplicate prediction IDs
```

Multiple checkpoints at one turn preserve their source order. This matches Python's stable sort in GateMem's official runner and avoids silently changing behavior for methods whose query path maintains caches.

## 5. JSONL subprocess protocol

`SubprocessGateMemAgent` provides a persistent request/response protocol:

```json
{"request_id":0,"operation":"reset","payload":{}}
{"request_id":1,"operation":"ingest","payload":{}}
{"request_id":2,"operation":"query","payload":{}}
{"request_id":3,"operation":"close","payload":{}}
```

The worker replies with the same request ID and either a strict-JSON result or a serialized error. The client enforces:

```text
one outstanding request
response timeout
maximum response size
request-ID agreement
strict JSON
method failure propagation
stderr diagnostics
```

Runtime or protocol failures raise errors. They are not converted into abstentions and therefore cannot be rewarded as safe selective behavior.

## 6. What process separation does and does not guarantee

JSON serialization prevents the method from following Python references to hidden attributes or future episode objects. It does **not** by itself prevent a malicious or accidentally overprivileged method from reading:

```text
benchmark files mounted on the same filesystem
repository fixtures and manifests
cloud credentials or API keys
evaluator sockets, logs, or temporary files
network-accessible hidden services
```

A confirmatory run must therefore place the method in a separate sandbox/container with:

```text
no raw checkpoint or evaluator-data mount
an empty or allowlisted working directory
minimal environment variables
no evaluator credentials
restricted network according to the preregistration
only the JSONL public-data channel
```

`minimal_subprocess_environment()` removes credential-like additions and omits common secrets, but is defense in depth rather than a sandbox.

## 7. Fair comparison

For G-flat, T-normalized, T+raw, and raw-retrieval baselines, freeze the same:

```text
public episode/turn/checkpoint stream
model and version
prompt budget
extraction, repair, and answer-call budget
retrieval candidates and context-token budget
latency boundary
hardware class
network policy
```

If an implementation uses an extra validator or repair call, that call is counted. If an annotated compatibility condition supplies `record_refs` or `memory_ops`, it must be run and named separately and the annotations must be byte-identical across systems.

## 8. Required result bundle

Before official scoring, persist:

```text
upstream repository and dataset revisions
method repository revision
public protocol/schema revision
source/public hashes and removed-path manifests
checkpoint prediction coverage report
method configuration and prompt hashes
model/token/retry/retrieval budgets
per-checkpoint latency and cost counters
scorer-facing predictions.jsonl
prompt-context/retrieval audit where available
```

Then run GateMem's official scorer unchanged. Official U, A, F, over-refusal, MGS, and answer/context/end-to-end leakage remain the primary benchmark result. Track X safe coverage, governed coverage, calibration, and cost are supplemental.

## 9. Current limitations

1. The runner has synthetic shape tests but no GateMem dataset result.
2. Static relationship objects are passed as strict JSON without a domain-specific field allowlist.
3. The subprocess transport has not yet been wrapped in an OS-level filesystem/network sandbox.
4. Token and monetary cost counters depend on the eventual method implementation.
5. The first confirmatory method adapter has not been selected.
6. External scorer compatibility still requires a pinned end-to-end smoke test against the official GateMem code.

No benchmark-performance or security claim follows from this scaffold alone.
