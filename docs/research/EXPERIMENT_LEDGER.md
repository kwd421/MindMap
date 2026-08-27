# Experiment ledger

This file is append-only. Corrections are new dated addenda, not silent edits.
Machine-readable records live in `records/`.

## EXP-20260827-001 — GateMem B1a/B1b independent local reproduction

- **Class:** reproduction of the aggregate result, not the same artifact
- **Question:** Does adding a fixed extractive reader after raw BM25 retrieval
  remove prompt-context leakage while preserving utility?
- **Source:** local detached MindMap revision
  `7a12a70bcc6f093070f4c36d1e961e554d36baa6` plus two documented temporary
  integration corrections
- **Benchmark:** GateMem
  `603f9f4b4ba4b77f043c20f85687fa016fd720b0`
- **Official scorer SHA-256:**
  `3d546a21778202959a9df12bac44c196a7f20a248cf5a2cb34f0d9b9c2623d8a`
- **Reader:** `deepset/minilm-uncased-squad2` at
  `934656cdda79824eabf503ed56e15c01ddbdbe3f`
- **Environment:** Python 3.11; `pip check` passed; 74 tests passed
- **Sample:** 4 domains, 2,218 checkpoints; two B1b replicates, 4,436 scored
  checkpoints total; official scorer 8/8 success
- **Pairing:** B1a/B1b retrieval and prompt context equal at 2,218/2,218
- **Result:** aggregate utility correct 335/728 to 41/728. B1b answer
  coverage 824/2,218. Privacy answer leakage 509/727 to 45/727, while
  privacy context and end-to-end leakage remained 509/727. Deletion answer
  leakage 646/763 to 96/763; deletion context exposure remained 645/763.
- **Interpretation:** H2 is supported in this pinned setting. The reader is a
  negative control, not a MindMap architecture or leaderboard result.
- **Artifact note:** protected raw outputs remain in a temporary local directory;
  they are not committed. PR #50 has matching aggregates but different artifact
  hashes/revisions and must be described as corroboration, not identity.

## EXP-20260827-002 — GateMem B2 deployable-surface local audit

- **Class:** development/interface audit
- **Source:** `f1d7b80b67021c1782d847b67d1d89979a6ea032`
- **Environment:** Python 3.11; 86 tests passed
- **Result:** committed 9-case surface audit passed 9/9 twice with identical
  output. This verifies the tested information-surface contract only.
- **Known threats:** global regular-expression monkeypatching in the safe wrapper,
  non-memory deletion false positives, prospective-policy limitations, topic
  overlap collisions, and the unknown-admit boundary.
- **Interpretation:** no performance, privacy improvement, or readiness claim.

## EXP-20260827-003 — LongMemEval official harness smoke/pilot

- **Class:** planned smoke followed by a preregistered small pilot
- **Status:** preregistered; outcome not yet inspected
- **Primary purpose:** verify official data/evaluator identity and measure a
  no-memory/local retrieval/DeepSeek Flash comparison on a fixed small sample.
- **Official harness:** `9e0b455f4ef0e2ab8f2e582289761153549043fc`
- **Data hashes:** oracle `821a2034...20c`; cleaned S `d6f21ea9...442`
- **Frozen sample:** six non-abstention question types plus two abstention items,
  selected by the predeclared SHA-256 ranking rule; ordered-ID hash
  `c0e75cb7dce45e7f70cc0aedfca6c1ef9fe6620bfb1b3fa09620917202720e6f`
- **Arms:** no memory, local BM25 top-3 sessions, oracle evidence context
- **Reader/judge:** `deepseek-v4-flash`, non-thinking, temperature 0; the pilot
  judge adapts the official rubric but is not the official GPT-4o metric
- **Stopping rule:** 24 answer and 24 judge calls, or stop before projected cost
  exceeds USD 0.25
- **Promotion condition:** prompt hashes, token/cost log, answer-session recall,
  paired results, and a manual judge audit. This pilot cannot be promoted to an
  official score regardless of its outcome.
