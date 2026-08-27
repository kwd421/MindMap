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
- **Status:** pending
- **Primary purpose:** verify official data/evaluator identity and measure a
  no-memory/local retrieval/DeepSeek Flash comparison on a fixed small sample.
- **Promotion condition:** exact data and scorer hashes, frozen sample, prompt
  hashes, token/cost log, and manual audit of judge behavior.
