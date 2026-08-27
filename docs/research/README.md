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
6. `COST_LEDGER.csv` records local and paid-model cost.
7. `records/` contains one machine-readable manifest per experiment.

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
