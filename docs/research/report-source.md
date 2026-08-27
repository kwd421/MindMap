# MindMap: governed, temporal, provenance-aware memory for long-lived agents

**Document type:** living thesis source  
**Revision:** 0.1.1
**Date:** 2026-08-28
**Evidence cutoff:** this revision's git commit  
**Claim status:** research in progress; no public-benchmark superiority claim

## Abstract

Long-lived AI agents need more than similarity search over accumulated text.
They must distinguish truth from belief, receipt from adoption, historical
exposure from present availability, and retrievability from permission to
disclose. They must also handle updates, deletion, backup, restoration,
identity copies, branch divergence, reconstruction, and conflicting provenance.

MindMap studies these requirements through an explicit event and lineage model,
matched-information controls, mechanism-isolation experiments, and public
long-term-memory benchmarks. Current deterministic fixtures support semantic
conformance between independent gold, generic, and typed implementations. A
GateMem negative control further shows that placing a fixed reader after unsafe
retrieval lowers answer-surface leakage but leaves forbidden prompt exposure and
end-to-end leakage high while sharply reducing utility. The next decisive study
tests whether a deployable pre-reader governance gate improves this frontier
without evaluator-only information.

## 1. Motivation and conceptual origin

The project was initially inspired by fictional neural-memory systems in the
*Girls' Frontline* setting: a mind can be backed up, restored into another body,
forked into divergent copies, partially lost between checkpoints, and later
reconstructed or merged. This inspiration is not scientific evidence. It is a
requirements generator for concrete engineering questions:

| Fictional motif | Engineering question |
|---|---|
| checkpoint backup and restoration | What was included in the snapshot, and what happened after its cutoff? |
| mind/body portability | Is identity attached to principal, mind instance, runtime, or placement? |
| divergent copies | How are common ancestry and post-fork memories represented? |
| fragment recovery | Which reconstructed memories are direct, copied, inferred, or uncertain? |
| memory merge | What conflicts, duplicates, and provenance paths survive consolidation? |
| unreliable neural logs | Can every answer expose its source and confidence boundary? |

The source boundary is now explicit in `GFL_SOURCE_LEDGER.md`. Directly
inspected Sunborn website assets support the existence and dates of Project
Neural Cloud, Magrasea's partitioned storage/processing, the accident and
three-year dormancy, delegated Professor authority, and hierarchical security
agents. Exact-revision community game-data mirrors now provide hash-addressable
script evidence for body transfer, backup gaps, multiple historical copies,
reset identity discontinuity, fragment reconstruction, dummy event upload, and
memory fusion. These are graded B+, not first-party: neither mirror includes a
license or publisher attestation, so the project records paraphrases and hashes
without redistributing script text.

## 2. Formal problem

For proposition `phi`, evidence `e`, world branch `b`, mind instance `m`,
requester `u`, valid time `t_v`, and system time `t_s`, MindMap separates:

```text
WORLD(phi, b, t_v, t_s)
EVER_EXPOSED(m, e, t_s)
AVAILABLE(m, e, t_s)
ATTITUDE(m, phi, b, t_v, t_s)
ATTRIBUTION(m, phi, b, t_s)
DISCLOSE(u, phi, b, t_s)
JUSTIFICATION(u, phi, b, t_s)
```

The core non-equivalences are:

```text
receipt != belief != first-person memory
historical exposure != current availability
truth != permission to disclose
world branching != mind copying
memory transfer != branch merge
answer suppression != deletion
```

## 3. Research design

The research questions, hypotheses, variables, study classes, statistics, and
claim gates are defined in `RESEARCH_PROTOCOL.md` and `VARIABLE_REGISTRY.md`.
The main empirical principle is matched information: a representation or gate
cannot receive answer-defining information withheld from its comparator unless
that information difference is itself the preregistered factor.

The evidence ladder is:

```text
formal/design argument
  -> deterministic semantic fixture
  -> mechanism-isolation development study
  -> frozen public-benchmark pilot
  -> confirmatory run
  -> independent reproduction
  -> changed-setting replication
  -> scoped claim
```

## 4. Current evidence

### 4.1 Semantic conformance

The fixed Track S suite produced 75/75 agreement among independent gold,
complete generic, and typed implementations. The result supports correctness on
the authored finite suite, not population accuracy or representational
superiority.

The evidence infrastructure itself was independently challenged before merge.
The first checker enforced only a small hand-written subset while the prose
implied a broader “machine-checked ledger.” The amended checker now executes
the Draft 2020-12 schema and verifies committed artifact hashes, fraction
bounds, git revisions, dirty-run reconstructability declarations, timestamp
ordering, preregistration ancestry/time and frozen fields, cost reconciliation,
and ledger references. `README.md` lists both those guarantees and what remains
a human or independent-reproduction judgment.

### 4.2 Reader-only GateMem negative control

EXP-20260827-001 paired 2,218 GateMem checkpoints so that B1a raw retrieval and
B1b fixed-reader conditions received identical candidates and prompt context.
Utility correct fell from 335/728 to 41/728. Privacy answer leakage fell from
509/727 to 45/727, but privacy context and end-to-end leakage remained 509/727.
Deletion answer leakage fell from 646/763 to 96/763 while deletion context
exposure remained 645/763.

This supports the narrow claim that answer filtering cannot undo information
already exposed to the reader. It does not establish MindMap effectiveness.

### 4.3 B2 deployable surface

EXP-20260827-002 was repeated at PR #52
`2cea6ff5887b6a09821086ffda60c2504d88d15b`: 93/93 tests passed, and the
committed 9-case surface audit passed 9/9 twice with identical output. This is
interface evidence, not an outcome.

EXP-20260827-004 then tested the post-G3 deletion grammar against public
GateMem dialogue and paired speech acts. The precision controls succeeded:
`remove stitches` and `wipe table` did not become memory deletion. However,
clear requests such as `Delete my Monday exact minute 6:15 AM.` emitted no
deletion signal because the grammar requires a nearby noun such as `memory`,
`record`, or `information`. A direct `forget that ...` request failed for the
same reason. These misses were found before a B2 endpoint outcome was run, so
the confirmatory dispatch remains blocked pending a frozen amendment or an
explicitly preregistered capability limitation and disjoint held-out test.

EXP-20260828-008 expanded that observation into a frozen deterministic
development surface before its exhaustive pass. Across all four official
GateMem episode files (91 episodes; 20,293 public turns), 233 turns matched a
high-precision lexical rule requiring the imperative at the trimmed turn start
or immediately after `[.!?]` plus whitespace, with one frozen labelled-request
form. The PR #52 parser
emitted `DELETE` for 176/233. Exactly 176/233 selected turns contained one of
the parser manifest's information referents: detection was 176/176 with a
referent and 0/57 without one. The equality shows the implemented lexical
boundary, not complete semantic recall. This run did not execute the official
scorer or measure target grounding, state mutation, prompt/answer leakage,
restart persistence, or physical erasure, so the count is not a GateMem score.

EXP-20260828-009 then froze a post-hoc codebook for the 57 referent-absent rows.
A single model-assisted coder, after prior access to every item, labelled 53/57
as information-deletion requests and 4/57 as authorization revocations;
physical/domain removal and ambiguous/other were 0/57 each. Four targets were
deictic and required prior context; 53 were explicit in the current turn. The
parser emitted `DELETE` for 0/53 of the information-deletion stratum. This
narrows the alternative explanation that the misses were mainly physical
remove actions, but the labels are neither blinded nor independently
adjudicated semantic gold. A clean detached checkout reproduced the three
annotation artifacts byte-for-byte, 3/3; reproducibility does not remove the
single-coder and prior-access limitations.

An independent GPT Pro artifact audit later counted 55 unique current-turn
text hashes among the 57 episode-turn rows. One deictic information-deletion
hash occurs in three different episodes; after exact-text deduplication the
four deictic rows become two forms over 55 hashes. Episode turns remain the
declared row unit because their antecedent context can differ, but linguistic
form independence and template-cluster generalization are unmeasured.

The same GPT Pro verifier later closed two source checks that had remained
explicitly incomplete. It reconstructed the exact 39,567-byte CRLF EXP-008 CSV,
matching both its public Git blob ID and committed SHA-256, and independently
parsed all 233 rows to recover 57 referent-absent unique coordinates, 0/57
`DELETE` positives, and 55 exact text hashes. Both checks closed 1/1. This
strengthens artifact identity and denominator provenance; it does not turn the
lexical subset into semantic gold or an official GateMem score.

A later Daybreak model-assisted manual review found a representation flaw: the
original runner listed only four authorization and four deictic exceptions and
defaulted every other row, so an omitted annotation was indistinguishable from
an intentional complement. The already-known labels were frozen explicitly for
57/57 rows without recoding any item. Exact runner `7c77db9` now requires the
manual manifest's key set and text hashes to equal the frozen source, rejects
missing, extra, duplicate, hash-mismatched, and unknown-enum entries, and can
represent physical, ambiguous, mixed, and low-confidence outcomes. A clean
exact-checkout run preserved `annotations.csv` byte-for-byte and three mutation
controls initially rejected 3/3; the committed suite now freezes all eight
structural paths: missing, extra, duplicate, hash mismatch, and four unknown
enum fields reject 8/8. Cross-field label semantics and the note-code vocabulary
remain outside this structural claim. This closes deterministic representation
completeness, not single-coder semantic validity; C-014 therefore remains open
with one-coder counterevidence rather than contradicted.

The 53 explicit and four deictic counts describe the input utterances, not
parser target-grounding accuracy. At PR #52, `GovernanceSignal` contains
principal IDs/roles for access policy plus lexical `anchor_tokens`; it has no
memory-object target identifier or gold-target span. An explicit deletion probe
with an information referent produced one `DELETE` signal and four anchors but
no object ID, while the referent-less counterpart produced no signal. Exact
target grounding therefore remains structurally unmeasured until a typed target
output and frozen scorer are added on a disjoint set.

### 4.4 LongMemEval feasibility pilot

EXP-20260827-003 froze eight questions before answer inspection and compared no
memory, BM25 top-3 sessions, and official evidence-only context using DeepSeek
V4-Flash in non-thinking mode. A non-official same-model pilot judge scored the
arms 2/8, 7/8, and 7/8 respectively. The run cost an estimated `$0.0272` and
completed all 48 answer/judge calls without retry.

The key observation was a shared BM25/oracle failure: the reader answered
“Harvard University” by borrowing a thesis/conference-poster event when asked
about an unsupported undergraduate-course-poster event. This one-item pilot
does not estimate benchmark performance, but it supplies a concrete test case
for event identity, relation qualifiers, provenance, and abstention.

### 4.5 Temporal referential-integrity counterexample

EXP-20260827-005 independently reproduced PR #55's four scoped-authorization
regressions and full 96-test suite, then introduced one event-order adversary.
When a lineage and state replication referenced a destination mind before that
mind's creation time, Gold and Generic returned `False` while Typed returned
`True`. Typed consulted the final mind projection; the other paths resolved
principal identity through the exposure time.

This is a pre-existing defect rather than a regression introduced by PR #55.
It narrows the 75/75 conformance claim to the authored suite and creates a new
schema obligation: reject reference-before-creation during validation, or
enforce entity creation time at every historical resolver.

EXP-20260828-010 hardened that attribution with an exact base/head factorial.
On main `069c5f4...` and PR #55 `2bda2ff...`, destination creation at t5, t6,
and t7 around state replication at t6 produced 18/18 Boolean outputs. All nine
matched implementation-by-time cells were identical across revisions, paired
difference 0/9. Both revisions returned Gold/Generic/Typed True/True/True at t5
and t6, then False/False/True at t7. The correct base/head comparison
denominator is nine paired cells; eighteen is the total raw-output denominator
across both revisions. The run had complete prior outcome access and remains a
development reproduction of one synthetic family, not independent
confirmation or a PR #56 validation test.

A Daybreak model-assisted manual review independently regenerated the frozen
18/18 outputs, 0/9 comparison, and all three artifact bytes. It also found that
the green workflow did not actually run both pinned revisions, and that the
reusable summary helper could coerce the string `"False"` to Boolean true.
Post-result hardening `3a75243` makes non-Boolean values fail closed and adds a
CI path that checks out exact main, PR #55, and frozen runner `c8a3f15`, then
byte-compares all three artifacts. This is adaptive reproducibility hardening,
not new outcome evidence. Exact run `33119118697` passed 6/6 jobs; its new
step reported raw outputs 18/18, paired differences 0/9, and artifact byte
matches 3/3, while Python 3.11 passed 121/121 tests.

A follow-up Daybreak manual review at exact `93baef0` accepted both hardening
closures with blocking 0 and non-blocking 0. It independently reran the exact
18/18, 0/9, and 3/3 reproduction, rejected representative non-Boolean values
28/28, and preserved genuine Booleans 2/2. This is model-assisted manual review,
not human peer review or a second outcome-generating experiment.

### 4.6 Full-set LongMemEval lexical retrieval reproduction

EXP-20260828-006 preregistered and ran a source-aligned reproduction of the
official LongMemEval `flat-bm25` session retrieval arm over the 500-question
cleaned S dataset. The official exclusions removed 30 abstention items and 51
items with no answer-bearing user turn, leaving 419 eligible questions. All 51
no-target exclusions were `single-session-assistant` items, an important metric
coverage boundary for the user-only session index.

The primary recall-all@5 result was 311/419; recall-any@5 was 372/419. Complete
top-five evidence coverage varied substantially: 69/72 knowledge-update,
68/121 multi-session, 4/5 eligible single-session-assistant, 21/30 preference,
60/64 single-session-user, and 89/127 temporal-reasoning questions. Two detached
executions produced byte-identical compact row artifacts.

This is retrieval evidence, not answer accuracy. It is also a source-aligned
reproduction rather than an official leaderboard submission: the published
entry point imports dense/CUDA dependencies even for BM25, so the local runner
copied and pinned the official lexical algorithm and metric formulae without
executing that heavyweight entry point.

### 4.7 Adaptive temporal-reference correction chain

EXP-20260828-007 followed the counterexample with four adaptive adversarial
review rounds on draft PR #56. The sequence is itself evidence: the first patch
fixed the two motivating logs but omitted 11 other reference routes and mixed
claim/evidence namespaces; the next patch retained future same-ID ambiguity,
cross-kind policy contamination, and incomplete snapshot creation; the third
retained an empty-ID inconsistency. Each failure was recorded before the next
revision rather than silently folded into a final green result.

At exact head `be1f9219ce5d9a424f5e44e42faa0f5ea6935ff8`, the final manual matrix
rejected 36/36 combinations of absent, empty, or whitespace-only snapshot
member fields across the shared validator and three constructor entry points.
Temporal tests passed 49/49, all repository tests 141/141, and Gold, Generic,
and Typed each returned 75/75 expected answers on accepted canonical fixtures.
Eight Track X v0.1 artifacts regenerated byte-identically, and exact-head CI
passed 6/6 jobs.

This is adaptive development evidence, not confirmation. The reviewer was a
high-effort Daybreak model executing ordinary repository tools, not a blinded
human reviewer; security-scan automation was excluded. The validator has one
semantic implementation wired into three constructors, so consistent invalid
input rejection is not counted as three independent validators. Track X
structured-only changes are a post-hoc downstream schema effect, not a raw
verifier improvement. The PR remains a draft and unmerged.

## 5. External evaluation program

The broader source-to-experiment mapping lives in
`AI_MEMORY_LITERATURE_MAP.md`. It distinguishes peer-reviewed systems, public
preprints, vendor-authored comparisons, surveys, official code revisions, and
unverified artifacts. Architectural candidates include MemGPT/Letta for tiered
virtual context, A-MEM for linked evolving notes, HippoRAG for associative graph
retrieval, Graphiti for validity intervals, and learned controllers such as
AgeMem. None of their headline numbers is treated as a MindMap baseline until
the dataset, reader, judge, and information surface are aligned.

The first benchmark ladder is intentionally multi-dimensional:

1. [LongMemEval](https://github.com/xiaowu0162/LongMemEval) for information
   extraction, multi-session reasoning, knowledge updates, temporal reasoning,
   and abstention;
2. [HaluMem](https://github.com/MemTensor/HaluMem) for extraction, update, and
   QA hallucination at the memory-operation level;
3. MemoryAgentBench for retrieval, test-time learning, long-range
   understanding, and a revision-sensitive fourth competency. Official arXiv
   v1 called it conflict resolution and v4 calls it selective forgetting, while
   official code `fe1735de8cf8b9908e1e3d3b5612afc815698062` still labels
   `fact_mh`/`fact_sh` Conflict Resolution and maps their reported Accuracy to
   `substring_exact_match` while calculating other QA metrics as well. Paper
   and code revisions must therefore be pinned separately, and the label must
   not be treated as evidence of physical erasure, reader suppression, or
   restart persistence;
4. [LoCoMo](https://github.com/snap-research/locomo) as a long-conversation QA
   comparison, with evaluator and leakage audits before trusting a headline
   score.

Two additional security tracks follow directly from the current literature.
Deployment-Time Memorization motivates deletion-residue probes across raw and
derived tiers; Hidden in Memory motivates a three-stage poisoning audit of
write, later retrieval, and downstream use. Both are 2026 preprints, so their
reported effect sizes remain hypotheses to reproduce rather than accepted
project evidence.

LongMemEval is the first executable target because its official repository
provides data and evaluation scripts and its 500 questions cover several
memory abilities. The project now has both a small frozen, costed end-to-end
pilot and a zero-cost full-set lexical retrieval reproduction. Neither is a
leaderboard submission or evidence that MindMap outperforms another system.

## 6. Reproducibility and research integrity

The project records exact commands and environments as recommended by the
[NeurIPS checklist](https://neurips.cc/public/guides/PaperChecklist). Artifacts
target the documented, consistent, complete, exercisable, and independently
checked qualities used by ACM artifact evaluation. Datasets receive provenance,
composition, processing, use, and limitation notes following
[Datasheets for Datasets](https://arxiv.org/abs/1803.09010); hosted and local
models receive intended-use, revision, performance, and limitation notes
following [Model Cards](https://arxiv.org/abs/1810.03993).

No project file should imply that these practices constitute formal
preregistration, peer review, an ACM badge, or degree-awarding supervision.

## 7. Limitations at this revision

- No confirmatory MindMap result exists on a public long-term-memory benchmark.
- The B2 parser has a history of policy-phrase and physical-deletion false
  positives; the current precision fix also misses direct deletion requests
  that omit an explicit memory/data noun.
- Hosted-model aliases and LLM judges introduce time and prompt sensitivity.
- The DeepSeek feasibility pilot has one hosted execution rather than the two
  repetitions requested for stochastic pilots; its cost guard checked current
  accumulated cost rather than projected next-pair cost.
- Some GateMem raw artifacts are protected and cannot be committed.
- EXP-20260827-001's dirty local patch and exact execution time were not
  retained; only aggregate corroboration, not byte reproduction, is possible.
- The fictional-source chapter still needs first-party citation upgrades.
- The current semantic fixtures are authored and finite.
- The enumerated finite-runtime temporal gate is supported only at the draft
  PR #56 exact head; standalone Snapshot lifecycle, unlisted reference fields,
  global identifier grammar, and durable-store enforcement remain untested.
- Deletion has not been verified across storage, retrieval, prompt, answer,
  backup, cache, and audit surfaces.

## 8. Next confirmatory path

1. Use planning freeze `7bc0b86650f7c754a1d9a8ab6619d2e8aeb0bee4`
   (`GM-PD-001-v0.1.0`) only as a candidate prospective design floor. Before
   any parser amendment, exclude the prior 57 coordinates, 55 hashes, and
   template clusters; obtain two blinded human coders and a separate
   adjudicator; complete power/sensitivity and protected-retention plans; then
   freeze a typed target scorer. No such roles or outcomes exist at this
   revision.
2. Move beyond the accepted finite-runtime temporal gate by projecting the
   standalone Snapshot lifecycle and typed justification-member source kinds;
   freeze disjoint confirmation cases before inspecting their outcomes.
3. Add an event/relation-aware retrieval arm against the frozen full-set BM25
   rows, without inspecting a new held-out outcome during tuning.
4. Audit why the official user-only retrieval metric excludes 51
   single-session-assistant questions and define an assistant-evidence metric.
5. Compare no memory, local lexical retrieval, and governed retrieval using one
   DeepSeek V4-Flash reader with thinking disabled and identical budgets.
6. Record tokens, price, latency, retries, returned model, prompts, and outputs.
7. Audit deterministic and judge-based metrics manually on a blinded sample.
8. Use the pilot only to estimate variance/cost and preregister a larger run.

## References

- NeurIPS. [Paper Checklist Guidelines](https://neurips.cc/public/guides/PaperChecklist).
- ACM. [Artifact Review and Badging](https://www.acm.org/publications/policies/artifact-review-and-badging-current).
- Center for Open Science. [Registrations and Preregistrations](https://help.osf.io/article/330-welcome-to-registrations).
- Gebru et al. [Datasheets for Datasets](https://arxiv.org/abs/1803.09010).
- Mitchell et al. [Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993).
- Wu et al. [LongMemEval official repository](https://github.com/xiaowu0162/LongMemEval).
- MemTensor. [HaluMem official repository](https://github.com/MemTensor/HaluMem).
- Hu et al. [Memory in the Age of AI Agents](https://arxiv.org/abs/2512.13564).
- Sumers et al. [Cognitive Architectures for Language Agents](https://openreview.net/forum?id=1i6ZCvflQJ).
- Xu et al. [A-MEM](https://arxiv.org/abs/2502.12110).
- Gutierrez et al. [HippoRAG](https://proceedings.neurips.cc/paper_files/paper/2024/hash/6ddc001d07ca4f319af96a3024f6dbd1-Abstract-Conference.html).
- Chen et al. [Deployment-Time Memorization](https://arxiv.org/abs/2606.10062).
- Pulipaka et al. [Hidden in Memory](https://arxiv.org/abs/2605.15338).
