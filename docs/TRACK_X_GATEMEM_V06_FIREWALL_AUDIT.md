[Session B]

# Track X GateMem v0.6 Firewall and Execution-Integrity Audit

**Status:** blocking pre-outcome review  
**Audited source branch:** `research/track-x-v0.6-gatemem-official-harness`  
**Audited base:** `research/track-x-v0.5-gatemem-baselines@ac533d0ca880dee3c689ce13443b42c672315ff8`  
**Source-head identity:** recorded in the follow-up audit commit after GitHub returns the parent SHA  
**Benchmark result accepted:** none

## 1. Disposition

The v0.6 branch adds useful official-run plumbing:

- a pinned GateMem checkout and data/scorer hash audit;
- a clean external-prediction path into GateMem's unmodified scorer;
- result-bundle hashing and method configuration capture;
- deterministic initial endpoint controls.

However, it invokes the unchanged v0.4/v0.5 public boundary. Three previously reported capability leaks therefore remain active, and the official harness introduces additional execution-integrity problems.

> **Do not run or interpret GateMem outcomes from v0.6 as a protected raw-language result until the blocking gates below are resolved.**

A local smoke run may be used only to debug scorer compatibility and must be labelled `unprotected-interface smoke test`.

---

## 2. Audited files

```text
src/mindmap/track_x/gatemem_public.py
src/mindmap/track_x/gatemem_runner.py
src/mindmap/track_x/gatemem_baselines.py
src/mindmap/track_x/gatemem_official.py
experiments/gatemem_external.py
tests/test_track_x_gatemem_official.py
docs/TRACK_X_GATEMEM_OFFICIAL_RUN.md
```

The review also checks the pinned GateMem external scorer contract at:

```text
rzhub/GateMem@603f9f4b4ba4b77f043c20f85687fa016fd720b0
```

---

## 3. Blocking finding F1 — source identifiers reveal evaluator structure

### Evidence

The method receives original values through:

```text
PublicEpisode.episode_id
PublicTurn.turn_id
PublicCheckpoint.checkpoint_id
PublicCheckpoint.episode_id
PublicCheckpoint.as_of_turn_id
```

The raw baseline then repeats source checkpoint and turn identifiers in `answer_structured` and `memory_audit`.

The released GateMem IDs are not opaque. Episode IDs contain domain, generator family, language, index, and scenario slug. Checkpoint suffixes are grouped by hidden query class in released episodes. Consequently, removing the explicit `query_type` field does not remove query-class capability.

### Risk

A method can learn or hard-code priors such as:

```text
early episode-local checkpoint ordinal -> utility / answer
middle ordinal                         -> privacy / refuse
late ordinal                           -> safety / no_memory
```

It can also recognize benchmark templates, split membership, or memorized scenarios from episode slugs and turn positions.

### Required correction

The outer evaluator retains source IDs and supplies the method only per-run opaque surrogates:

```text
method_episode_id
method_turn_id
method_query_id
```

Use random UUIDs or HMAC-derived values under an evaluator-only per-run secret. Do not use sequential checkpoint surrogates. Restore source checkpoint IDs only after the method returns, inside the evaluator-owned join.

`as_of_turn_id` is not method-required because the runner invokes the query only after ingesting the correct prefix. Remove it from the method query object. A sanitized public timestamp already observable from ingested turns may be provided only under a separately declared temporal-coordinate condition.

### Required tests

1. No method-visible identifier contains a source-ID substring.
2. A probe matching `ckpt_(\d+)`, domain slugs, generator names, and source turn patterns observes no match.
3. Permuting source IDs does not change method inputs or semantic predictions.
4. Fresh surrogate secrets produce semantically identical predictions.
5. The evaluator correctly restores the official source checkpoint ID only after method execution.

---

## 4. Blocking finding F2 — reset relationships include answer-defining policy annotations

### Evidence

`public_episode_from_raw()` clones every `entities.relationships` object and exposes it at reset. Released GateMem episodes include fields such as:

```text
access_level
assigned_clinician
covering_clinician scope
family relationship and scheduling scope
```

These values are directly relevant to access-control answers and may summarize policy that the raw-language condition is supposed to reconstruct from turns.

### Risk

The method can bypass extraction, temporal update, and authorization reasoning. A low access-control violation rate may measure provided relationship annotations rather than memory-system behavior.

### Required condition split

```text
X-raw-primary
  chronological public turns
  speaker/asker identity and role
  no entities.relationships
  no record_refs or memory_ops

X-directory-sensitivity
  X-raw-primary plus identity/display/role directory only

X-annotated-relationship-compatibility
  a separately named, byte-identical annotation condition
  never reported as raw-language
```

A relationship field may enter the primary process only if it is independently available before the benchmark conversation, has explicit validity semantics, and does not encode consent, access, assignment scope, disclosure, deletion, or a future policy transition.

### Required tests

1. A reset-only probe cannot infer family access, assigned-care-team scope, revocation, or expected action.
2. Removing relationships leaves public turn/query text unchanged.
3. Every reset field has provenance class `public_directory`, `benchmark_annotation`, or `derived_from_dialogue`.
4. Only `public_directory` may enter the primary process.

---

## 5. Blocking finding F3 — checkpoint probes share mutable method state

### Evidence

`run_protected_episode()` creates one `GateMemPublicSession`, resets one agent, then issues every checkpoint query in sorted episode order. Earlier benchmark queries and answers can mutate caches, consolidation state, counters, or policies observed by later checkpoints.

The v0.6 document explicitly describes one fresh method instance per episode, not one isolated state per checkpoint.

### Risk

GateMem checkpoints are evaluator probes, not world events. A method may infer query class from prior probe count/order or may be accidentally contaminated by prior privacy/deletion questions. Opaque identifiers alone do not close this channel.

### Required primary mode

For each checkpoint, evaluate:

```text
fresh public reset
+ exactly the public turn prefix through that checkpoint
+ exactly one query
```

Acceptable implementations:

- fresh replay per checkpoint;
- verified immutable snapshot plus clone;
- process snapshot restored before each query.

The required invariant is:

```text
Prediction(c) = f(public reset, public turns <= c, public query c, frozen config)
```

and is independent of every other benchmark checkpoint.

Keep the upstream sequential behavior only as `upstream_sequential_compatibility`. Report isolated-versus-sequential disagreement as checkpoint-interference error.

### Required tests

1. Random checkpoint-order permutation leaves isolated outputs byte-identical.
2. Repeating a checkpoint cannot change another prediction.
3. Inserting an unrelated privacy/deletion probe cannot change a utility prediction.
4. A deliberately stateful query-counter agent is neutralized by isolated mode and detected in sequential mode.
5. Snapshot/clone and replay agree for a deterministic reference agent.

---

## 6. High-severity finding F4 — result metadata falsely declares that raw benchmark text was not copied

### Evidence

`run_external_gatemem()` writes this unconditionally:

```text
boundary.raw_benchmark_text_copied_to_result = false
```

Its docstring also says the run does not copy benchmark text to results.

But `RawLexicalGateMemAgent` copies selected turn text into:

```text
output.answer
output.memory_audit.items[*].text
output.memory_audit.prompt_context.text
```

Those fields are written to `predictions.jsonl`. The current test covers only `AlwaysNoMemoryGateMemAgent`, so it cannot detect this contradiction.

### Required correction

Replace the Boolean with measured, method-specific fields:

```text
source_dataset_files_copied
raw_text_in_predictions
raw_text_in_protected_audit
raw_text_in_publishable_artifact
prompt_context_text_retained
```

Scan the completed bundle and fail if declared exposure does not match observed exposure. Separate a protected local full-text bundle from publishable redacted artifacts containing IDs/spans/hashes and aggregates only.

Add an explicit raw-lexical regression test containing a sentinel source string.

---

## 7. High-severity finding F5 — checkout cleanliness is not hermetic

### Evidence

`git_dirty()` runs:

```text
git status --porcelain --untracked-files=no
```

Thus untracked files are ignored. The scorer subprocess also inherits the ambient environment and Python import configuration.

### Risk

An untracked `sitecustomize.py`, importable module, local configuration, or environment-provided `PYTHONPATH` can change official scoring while the harness reports `dirty=false`. The recorded scorer hash alone does not bind all imported code.

### Required correction

For an accepted external run:

1. require a fully clean checkout including untracked files, or use a fresh detached worktree/container;
2. run the scorer in a sanitized environment;
3. record Python executable/version and dependency lock identity;
4. hash the relevant tracked source tree or record the full Git tree SHA;
5. prevent network access unless explicitly preregistered;
6. retain `--allow-dirty-checkout` only for non-scientific debugging and mark the result invalid.

---

## 8. High-severity finding F6 — stale output artifacts may be mixed into a new run

### Evidence

The harness creates an output directory but does not require it to be empty or atomically replace it. Core JSONL files are overwritten, while pre-existing official scorer files or unrelated artifacts may survive.

### Risk

A result bundle can contain stale `judge_scores`, summaries, logs, or artifacts from another method/configuration. Hashing the resulting mixture does not prove one-run provenance.

### Required correction

Use one of:

- fail unless output directory is absent/empty;
- write to a temporary directory and atomically rename on success;
- use a content-addressed run ID derived from the frozen run manifest.

The manifest must enumerate every accepted artifact and reject unexpected files.

---

## 9. Methodological boundary F7 — raw excerpt echo is an endpoint, not a matched retrieval baseline

The current raw lexical agent emits retrieved excerpts as the final answer. It measures a high-exposure endpoint but conflates retrieval and generation.

Use the following names:

```text
B0   AlwaysNoMemory
B1a  RawContextEchoAlways
B1b  RawBM25 + shared frozen reader
B1c  RawBM25 + same reader + frozen selective rule
```

Only B1b/B1c may be compared with G-flat/T-normalized as matched answer systems. They must share the reader model, prompt hash, tokenizer, evidence-token budget, output-token budget, calls, retries, and latency accounting.

The current character ceiling is acceptable for B1a smoke testing only. Matched systems require the reader tokenizer and a token ceiling.

---

## 10. Exposure accounting F8 — retrieval, prompt, answer, and stored audit are distinct

Define:

```text
R(q) = retrieved candidates
P(q) = exact post-budget prompt spans
A(q) = final answer
D(q) = persisted diagnostic/audit content
```

Report leakage or sensitive exposure separately over all four surfaces. The pinned GateMem rule scorer can inspect exact prompt context when supplied, but it does not automatically score extra full-text diagnostic fields. Therefore a clean prompt score does not imply a clean stored audit.

`memory_audit.prompt_context.text` must be byte-identical to the reader's actual memory block. `retrieved_items` and post-budget `prompt_items` must remain separate.

---

## 11. Additional execution gates

Before any outcome is interpreted:

- verify the actual MindMap Git head and dirty state rather than accepting an arbitrary `repository_revision` argument;
- require a recorded repository revision rather than permitting `unrecorded`;
- hash and validate all expected official scorer outputs, not only `summary.json`;
- align documented scorer filenames with the pinned scorer's real outputs;
- record whether default or `--gate_by_action` scoring was selected before inspection;
- keep official GateMem metrics and Track X supplemental metrics in separate namespaces;
- do not publish full raw excerpts without resolving benchmark terms.

---

## 12. Synthetic/public Track X integration

The tracks answer different questions:

```text
synthetic #38/#44
  verifies fine-grained MindMap semantics, partial support, topology composition,
  correlated corruption, verifier interfaces, and known counterexamples

public GateMem v0.6
  verifies external task realism, native U/A/F and MGS behavior,
  prompt exposure, and public-domain generalization pressure
```

The synthetic track should export invariant/failure hypotheses into public diagnostics. The public track should return observed natural error patterns to the synthetic corruption model. Neither result substitutes for the other.

---

## 13. Acceptance matrix

| Gate | Required before smoke | Required before reported external result |
|---|---:|---:|
| checkout revision/data/scorer hashes | yes | yes |
| opaque method-side identifiers | no | **yes** |
| policy relationship removal | no | **yes** |
| checkpoint-isolated primary mode | no | **yes** |
| exact prompt context | yes for raw | yes |
| truthful artifact exposure manifest | yes | yes |
| fully clean/hermetic scorer | no | **yes** |
| empty/atomic output bundle | yes | yes |
| shared-reader matched baseline | no | yes for comparative claims |
| sandboxed method process | no | **yes** |

A smoke run conducted before the bold gates pass is plumbing evidence only and must not be used for model, memory, safety, or governance conclusions.

## 14. Requested Session A response

Please explicitly accept, amend, or reject:

1. the three blocking capability findings F1–F3;
2. the false exposure declaration F4;
3. hermetic-checkout and atomic-output gates F5–F6;
4. B1a/B1b/B1c naming and comparison boundary;
5. the synthetic/public feedback loop.

Silence is not approval. No benchmark outcome should be generated while these review gates remain unresolved.