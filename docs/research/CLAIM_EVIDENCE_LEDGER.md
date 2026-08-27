# Claim–evidence ledger

Status vocabulary: `design`, `exploratory`, `supported`, `contradicted`,
`superseded`, `open`. A supported claim remains limited to its listed scope.

| Claim ID | Claim | Status | Supporting evidence | Counter-evidence / limitation | Scope |
|---|---|---|---|---|---|
| C-001 | Gold, generic, and typed implementations agree on the authored fixed Track S suite. | supported | Track S: 75/75 gold/generic/typed agreement; repository tests | EXP-20260827-005 finds a future-reference divergence outside the suite | exactly the authored deterministic canonical suite |
| C-002 | A post-retrieval frozen reader reduces answer leakage but does not repair forbidden prompt exposure. | supported | EXP-20260827-001; 2,218 matched B1a/B1b contexts; answer leakage fell while context/e2e remained high | utility collapsed; exact dirty source/patch is unreconstructable; aggregate only; GateMem only | pinned GateMem negative control aggregate |
| C-003 | The current B2 information-surface implementation is ready for performance claims. | contradicted | 93 local tests and 9/9 surface cases twice at `2cea6ff...` | EXP-20260827-004: clear official and synthetic deletion requests emit no signal; surface tests do not measure language coverage | exact PR #52 head; no endpoint claim permitted |
| C-004 | Pre-reader governance improves the utility–safety frontier over raw retrieval. | open | mechanism rationale | no frozen B2 outcome yet | none |
| C-005 | MindMap outperforms other long-term-memory systems on a public benchmark. | open | none | no matched official comparison | none |
| C-006 | Explicit backup, lineage, fork/merge, and reconstruction semantics are useful engineering abstractions. | design | canonical model and fictional-source inspiration | operational advantage not yet measured | architecture hypothesis |
| C-007 | MindMap implements complete deletion. | contradicted | none | current evidence distinguishes answer suppression from persistent context exposure; all storage surfaces not audited | no such claim permitted |
| C-008 | Semantically adjacent evidence can cause a reader to answer an unsupported event question even when the official evidence-only context is supplied. | exploratory | EXP-20260827-003: `a96c20ee_abs` failed under both BM25 and oracle context | one selected question; same answerer/judge family; pilot only | one pinned LongMemEval item |
| C-009 | The three canonical implementations are temporally equivalent when events reference entities that are created later in system time. | contradicted | EXP-20260827-005: Gold `False`, Generic `False`, Typed `True` | one adversarial sequence; invalid-input policy is not yet normative | reference-before-creation replication path |
| C-010 | PR #52's post-G3 deletion grammar recognizes direct deletion requests without an explicit memory/data noun. | contradicted | EXP-20260827-004: 0/2 exact upstream and 0/2 synthetic direct requests emitted a signal | small development sample; not a recall estimate | exact grammar at `2cea6ff...` |
| C-011 | The source-aligned LongMemEval flat-BM25 session baseline retrieves every answer-bearing user session in its top five for 311 of 419 officially eligible cleaned questions. | supported | EXP-20260828-006; exact official data and source hashes; two byte-identical row artifacts | lightweight runner mirrors the official lexical path but the dependency-heavy official entry point was not executed; retrieval only | LongMemEval-S cleaned `d6f21ea9...442`, official exclusions, session granularity |

## Claim update rule

Every status change must identify an experiment ID, exact revision, denominators,
and the narrowest valid scope. A GitHub green check proves its declared command
ran; it does not by itself prove an architecture or benchmark claim.
