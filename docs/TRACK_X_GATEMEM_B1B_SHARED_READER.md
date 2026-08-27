# Track X GateMem B1b — Raw BM25 Context with a Frozen Shared Reader

**Status:** pre-outcome implementation and official-run candidate  
**Tracks:** Issue #4  
**Base:** PR #46 opaque GateMem firewall, head `ae1fc83bade5709e3671c47b9cb251074650b066`

## 1. Question

The accepted B1a endpoint returns selected raw context as the answer. It
therefore mixes retrieval coverage with a deliberately degenerate context-echo
use policy.

B1b asks a narrower causal question:

> What changes when the exact same B1a BM25 candidates and prompt context are
> consumed by one frozen public extractive answer reader?

B1b is still policy-unaware. It cannot remove private or deleted text after
that text has entered the reader context. Prompt-context leakage therefore
remains co-primary and is expected to form a lower bound on end-to-end leakage.

## 2. Frozen retrieval surface

B1a and B1b share the existing `RawLexicalGateMemAgent` implementation and:

```text
top_k                 5
BM25 k1                1.2
BM25 b                 0.75
recency weight         0.0
prompt character cap   6000
```

For every official checkpoint, the protected workflow requires equality of:

```text
prompt-context SHA-256
prompt character count
```

between B1a and B1b before comparing any answer metric. The prompt text and
predictions remain protected and are not uploaded.

## 3. Frozen reader

```text
model:       deepset/minilm-uncased-squad2
revision:    934656cdda79824eabf503ed56e15c01ddbdbe3f
task:        extractive question answering / SQuAD2
license:     CC-BY-4.0, as declared by the upstream model card
runtime:     CPU, eval/inference mode
max length:  384 tokens
stride:      128 tokens
max answer:  30 tokens
null margin: 0.0, not calibrated on GateMem
```

The model is referenced by immutable revision and is not copied into this
repository. Runtime packages are pinned in the optional `reader` extra. The
workflow records exact installed package versions and aggregate reader calls,
windows, input tokens, and wall time.

The null decision compares the best extractive span against the lowest CLS
null score across overflow windows. The resulting sigmoid is a diagnostic
score only. It is not an empirically calibrated probability and is not used as
a confirmatory selective threshold.

## 4. Information firewall

The reader receives only:

```text
public checkpoint query text
B1a prompt context text
```

It does not receive:

```text
source checkpoint, episode, turn, or principal IDs
as-of source chronology ID
GateMem relationship annotations
hidden checkpoint labels
future turns
gold records
record_refs
memory_ops
```

The outer evaluator retains the source checkpoint ID and invokes the unmodified
pinned official scorer after method return.

## 5. Public and protected artifacts

Protected files may contain benchmark text, answers, and prompt audits:

```text
predictions.jsonl
episode_audit.jsonl
turn_audit.jsonl
checkpoint_audit.jsonl
official per-checkpoint score rows
```

They must not be uploaded or committed. Publishable output is limited to:

- official aggregate summaries for B1a and B1b;
- supplemental answered-denominator aggregates;
- exact upstream/source/scorer/model/package revisions;
- aggregate reader cost counters;
- prompt-hash equality count;
- artifact commitments that disclose no benchmark text.

## 6. Interpretation boundary

A B1b result may establish the effect of adding this one reader to the fixed raw
retrieval context. It does not establish:

- MindMap effectiveness;
- policy or deletion enforcement;
- G-flat or T-normalized performance;
- calibrated abstention;
- equal-budget comparison with a structured system;
- native GateMem relationship-capability compatibility;
- public-benchmark state of the art.

B1b is a reader/use control. The next governance mechanism is B2:

```text
same raw candidates
-> pre-reader permission/deletion/provenance gate
-> same frozen reader
```

Only B2 can test whether preventing forbidden context from reaching generation
improves the utility/governance frontier relative to B1b.
