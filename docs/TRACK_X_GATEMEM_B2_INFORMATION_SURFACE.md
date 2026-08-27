# Track X GateMem B2 — Deployable Information-Surface Freeze

**Status:** pre-outcome contract and synthetic surface audit; no public B2 result  
**Base:** PR #50 head `93d1afe8b684b1ebbd26cf174832a2d0e2ea59a1`  
**GateMem:** `603f9f4b4ba4b77f043c20f85687fa016fd720b0`  
**Issue:** #4

## 1. Deciding causal question

B1a retrieves raw public turns with fixed BM25 and exposes them directly. B1b
keeps the exact B1a candidates and prompt but adds one frozen reader. B1b
reduced final answer strings mostly through `no_memory`, destroyed utility, and
could not reduce end-to-end leakage below the already exposed prompt context.

B2 therefore tests the next mechanism:

```text
same B1a raw top-k candidates
-> pre-reader governance gate
-> admitted context only
-> same frozen B1b reader
```

The B2 hypothesis is not that a typed database is better. It is that a
pre-reader gate operating on deployable evidence can improve the
utility/governance frontier relative to reader-only B1b.

## 2. Primary capability condition

The primary B2 method receives only information available through the protected
raw-language runner:

- incrementally observed public turn text;
- opaque per-run turn, principal, episode, and query identities;
- speaker role and optional public display name;
- public timestamp and turn kind;
- incremental ingest order up to the checkpoint;
- asker opaque identity, asker role, and query text;
- the exact B1a top-k turn candidates and BM25 scores;
- the same B1b reader configuration and budget.

The machine-readable contract is:

```text
configs/track_x_gatemem_b2_information_surface_v0_1.json
```

The implementation generates the same manifest through
`governance_surface_manifest()` and tests exact JSON equality.

## 3. Forbidden evaluator-only inputs

The method must fail closed if any of these fields enters its information
surface:

```text
query_type
expected_action
judge_spec
leak_targets
relationships
records
gold_records / gold_record_ids
record_refs
memory_ops
future_turns
source checkpoint / episode / turn IDs
as_of_turn_id
labels
```

The outer evaluator may retain these fields only for official scoring and
protected post-hoc analysis. They cannot influence candidate ranking, policy
parsing, gating, prompt construction, reader invocation, or method action.

## 4. No hidden relationship capability

Pinned GateMem's native `PolicyRAGAgent` can use
`episode.entities.relationships`, which contain answer-relevant authorization
metadata. That is a valid native benchmark baseline but a different capability
condition.

The B2 primary condition deliberately excludes relationships. It is named:

```text
public-turn-text-derived-governance
```

It must not be described as native Policy-RAG compatibility. A later
relationship-capability condition, if run, must be separately named and may not
replace this result.

## 5. Public policy signal semantics

The frozen parser recognizes explicit public-turn assertions only:

- information deletion: a deletion verb (`delete`, `forget`, `erase`, `remove`,
  `purge`, or `wipe`) must occur in the same turn as an information referent
  (`memory`, `record`, `data`, `information`, `details`, `conversation`,
  `message`, `note`, or `history`);
- deny-target: `do not share/disclose with <principal or role>`;
- allow-list: `only share with <principal or role>`;
- actor-only: `keep this private/confidential`;
- grant: `may/can share with` or explicit allow/authorize-to-access phrasing.

Bare domain actions are not Active Forgetting. In particular:

```text
Please remove the stitches tomorrow.  -> no deletion signal
Please wipe the table.                 -> no deletion signal
Please delete the diagnosis record.    -> deletion signal
```

A signal records:

```text
operation
restriction scope
actor opaque identity and role
observed ingest index
source public turn
mentioned target principals/roles
topic anchor tokens
source-text SHA-256
```

The primary gate applies a policy signal only when:

1. it was observed after the candidate turn;
2. it came from the same speaker as the candidate turn;
3. any non-empty topic anchors overlap the candidate text.

This is an auditable heuristic, not a legal or institutional authorization
engine. Same-speaker authority is a conservative source-control assumption, not
a claim that every real speaker may revoke all data they utter.

## 6. Frozen policy choices

```text
unknown policy:                 admit
external authenticated policy: disabled
same-speaker authority:         required
deleted state:                  terminal
candidate backfill:             disabled
policy-directive turn:          blocked from reader context
```

Unknown-admit prevents B2 from becoming an all-refuse baseline. It also means
B2 may show no governance improvement when policy or deletion is not explicitly
recoverable from public dialogue. That null result must be retained.

The gate blocks the entire public policy-directive turn because the v0.9
mechanism has no span-level redaction and the directive may repeat protected or
deleted content. This conservative choice can reduce utility and is measured as
false blocking.

## 7. Candidate and reader equality

B2 must use the exact B1a retrieval method and fixed parameters:

```text
top_k:                 5
BM25 k1:               1.2
BM25 b:                0.75
recency weight:        0.0
prompt character cap:  6000
```

B2 receives only those top-k candidates. When candidates are blocked, it does
not retrieve replacements. The retrieval-item sequence and scores must equal
B1a checkpoint by checkpoint before a B2 result is accepted.

The reader remains:

```text
deepset/minilm-uncased-squad2
revision 934656cdda79824eabf503ed56e15c01ddbdbe3f
max length 384
stride 128
max answer 30 tokens
null margin 0.0, not GateMem-calibrated
```

Reader calls, tokens, windows, latency, and package revisions are reported
separately. B2 is allowed to make fewer reader calls when no candidate is
admitted; that is mechanism cost, not a matched-call claim.

## 8. Required metrics

Official GateMem metrics remain primary. Supplemental stage metrics must include:

### Retrieval/candidate stage

- official checkpoint coverage;
- exact B1a/B2 retrieval-item equality;
- top-k candidate count and character budget;
- candidate recall where evaluator-side labels permit protected analysis.

### Prompt-governance stage

- admitted and blocked candidate counts;
- permitted prompt recall;
- forbidden prompt exposure;
- false blocking of required evidence;
- privacy/deletion prompt-context exposure;
- B2 matched-signal checkpoint count and reason-code counts.

`B2_matched_signal_checkpoint_count` is method-dependent diagnostic coverage. It
must not be described as a method-independent public-signal identifiability
estimand.

### Reader/answer stage

- utility accuracy;
- answer, prompt-context, and end-to-end privacy leakage;
- answer, prompt-context, and end-to-end deletion leakage;
- action distribution, coverage, over-refusal, and fixed safe coverage;
- reader calls, input tokens, windows, latency, and cost.

Supplemental candidate/permitted/forbidden labels stay evaluator-side and cannot
cross into the method.

## 9. Acceptance and falsification

No B2 superiority claim is allowed from the surface audit. A public outcome is
accepted only after:

1. exact source, scorer, model, dependency, and workflow pins;
2. 2,218/2,218 official checkpoint coverage;
3. B1a/B2 retrieval candidate equality at every checkpoint;
4. method-surface scans proving forbidden fields absent;
5. official scorer success in every domain;
6. aggregate-only artifact inspection;
7. explicit Session B code/contract/result review.

The B2 hypothesis is rejected or narrowed if it:

- fails to reduce forbidden prompt exposure;
- improves safety only by collapsing useful evidence and coverage;
- uses evaluator-only relationships or labels;
- changes retrieval candidates or reader settings;
- depends on post-hoc threshold or parser tuning;
- gives no gain because public text lacks identifiable policy signals;
- is dominated by blanket refusal or by the unfiltered B1b frontier.

## 10. Current evidence boundary

The committed deterministic audit verifies only the interface and fixed
mechanism on hand-authored public-turn examples. It is not:

- a GateMem performance result;
- an official leaderboard result;
- evidence for MindMap, G-flat, T-normalized, or T+raw;
- an empirical calibration result;
- a production access-control claim.

A positive public B2 result, if obtained, would establish only the value of this
specific public-text-derived pre-reader gate under the frozen capability and
reader conditions.