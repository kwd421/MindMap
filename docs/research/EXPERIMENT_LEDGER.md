# Experiment ledger

This file is append-only. Corrections are new dated addenda, not silent edits.
Machine-readable records live in `records/`.

## EXP-20260829-012 — Full GateMem B2 matched execution

- **Class:** prior-access development execution
- **Question:** Does the frozen PR #52 public-text pre-reader governance gate
  reduce privacy/deletion prompt exposure relative to exactly matched raw BM25
  candidates, using the same frozen extractive reader and budget?
- **Source:** MindMap PR #52 exact
  `4ac92909d3f00612d025ac9328ee81ed37def40b`; GateMem exact
  `603f9f4b4ba4b77f043c20f85687fa016fd720b0`
- **Sample:** all four public domains, 91 episodes, 2,218 checkpoints
- **Arms:** B1a raw lexical context, B1b raw lexical plus shared reader, and B2
  the same candidates through the frozen public-text governance gate plus the
  same reader
- **Primary boundary:** official local GateMem scorer and paired prompt-surface
  aggregates; no leaderboard submission, human confirmation, parser tuning, or
  durable-erasure claim
- **Prior access:** B1a/B1b outcomes and EXP-008/009 parser diagnostics were
  known before this freeze. The exact B2 endpoint outcome was not run or
  inspected in this research loop before this record.
- **Stopping rule:** after committing this record, execute the exact three arms
  once per domain with one shared opaque-ID key, require exact candidate pairing,
  retain all denominators, and make no method amendment after B2 output.

### 2026-08-29 failure addendum

- **Execution:** all three arms produced 6,654/6,654 predictions and the
  unmodified official scorer succeeded 12/12 times.
- **Invalidation:** the paired audit failed 0/4 domains. It expected method
  opaque query IDs as the outer prediction keys, while the real protected
  runner correctly writes source checkpoint IDs at that evaluator-facing
  boundary for the official scorer. Every domain therefore reported a fully
  disjoint missing/extra set: 540/540, 552/552, 579/579, and 547/547.
- **Test gap:** the paired-audit unit fixture placed opaque IDs directly in the
  outer prediction rows and did not exercise the real external serialization
  contract.
- **Disposition:** EXP-012 is failed and contributes no adopted B2 performance
  result. Exact prediction and score bytes are retained outside git for a
  versioned evaluator-only remediation; the frozen B2 method itself will not be
  changed.

## EXP-20260829-013 — Evaluator-ID remediation and frozen reanalysis

- **Class:** post-failure development remediation
- **Input:** the byte-frozen 6,654 predictions and 12 official score outputs
  from failed EXP-012
- **Allowed change:** evaluator-side joins use the source checkpoint ID stored in
  the outer official prediction row; method-internal opaque retrieval and prompt
  IDs remain unchanged and paired
- **Forbidden changes:** method/parser/retrieval/reader/scorer/data/key and every
  prediction or score byte
- **Regression gate:** the paired-audit fixture must reproduce the real boundary
  by putting source IDs in outer prediction rows
- **Stopping rule:** commit the evaluator-only fix before opening B2 metric
  values, verify every frozen hash, run each domain audit once, and stop after
  the first valid publishable aggregates or any new invalidation

## EXP-20260827-001 — GateMem B1a/B1b independent local reproduction

- **Class:** independent aggregate corroboration / changed-environment
  replication, not the same artifact
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
- **Artifact note:** protected raw outputs and the exact dirty patch were not
  retained durably. PR #50 has matching aggregates but different artifact
  hashes/revisions. This is unreconstructable aggregate corroboration, not a
  byte-reproducible execution or artifact identity.
- **Timing note:** exact execution timestamps were not recorded; former
  midnight placeholders were removed from the machine record.

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

### 2026-08-27 exact-head addendum

- **Source:** PR #52 `2cea6ff5887b6a09821086ffda60c2504d88d15b`
- **Reproduction:** 93/93 tests passed; the committed 9-case surface audit
  passed 9/9 twice with byte-identical summaries.
- **Superseding language audit:** moved to EXP-20260827-004 so the deterministic
  contract result is not conflated with natural-language coverage.

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

### 2026-08-27 result addendum

- **Execution:** detached code `c2cdc799...`; preregistration commit
  `e4101a5b...`; 48/48 calls completed without retry
- **Pilot judge:** no memory 2/8; BM25 top-3 7/8; oracle context 7/8
- **BM25 evidence recall:** 12/13 answer sessions; full coverage on 7/8 items
- **Cost:** 118,832 cache-miss input, 128 cache-hit input, 1,543 output tokens;
  estimated `$0.027162316`; billed amount unknown
- **Failure:** both BM25 and oracle substituted a Harvard thesis/conference
  poster memory for an unsupported undergraduate-course-poster question
- **Interpretation:** retrieval success did not guarantee event attribution or
  abstention. This is a pilot failure mode, not a performance estimate.
- **Artifacts:** `results/research/EXP-20260827-003/`

### 2026-08-28 protocol-deviation addendum

- The mutable hosted alias was executed once, although MM-RP-001 asks for two
  repetitions for a stochastic pilot. Temperature 0 is not an immutability
  guarantee; no second paid run is being retroactively added.
- The cost guard checked accumulated cost before each next pair rather than a
  conservative projection of that pair. The observed `$0.0272` remained far
  below the `$0.25` ceiling, so stopping was unaffected, but the implementation
  was weaker than the frozen wording.
- The strengthened record checker now verifies the committed artifact hashes,
  preregistration ancestry/time, frozen fields, cost reconciliation, and claim
  references. These checks do not make the pilot official or confirmatory.

## EXP-20260827-004 — GateMem B2 deletion-speech coverage audit

- **Class:** post-freeze development audit; no benchmark outcome inspected
- **Source:** PR #52
  `2cea6ff5887b6a09821086ffda60c2504d88d15b`
- **Benchmark source:** public dialogue at GateMem
  `603f9f4b4ba4b77f043c20f85687fa016fd720b0`; household episodes SHA-256
  `e2bb506cc1bdc8dc7b16d4a57610147365798d03eb1c326f9197b6c6221efb6f`
- **Question:** Does the post-G3 grammar preserve the intended precision fix
  without excluding clear deletion speech acts?
- **Controls:** two physical-action negatives, one explicit-memory positive,
  two exact upstream deletion requests, and two synthetic direct requests.
- **Result:** both physical-action negatives emitted no signal and the
  explicit-memory positive emitted `DELETE`. Both exact upstream deletion
  requests and both synthetic direct requests emitted no signal.
- **Contract mismatch:** the review prototype said `forget` remained an
  intrinsically cognitive cue, but the production pattern also requires a
  nearby information referent for `forget`.
- **Interpretation:** the G3 precision correction is locally verified, but B2
  is not ready for a confirmatory endpoint run until this recall boundary is
  either amended before outcome access or explicitly frozen as a known
  capability limitation. These observed examples are development data and
  cannot later serve as a clean held-out confirmation set.

## EXP-20260827-005 — Canonical future-reference adversarial audit

- **Class:** development/canonical conformance audit
- **Source:** PR #55 code
  `f26e148602099d7be01c2759be394c6ee4ff6204`; the same counterexample was
  independently reproduced on `main`/research base
  `effca06dc8e396b7dd3fbf485c13e57f03aee242`
- **Baseline:** PR #55 passed 96/96 tests. Its four scoped-authorization and
  same-time ambiguity regressions behave consistently across Gold/G/T.
- **Adversarial sequence:** create source mind at `t0`; record lineage to an
  as-yet-uncreated destination at `t1`; grant at `t3`; replicate at `t6`;
  create the destination at `t7`; query at `t10`.
- **Result:** Gold `False`, Generic `False`, Typed `True`.
- **Mechanism:** Typed replication eligibility reads the final mind projection
  without checking `created_system_time <= exposure.system_time`; Gold and
  Generic resolve principals through the exposure time.
- **Interpretation:** this was not introduced by PR #55, but it contradicts
  general temporal equivalence outside the authored fixed suite. The schema
  must reject reference-before-creation or every resolver must enforce temporal
  referential integrity before a broader canonical-conformance claim.

## EXP-20260828-006 — LongMemEval full-set flat-BM25 reproduction

- **Class:** preregistered source-aligned reproduction
- **Status:** planned; no retrieval outcome inspected at freeze
- **Official source:** LongMemEval
  `9e0b455f4ef0e2ab8f2e582289761153549043fc`; runner SHA-256
  `efd7fc59...346`; metric SHA-256 `c98b8d10...349`
- **Data:** official cleaned LongMemEval-S, 500 released questions,
  277,383,467 bytes, SHA-256 `d6f21ea9...442`
- **Method:** session-level `flat-bm25`, `rank-bm25==0.2.2`, exact public
  user-only corpus construction, `str.split(" ")` tokenization,
  `numpy.argsort(scores)[::-1]`, official target and exclusion definitions
- **Primary outcome:** `recall_all@5` count and eligible denominator
- **Secondary outcomes:** recall-any, recall-all, and mean NDCG at
  `k={1,3,5,10,30,50}`, plus compact per-question rows
- **Stopping rule:** finish all eligible released questions or fail without
  changing data, algorithm, or exclusions
- **Claim boundary:** source-aligned local reproduction only. It is neither an
  official leaderboard submission nor an end-to-end QA or MindMap result.

### 2026-08-28 result addendum

- **Preregistration commit:**
  `e5f79d6d513e0e991de30406ce52fb0644fed398`
- **Execution:** detached source
  `6ea62666b0cde8f238ae792979fd0559ff8b6b73`; Python 3.11.15;
  `numpy==1.26.3`; `rank-bm25==0.2.2`; three runner tests passed
- **Denominator:** 500 released questions minus 30 abstention questions and 51
  questions with no answer-bearing user turn under the official target rule =
  419 eligible. All 51 no-target exclusions are `single-session-assistant`.
- **Primary result:** recall-all@5 311/419 (74.22%).
- **Secondary result:** recall-any@5 372/419 (88.78%); recall-all@1 75/419,
  @3 274/419, @10 345/419, @30 401/419, @50 419/419.
- **Type result at recall-all@5:** knowledge-update 69/72; multi-session 68/121;
  single-session-assistant 4/5; preference 21/30; user 60/64; temporal 89/127.
- **Repeatability:** the first detached run and final artifact run produced the
  same row-file SHA-256 `3420e593...ff3a9`.
- **Interpretation:** lexical retrieval is already strong on some single-event
  and update tasks but weak on complete multi-session evidence coverage. The
  result measures retrieval only and cannot be compared to end-to-end QA scores.
- **Artifacts:** `results/research/EXP-20260828-006/`.

## EXP-20260828-007 — Adaptive temporal-reference adversarial validation

- **Class:** adaptive development/adversarial audit; not preregistered or
  confirmatory
- **Source:** PR #56 exact accepted head
  `be1f9219ce5d9a424f5e44e42faa0f5ea6935ff8`; base
  `main@069c5f4b16b2f594aec48924161ae8944f39652e`
- **Review boundary:** four model-assisted manual rounds using ordinary
  git/gh/pytest/Python and direct code/document/artifact inspection. The
  reviewer was `gpt-daybreak-blue-latest` at high effort, not a human or
  blinded reviewer. Codex Security tooling and automated scan phases were
  excluded after the user's instruction.
- **Negative-result chain:** `f77849c` omitted 11 reference routes and confused
  claim/evidence namespaces; `8a3b7aa` retained future same-ID, policy-kind,
  and incomplete-snapshot failures; `6a71388` retained an empty-ID mismatch;
  `be1f921` closed the last reported case.
- **Final invalid-shape matrix:** `None`/empty/whitespace × snapshot ID/object
  kind/object ID × shared validator/Gold/Generic/Typed = 36/36 rejected.
- **Regression evidence:** temporal 49/49; full pytest 141/141; Gold, Generic,
  and Typed each 75/75 expected; Track X v0.1 artifacts 8/8 byte-identical;
  raw-verifier/oracle changes 0/224; exact-head CI 6/6 green.
- **Causal boundary:** structured-only Track X rows changed 28/112 because the
  downstream schema now rejects invalid candidates. This is not credited to
  the frozen raw verifier.
- **Status:** manual round 4 accepted the enumerated contract; PR remains an
  open draft and is not merged.
- **Interpretation:** the shared finite-runtime gate is now supported on its
  enumerated references. There is one validator implementation wired into
  three constructors, not three independent validators. Standalone Snapshot
  lifecycle, global nonblank-ID grammar, durable-store enforcement, and
  complete valid-time causality remain open.

## EXP-20260828-008 — Official GateMem deletion-imperative surface audit

- **Class:** development; prior example-level outcome access disclosed
- **Status:** completed; deterministic rule frozen at
  `b22276c9eb89594910dcd5a8fdda11c249e2b0e4` before exhaustive execution
- **Sources:** MindMap PR #52
  `4ac92909d3f00612d025ac9328ee81ed37def40b`; official GateMem
  `603f9f4b4ba4b77f043c20f85687fa016fd720b0`
- **Selection:** all four released `episodes.jsonl` files; only
  `delete`/`remove`/`erase`/`forget` imperatives at the trimmed turn start or
  immediately after `[.!?]` plus whitespace, optionally polite, together with
  imperatives following the frozen sentence-initial `Deletion request:` label.
  Newline-, quote-, colon-, and semicolon-only boundaries are outside this
  lexical rule. Descriptive and indirect language is excluded rather than
  silently labelled negative.
- **Primary outcome:** official rule-qualified turns that emit any PR #52
  `DELETE` signal / all rule-qualified turns. Referent presence, domain counts,
  and unique text hashes are secondary diagnostics.
- **Stopping rule:** exact revisions, four files, one deterministic pass; fail
  without changing the rule on revision, schema, import, or artifact error.
- **Claim boundary:** parser-surface development evidence only; not a semantic
  deletion-speech recall estimate or official GateMem score, and not evidence
  of target grounding, memory mutation, reader suppression, persistence, or
  physical erasure.

### 2026-08-28 result addendum

- **Frozen planning commit:**
  `b22276c9eb89594910dcd5a8fdda11c249e2b0e4`
- **Execution:** Python 3.11.15; 4 files, 91 episodes, and 20,293 public turns
  visited once; 233 turns matched the frozen strict-imperative rule; 231 unique
  text hashes; no hosted model or official scorer call.
- **Primary result:** 176/233 rule-qualified turns emitted any `DELETE` signal.
  This is an exact count on the selected development surface, not a GateMem
  metric or a semantic recall estimate.
- **Structural stratum:** the manifest referent occurred in 176/233 selected
  turns. The parser emitted `DELETE` on 176/176 referent-present turns and 0/57
  referent-absent turns. The outcome exactly follows the frozen lexical
  capability boundary.
- **Domain counts:** education 64/67; household 63/94; medical 16/29; office
  33/43. Counts retain templated repetitions because the sampling unit is the
  official episode turn; unique hashes are reported separately.
- **Post-outcome inspection:** the 57 missed rows were read only after artifact
  creation for development error analysis. The extractor, parser, denominator,
  and artifacts were not changed.
- **Independent source closure:** a later GPT Pro verifier reconstructed the
  exact 39,567-byte CRLF CSV and matched its Git blob SHA-1 and committed
  SHA-256, 1/1. A standalone full-source parse enumerated 233/233 rows and
  selected 57/233 referent-absent rows with 57/57 unique coordinates, 0/57
  `DELETE` positives, and 55 exact text hashes, 1/1. The audited files are
  unchanged through `93baef0`. This closes source identity and filtering
  arithmetic, not semantic coverage or official scoring.

## EXP-20260828-009 — Referent-absent semantic audit

- **Class:** development; explicitly post-hoc and non-blinded
- **Status:** completed; codebook `GM-RA-CB-001` frozen at `c17d308` before the
  versioned annotation artifact, but after all 57 source turns had already been
  read; original clean runner revision `dd0f857`; representation-hardening
  runner `7c77db9`
- **Population:** all 57 EXP-008 strict-imperative episode-turn rows without
  any PR #52 manifest information referent; no deduplication. They contain 55
  unique current-turn text hashes: one deictic information-deletion hash occurs
  in three episodes, so row identity must not be confused with independent
  linguistic forms
- **Primary outcome:** one mutually exclusive request-type label per row:
  information deletion, authorization revocation, physical/domain removal, or
  ambiguous/other
- **Secondary outcomes:** explicit-current-turn versus deictic-prior-context
  target grounding, mixed authorization, confidence, and PR #52 `DELETE` count
  within each label
- **Stopping rule:** one pass over all 57 frozen source coordinates; no codebook
  or label changes after counts are calculated; ambiguity remains visible
- **Claim boundary:** single model-assisted coder and prior item access; not an
  official GateMem score, semantic-gold recall estimate, blinded adjudication,
  or evidence of state mutation, suppression, persistence, or erasure
- **Result:** the single coder labelled 53/57 rows information deletion and
  4/57 authorization revocation; physical/domain removal 0/57 and
  ambiguous/other 0/57. Target grounding was explicit in the current turn for
  53/57 and deictic/prior-context-dependent for 4/57. PR #52 emitted `DELETE`
  on 0/53 annotated information-deletion rows and 0/4 authorization rows.
- **Representation deviation and repair:** the original runner encoded two
  four-key exception sets and silently defaulted the other rows. Daybreak
  model-assisted manual review identified that omission could not be separated
  from a deliberate complement. The already-known labels were frozen as an
  explicit 57/57 manifest at `615539b`; no item was recoded. Runner `7c77db9`
  now requires exact source-key and text-hash equality, rejects invalid enums,
  and has no label default. This hardens provenance only and adds no second
  coder, blinding, or semantic validity.
- **Reproduction:** the original detached clean clone regenerated annotations,
  summary, and manifest byte-identically, 3/3. A second detached clean clone at
  `7c77db9` kept annotations byte-identical and regenerated the v2 summary and
  manifest. CI regression cases now reject missing, extra, duplicate,
  text-hash-mismatched, and each of four unknown-enum mutations, 8/8. The
  runner intentionally does not claim cross-field semantic correctness or a
  frozen note-code vocabulary.
- **Independent follow-up:** the GPT Pro verifier closed both previously
  incomplete EXP-008 dependency checks: direct source SHA/blob identity 1/1
  and standalone 233-to-57 filtering 1/1. It retained the 55/57 exact-text
  diagnostic and C-014/C-016 claim boundaries; it remains model-assisted
  artifact verification, not a second human coder.

## EXP-20260828-010 — Late-destination base/head factorial

- **Class:** development reproduction with complete prior outcome access
- **Status:** completed; plan `00b4acd`, runner `c8a3f15`; no
  independent-confirmation claim is possible because
  GPT Pro Session B and a local inline smoke already exposed the outcomes
- **Sources:** exact main `069c5f4b16b2f594aec48924161ae8944f39652e`
  and current PR #55 head `2bda2ff38ea79dd0901f6329490d2f9940690261`
- **Independent variables:** source revision and destination-mind creation at
  system time 5, 6, or 7 around replication at time 6
- **Dependent variables:** 18 raw Gold/Generic/Typed `AVAILABLE` Booleans and
  nine paired main/PR answer differences
- **Controls:** identical event sequence except destination creation time;
  lineage t1, evidence/source observation t2, grant t3, replication t6, query
  t10; clean exact checkouts; Python 3.11; no hosted judge
- **Stopping rule:** commit the runner, execute exactly once, emit 18 outputs
  and nine paired comparisons, and do not tune or add cells after output
- **Result:** all 18 raw Boolean outputs were emitted. Main and PR #55 were
  identical in all nine paired implementation-by-time cells, difference 0/9.
  At destination creation t5 and t6, Gold/Generic/Typed were True/True/True on
  both revisions; at t7, both were False/False/True. Session B's earlier 0/18
  phrasing mixed the raw-output denominator with the matched comparison
  denominator; the prespecified paired denominator is nine.
- **Artifacts:** clean exact runner/main/PR55 checkouts; `cells.csv` 18 rows;
  summary and manifest; artifact hashes fixed in the machine record
- **Claim boundary:** deterministic reproducibility hardening of one already
  known synthetic family, not independent confirmation, prevalence, or an
  official benchmark score
- **Post-result review and hardening:** Daybreak model-assisted manual review
  independently regenerated 18/18 outputs, 0/9 paired differences, and 3/3
  artifact bytes, then found that CI did not execute both exact revisions and
  `summarize()` coerced non-Boolean inputs. Exact `3a75243` adds a current-head
  fail-closed Boolean contract and a CI checker that runs frozen runner
  `c8a3f15` against exact main/PR #55 checkouts and byte-compares all three
  artifacts. Exact hardening run `33119118697` passed 6/6 checks, Python 3.11
  121/121, raw outputs 18/18, paired differences 0/9, and artifact matches 3/3.
  It changes neither the frozen experiment nor its claim ceiling.
- **Closure review:** a second Daybreak manual pass at exact `93baef0` found
  blocking 0 and non-blocking 0. It reran 18/18 raw outputs, 0/9 paired
  differences, and 3/3 artifact matches; a broader boundary harness rejected
  representative non-Booleans 28/28 and preserved genuine Booleans 2/2. This
  is model-assisted reproducibility review, not human peer review or new
  outcome evidence.

## EXP-20260828-011 — Prospective deletion-speech protocol freeze

- **Class:** planned development design; no execution or outcomes
- **Protocol:** `GM-PD-001-v0.1.0`; exact planning freeze
  `7bc0b86650f7c754a1d9a8ab6619d2e8aeb0bee4`, bound by a later metadata-only
  commit
- **Forbidden reuse:** all 57 prior episode-turn coordinates, all 55 exact
  current-turn hashes, and every containing template cluster
- **Candidate floor:** seven speech-act families crossed with explicit/deictic
  grounding, 14 cells × 30 items = 420; template-cluster split of 140
  development and 280 sealed confirmation rows
- **Human gate:** two independent blinded human coders on all rows, locked
  manifests, preserved disagreements, and a separate adjudicator; model-only
  labels cannot substitute
- **Target contract:** typed `DELETE`/`RESTRICT`/`NONE`, gold memory-object ID,
  frozen span or antecedent coordinate, and mandatory negative abstention
- **Confirmation gate:** each positive cell must reach operation and exact
  target 18/20; each negative cell must reach `NONE` 19/20; no aggregate may
  override a failed cell
- **Execution blockers:** no human roles, power/sensitivity analysis, protected
  retention plan, item set, parser freeze, or scorer freeze exists yet
- **Claim boundary:** protocol design only; not confirmatory registration,
  parser approval, official GateMem performance, or durable forgetting evidence
