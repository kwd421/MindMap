[Session B]

# GateMem Checkpoint-Isolation Protocol

**Status:** pre-outcome design  
**Applies to:** future stateful raw-reader, G-flat, T-normalized, and T+raw methods  
**Does not invalidate:** deterministic B0/B1a endpoint smoke results when query methods are demonstrably side-effect-free

## 1. Threat model

GateMem checkpoints are evaluator probes. They are not dialogue turns and must not become durable agent experience.

A sequential evaluator can otherwise create:

```text
prior query text/action
query counter or cache
privacy/safety probe order
same-prefix source ordering
reader output
    -> later memory state or action
```

This is both a leakage channel and an accidental contamination channel.

For checkpoint `c`, the scientific prediction must satisfy:

```math
Pred(c)=f(S_0,E_{\le c},Q_c,\theta,K_r,Z_c)
```

where:

- `S_0` is the declared reset capability;
- `E_{≤c}` is the public turn prefix;
- `Q_c` is only the active query;
- `θ` is frozen method configuration;
- `K_r` is the evaluator-only opaque-ID run-group key;
- `Z_c` is a checkpoint-local random seed when supported.

It must be conditionally independent of every other evaluator checkpoint.

---

## 2. Reference replay algorithm

For every checkpoint independently:

```text
instantiate fresh method
reset with the same public episode capability
replay exact turns through source as-of position
capture pre-query state commitment if available
invoke exactly one query
capture output and discarded post-query state commitment
close method and discard state
restore official source checkpoint ID only in evaluator
```

Pseudo-code:

```python
for checkpoint in checkpoints_in_any_order:
    method = factory(seed=seed_for(checkpoint, replicate))
    method.reset(public_episode)
    for turn in public_prefix(checkpoint):
        method.ingest(turn)
    pre = method.state_commitment() if supported else None
    output = method.query(public_query(checkpoint))
    post = method.state_commitment() if supported else None
    emit(checkpoint.source_id, output, pre, post)
    method.close()
```

The checkpoint iteration order must be randomized in a regression condition and must not alter canonical predictions.

---

## 3. Snapshot optimization

Full replay costs:

```math
C_{replay}=\sum_{c=1}^{C} PrefixLength(c).
```

For long episodes this is benchmark overhead, not logical deployed-memory cost.

A snapshot backend may instead:

1. ingest the stream once;
2. create an immutable pre-query snapshot at each unique as-of prefix;
3. clone/restore the snapshot separately for each checkpoint at that prefix;
4. issue one query per clone;
5. discard the clone.

Approximate work:

```math
C_{snapshot}=T\cdot C_{ingest}+U\cdot C_{snapshot}+C\cdot C_{clone/query},
```

where `T` is turns, `U` unique checkpoint prefixes, and `C` checkpoints.

Snapshot and replay outputs must agree on a deterministic reference method before snapshot mode is accepted.

A snapshot manifest binds:

```text
method version/config
public episode capability hash
turn-prefix hash
opaque-key commitment
pre-query state hash
snapshot backend/version
```

---

## 4. Query-purity shortcut

A method may use the upstream sequential mode as a primary optimization only after proving a query-purity contract.

Sufficient component-level conditions include:

```text
query reads durable state but does not mutate it
query-local caches are discarded or semantically invisible
reader outputs are never consolidated
query count/order is unavailable to policy logic
RNG is checkpoint-local
pre/post durable state commitments are equal
```

Even then, run isolated versus sequential equivalence on every checkpoint:

```math
InterferenceRate=
\frac{\#\{c: Canon(Pred_{iso}(c))\ne Canon(Pred_{seq}(c))\}}{C}.
```

A nonzero rate disqualifies sequential mode as the scientific primary result.

`Canon` removes evaluator-owned source IDs and non-semantic timing fields but preserves action, answer, selected evidence, prompt context, and method audit decisions.

For B0 and current B1a, query methods are simple read-only functions over stored turns. Their endpoint runs may be retained as narrow smoke results, but this does not prove query purity for future systems.

---

## 5. Required interference mutants

The test suite includes deliberately stateful agents:

### Counter mutant

```text
increments query_count
changes action after N queries
```

### Query-consolidation mutant

```text
stores query entities as durable memories
later retrieval changes
```

### Privacy-probe mutant

```text
seeing a privacy query raises a persistent refusal flag
later utility query changes
```

### Answer-feedback mutant

```text
stores its own prior answer or retrieved context
```

### Same-prefix ordering mutant

```text
changes behavior based on source order among checkpoints sharing as-of turn
```

All mutants must show interference in compatibility mode and no cross-checkpoint effect in isolated mode.

---

## 6. Stochastic methods

Use a common checkpoint-local seed when the model/runtime supports it:

```text
seed = H(run_seed, episode_surrogate, source_checkpoint_outer_id)
```

The seed is evaluator-controlled. Source checkpoint identity is used only outside the method boundary to derive a random value; the source ID itself is never exposed.

For providers without deterministic seeded inference:

- use temperature zero where appropriate;
- record provider/model revision and request IDs;
- treat repeated calls as technical replicates;
- compare order conditions with paired cluster summaries rather than requiring byte identity;
- do not confuse provider nondeterminism with checkpoint interference.

The deterministic reference-agent isolation tests remain mandatory regardless of provider behavior.

---

## 7. Cost reporting

Report two ledgers:

### Logical deployed cost

```text
ingest/extraction calls once per chronological stream
stored bytes and write amplification
one query per checkpoint
reader/verifier/filter calls
```

### Benchmark isolation overhead

```text
replayed turns
snapshot creation/cloning
extra process launches
state serialization bytes
isolation wall time
```

Do not count replayed ingestion as if a deployed memory system would repeatedly re-extract the same turn. Also do not hide the actual benchmark compute consumed.

---

## 8. Acceptance gates

Before a stateful GateMem result is reported:

1. replay-isolated mode exists;
2. checkpoint-order permutation passes;
3. repeat/insertion mutants pass;
4. same-prefix ordering is irrelevant;
5. method failure remains failure, not safe abstention;
6. snapshot mode, if used, matches replay on a reference method;
7. isolated/sequential interference rate is reported;
8. logical and isolation costs are separated;
9. one run-group opaque key is shared across paired methods;
10. selection confidence, when used, is checkpoint-local and separate from GateMem action semantics.

Silence is not approval. This contract should be explicitly accepted, amended, or rejected before G-flat/T/T+raw external runs.
