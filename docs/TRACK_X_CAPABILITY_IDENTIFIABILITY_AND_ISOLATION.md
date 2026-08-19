[Session B]

# Track X Capability, Identifiability, Pairing, and Query-Isolation Protocol

**Status:** pre-outcome methodological supplement  
**Related public hub:** Issue #4  
**Related semantic/coordination hub:** Issue #7  
**Implementation reviewed:** `research/track-x-v0.7-gatemem-opaque-firewall`  
**Benchmark outcome claimed:** none

## 1. Why this supplement is needed

A memory benchmark can confound at least four independent questions:

1. whether the relevant facts were present in the method-visible input;
2. whether the method extracted and retained those facts;
3. whether retrieval exposed the right evidence to the reader;
4. whether the reader selected the right action and answer.

GateMem adds a fifth question: whether static relationship/directory metadata is part of the intended method capability. At the pinned release, native agents receive requester-relevant relationship facts through the episode scaffold. A stricter dialogue-only condition removes that information and asks the method to reconstruct policy from language. Both are useful, but they are different experiments.

The protocol below prevents capability removal, pseudonymization randomness, and evaluator-query history from being misreported as a memory-architecture effect.

---

## 2. Capability conditions

For checkpoint `c`, define:

```text
E_c = chronological public turn prefix through c
D_c = principal identity / display / role directory
R_c = static requester-relevant relationship metadata
Q_c = authenticated requester and query
Y_c = required action plus permitted answer content
```

Freeze at least these named conditions:

### C_raw

```text
(E_c, D_c, Q_c)
no R_c
no record_refs
no memory_ops
```

This tests end-to-end policy reconstruction from dialogue with an identity directory. It must not be called turn-text-only if `D_c` is supplied.

### C_native

```text
(E_c, D_c, R_c, Q_c)
```

`R_c` follows the pinned native GateMem relationship capability. Any decision about `record_refs` or `memory_ops` is an additional named axis and must be identical across compared methods.

### C_annotated

A compatibility or ceiling condition containing further benchmark annotations. It is never the primary raw-language condition.

Results must always include the capability condition in method names, manifests, result directories, and tables.

---

## 3. Identifiability

Let `W_C(o)` be the set of benchmark-consistent latent worlds that produce the same method-visible observation `o` under capability condition `C`.

A checkpoint is action-identifiable under `C` when:

```math
I_C(c)=1
\iff
\left|\{Y(w,c): w\in W_C(Obs_C(c))\}\right|=1.
```

This is stronger than saying the expected action appears lexically in the dialogue. It asks whether every completion consistent with the supplied evidence implies the same action and disclosure scope.

### Operational labels

```text
raw_identifiable
  C_raw uniquely determines Y_c

relationship_dependent
  C_raw is ambiguous but C_native determines Y_c

ambiguous_even_native
  C_native does not uniquely determine Y_c

annotation_leaky
  an evaluator annotation directly encodes Y_c or a close surrogate
```

### Estimation procedure

Use a hierarchy of evidence:

1. declarative benchmark/generator analysis where available;
2. paired counterfactual completion of omitted relationship facts;
3. blinded dual human annotation with adjudication;
4. automated model auditing only as a diagnostic, never the sole gold source.

For a raw-primary benchmark claim, report performance separately on `raw_identifiable` and `relationship_dependent` strata. A failure on a relationship-dependent item is not automatically evidence of memory failure; the method may be missing an exogenous capability.

---

## 4. Separating architecture and capability effects

For method architecture `A` and capability condition `C`, let `M(A,C)` be a frozen metric.

Architecture effect within one capability:

```math
\Delta_{arch}^{C}=M(T,C)-M(G,C).
```

Capability effect within one architecture:

```math
\Delta_{cap}^{A}=M(A,C_{native})-M(A,C_{raw}).
```

Architecture–capability interaction:

```math
\Delta_{int}=
[M(T,C_{native})-M(T,C_{raw})]
-
[M(G,C_{native})-M(G,C_{raw})].
```

A large `Δ_cap` with a small `Δ_arch` means the dominant experimental variable was supplied information, not typed versus generic memory. A large `Δ_int` means the architecture behaves differently when exogenous relationship information is removed and requires explicit interpretation.

Do not pool `C_raw` and `C_native` into one score.

---

## 5. Opaque identifier design

Pseudonymization is an evaluator firewall, not a model feature.

### Least-capability rule

The method needs stable opaque IDs only where continuity requires them:

```text
principal ID: usually required
turn ID: useful for source attribution and retrieval audit
episode ID: optional opaque namespace
query/checkpoint ID: normally not semantically required
```

Transport request ordering should use a separate RPC request counter. In checkpoint-isolated mode, the semantic query object can omit a query ID entirely. If an opaque query ID is retained for compatibility, it must not enter the reader prompt and should be tested as an ablation.

### Paired run-group key

For paired methods in technical replicate `r`, use one evaluator-only opaque key `K_r` for every compared method:

```text
B0, B1, G-flat, T-normalized, T+raw
  all receive the same pseudonyms under K_r
```

Across independent technical replicates, draw fresh keys:

```text
K_1, K_2, ...
```

This gives a common-random-numbers design. The paired method contrast for replicate `r` is:

```math
D_r=M(T,K_r)-M(G,K_r).
```

Using unrelated keys for paired methods introduces avoidable tokenization and identifier nuisance. Using one key forever may permit accidental benchmark memorization.

Public artifacts may record a one-way commitment to `K_r`. Exact reproduction requires protected key escrow or a controlled rerun service; publishing the secret would weaken the capability boundary.

Scientific runs should require a cryptographically random 256-bit key. A caller-supplied low-entropy byte string is acceptable only for unit tests.

---

## 6. Source-ID leak surface

The forbidden source set must include:

```text
source episode IDs
all source turn IDs
all source checkpoint IDs
all source principal IDs, including non-asker speakers and directory-only principals
scenario/template slugs
source ordinal patterns
```

Scan every method-controlled output surface:

```text
answer
answer_structured
used_record_ids
memory_audit
retrieval traces
prompt text
logs returned across RPC
```

Substring scanning is a regression guard, not a complete noninterference proof. Also run trained/adversarial probes that attempt to recover domain template, checkpoint class, source ordinal, or split from the full serialized method input.

---

## 7. Checkpoint isolation

Benchmark checkpoints are evaluator probes, not world events. A query must not change the durable memory state used for another checkpoint.

Define the primary prediction invariant:

```math
Pred(c)=f(E_c,D_c,R_c,Q_c,\theta,K_r)
```

and require independence from every other checkpoint query and answer.

### Primary modes

#### Replay isolation

For every checkpoint:

```text
fresh method instance
reset with public episode capability
replay exact public prefix
issue exactly one query
close/discard state
```

#### Snapshot isolation

Process the chronological stream once. At each unique prefix, create a verified immutable pre-query snapshot and clone/restore it separately for each checkpoint at that prefix.

### Compatibility mode

The upstream sequential one-agent-per-episode behavior may be preserved as:

```text
upstream_sequential_compatibility
```

It is not the sole scientific primary condition. Report:

```text
checkpoint_interference_rate
  = isolated/sequential prediction disagreements / checkpoints
```

### Required tests

1. random permutation of checkpoint evaluation order leaves isolated outputs unchanged;
2. repeating a checkpoint cannot alter another prediction;
3. inserting an unrelated privacy/deletion probe cannot alter a utility prediction;
4. a deliberately stateful query-counter method affects sequential mode but not isolated mode;
5. snapshot/clone agrees with full replay for deterministic methods;
6. pre-query and discarded post-query state hashes are recorded where the backend permits it.

### Cost accounting

Separate:

```text
logical memory cost
  ingestion/extraction/storage work needed by a deployed stream

benchmark isolation overhead
  replay, clone, or restore cost introduced only to prevent evaluator-probe contamination
```

Do not penalize a method twice for logical ingestion when checkpoint isolation replays the same prefix, but report actual wall time and resources transparently.

---

## 8. Exposure and artifact provenance

Use four distinct exposure surfaces:

```text
R(q): retrieved candidates
P(q): exact post-budget prompt spans
A(q): final answer
D(q): persisted diagnostics/audits
```

GateMem's pinned auxiliary scorer can inspect `P(q)` when `memory_audit.prompt_context.text` is exact. It does not imply that every full-text field in `D(q)` is scored.

Replace a single Boolean such as `raw_benchmark_text_copied_to_result` with measured fields:

```text
source_dataset_files_copied
raw_text_in_predictions
raw_text_in_protected_audit
raw_text_in_publishable_artifact
prompt_context_text_retained
```

Create two bundles:

### Protected full bundle

May contain exact answers and prompt context required for local official scoring. Access-controlled and subject to benchmark terms.

### Publishable redacted bundle

Contains opaque/public IDs where permitted, spans, hashes, configuration, aggregate metrics, and no unnecessary raw excerpts.

Every artifact has a manifest entry with:

```text
path
sha256
content class
benchmark-derived flag
sensitivity class
expected producer
```

Unexpected files fail the run.

---

## 9. Hermetic execution

An accepted external run requires:

1. exact upstream commit and Git tree identity;
2. clean tracked and untracked checkout, preferably a fresh detached worktree/container;
3. sanitized scorer environment and explicit Python/dependency identity;
4. no network unless preregistered;
5. absent/empty output destination or temporary-directory atomic finalize;
6. an allowlisted artifact manifest;
7. actual repository head verification rather than a caller-provided descriptive string;
8. hashing of the pinned scorer's real output files:
   - `predictions.normalized.jsonl`
   - `scores.jsonl`
   - `summary.json`
   - optional `judge_scores.jsonl` under a separately frozen judge condition.

A non-hermetic run is a scorer-plumbing smoke test only.

---

## 10. Synthetic/public feedback loop

The tracks are complementary:

```text
synthetic Track X
  counterfactual identifiability
  mind/world topology
  partial support
  controlled correlated corruption
  query-side-effect mutants

public Track X
  native task realism
  natural joint extractor errors
  external utility/governance behavior
  real prompt and artifact exposure
```

Public observed error vectors should calibrate synthetic corruption modes. Synthetic counterexamples should become prespecified public diagnostics or targeted human-reviewed extensions. Neither track may be used to claim the result of the other.

---

## 11. Minimum pre-outcome decision matrix

| Decision | Required before plumbing smoke | Required before reported result |
|---|---:|---:|
| opaque IDs | recommended | yes |
| paired run-group key | no | yes for paired comparisons |
| capability condition named | yes | yes |
| identifiability strata | no | yes for C_raw interpretation |
| checkpoint isolation | no | yes |
| truthful R/P/A/D exposure | yes | yes |
| hermetic scorer/output | no | yes |
| official metric namespace preserved | yes | yes |

No silence-based approval applies. Session A should explicitly accept, amend, or reject the capability, identifiability, pairing, and isolation definitions before a GateMem result is interpreted.
