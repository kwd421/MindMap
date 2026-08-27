# MindMap research record

This directory is the canonical research record for MindMap. It is written so
that a reader who did not participate in the project can distinguish a design
idea, a pilot observation, a reproduced result, and a supported claim.

## Read this first

1. `report-source.md` is the living thesis-style source document.
2. `RESEARCH_PROTOCOL.md` defines the research and claim gates.
3. `VARIABLE_REGISTRY.md` fixes variables, metrics, and known confounders.
4. `EXPERIMENT_LEDGER.md` is the append-only human-readable experiment index.
5. `CLAIM_EVIDENCE_LEDGER.md` links every public claim to supporting and
   counter-evidence.
6. `GFL_SOURCE_LEDGER.md` separates first-party setting evidence, traceable
   community synthesis, and engineering inference.
7. `AI_MEMORY_LITERATURE_MAP.md` maps papers and exact public artifacts to
   falsifiable project requirements and planned comparisons.
8. `GATEMEM_PROSPECTIVE_DELETION_PROTOCOL.md` freezes the current disjoint
   human-coding and target-grounding gate; it has no outcomes yet.
9. `COST_LEDGER.csv` records local and paid-model cost.
10. `records/` contains one machine-readable manifest per experiment.

The record borrows its controls from the NeurIPS paper checklist, ACM artifact
evaluation, OSF preregistration, Datasheets for Datasets, and Model Cards. It is
not an institutional preregistration or an ACM badge application.

## Non-negotiable rules

- Never overwrite an experiment record. Amend it with a dated addendum.
- Never promote a smoke test or development pilot to a confirmatory result.
- Record negative results and protocol deviations.
- Pin source, data, model, prompt, evaluator, and environment revisions.
- Keep evaluator-only labels outside the deployable method information surface.
- Separate source revision from CI synthetic merge/checkout revision.
- Report raw counts and denominators with percentages.
- Report answer, prompt-context, and end-to-end leakage separately.
- Do not commit API keys, protected raw benchmark data, or private chat content.

## Source standards

Research-practice sources:

- [NeurIPS Paper Checklist](https://neurips.cc/public/guides/PaperChecklist)
- [ACM artifact review and badging](https://www.acm.org/publications/policies/artifact-review-and-badging-current)
- [OSF registrations and preregistrations](https://help.osf.io/article/330-welcome-to-registrations)
- [Datasheets for Datasets](https://arxiv.org/abs/1803.09010)
- [Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993)

Benchmark claims should cite the official repository and paper. Community
reviews are useful audit leads, but they are not treated as result evidence
until the underlying code or artifact is checked directly.

## What the checker actually guarantees

`python tools/check_research_records.py` now applies the Draft 2020-12 schema
and project semantic checks. A green result means:

- every record passes the committed schema and has no undeclared top-level
  fields;
- numerator/denominator pairs are integral, positive-denominator, and bounded;
- declared artifact files exist inside the repository and match SHA-256;
- source and checkout revisions resolve as local commits;
- dirty runs declare either a verifiable patch artifact or explicit
  unreconstructability;
- exact timestamps are ordered, while unknown timestamps are explicitly
  marked rather than replaced by midnight placeholders;
- confirmatory and reproduction records contain a non-null preregistration
  anchor;
- a declared preregistration commit contains the record, descends from the
  source revision, predates the run, and preserves method arms, models,
  controls, sample, primary outcome, and stopping rule;
- the cost ledger has exactly one reconciled row per experiment;
- experiment-ledger headings and claim-ledger references resolve to manifests.

It does **not** prove that an external dataset or model matches its claimed
identity when the bytes are unavailable, that an LLM judgment is correct, that
the recorded command was actually executed, or that a study design is valid.
Those require retained artifacts, independent review, and reproduction. The
schema and checker are versioned research infrastructure, not an institutional
registry or tamper-proof timestamp service.
