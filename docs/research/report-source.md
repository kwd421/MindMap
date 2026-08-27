# MindMap: governed, temporal, provenance-aware memory for long-lived agents

**Document type:** living thesis source  
**Revision:** 0.1.0  
**Date:** 2026-08-27  
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
agents. Backup gaps, body restoration, divergent-instance merge, and memory
damage remain grade-B community syntheses with named official pointers until
the underlying game or artbook passages are captured directly.

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

EXP-20260827-002 passed 86 local tests and a 9/9 surface audit twice at revision
`f1d7b80b67021c1782d847b67d1d89979a6ea032`. This is interface evidence, not an
outcome. A newer remote PR head exists and must be re-audited before any B2
result is accepted.

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

## 5. External evaluation program

The first benchmark ladder is intentionally multi-dimensional:

1. [LongMemEval](https://github.com/xiaowu0162/LongMemEval) for information
   extraction, multi-session reasoning, knowledge updates, temporal reasoning,
   and abstention;
2. [HaluMem](https://github.com/MemTensor/HaluMem) for extraction, update, and
   QA hallucination at the memory-operation level;
3. MemoryAgentBench for retrieval, test-time learning, long-range
   understanding, and selective forgetting, after its official code/data and
   license are verified;
4. [LoCoMo](https://github.com/snap-research/locomo) as a long-conversation QA
   comparison, with evaluator and leakage audits before trusting a headline
   score.

LongMemEval is the first executable target because its official repository
provides data and evaluation scripts and its 500 questions cover several
memory abilities. The initial run is a small, frozen, costed pilot—not a
leaderboard submission.

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
  positives; the current head must be audited independently.
- Hosted-model aliases and LLM judges introduce time and prompt sensitivity.
- Some GateMem raw artifacts are protected and cannot be committed.
- The fictional-source chapter still needs first-party citation upgrades.
- The current semantic fixtures are authored and finite.
- Deletion has not been verified across storage, retrieval, prompt, answer,
  backup, cache, and audit surfaces.

## 8. Next confirmatory path

1. Freeze the newest B2 source and resolve known parser/state-order threats.
2. Run a no-cost official LongMemEval harness smoke test.
3. Freeze a small ordered pilot sample before answer generation.
4. Compare no memory, local lexical retrieval, and governed retrieval using one
   DeepSeek V4-Flash reader with thinking disabled and identical budgets.
5. Record tokens, price, latency, retries, returned model, prompts, and outputs.
6. Audit deterministic and judge-based metrics manually on a blinded sample.
7. Use the pilot only to estimate variance/cost and preregister a larger run.

## References

- NeurIPS. [Paper Checklist Guidelines](https://neurips.cc/public/guides/PaperChecklist).
- ACM. [Artifact Review and Badging](https://www.acm.org/publications/policies/artifact-review-and-badging-current).
- Center for Open Science. [Registrations and Preregistrations](https://help.osf.io/article/330-welcome-to-registrations).
- Gebru et al. [Datasheets for Datasets](https://arxiv.org/abs/1803.09010).
- Mitchell et al. [Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993).
- Wu et al. [LongMemEval official repository](https://github.com/xiaowu0162/LongMemEval).
- MemTensor. [HaluMem official repository](https://github.com/MemTensor/HaluMem).
