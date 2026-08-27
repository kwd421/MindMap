# MindMap — Runnable Neural-Cloud Memory Research Core

MindMap is a research repository for long-horizon agent memory inspired by the **mindmap / neural-cloud** metaphor. The implemented core models a persistent, versioned software mind rather than a visual mind-map diagram.

The central semantic rule is:

> **world truth ≠ a principal's belief ≠ first-person memory ≠ current disclosure permission**

The code therefore keeps world state, possession/exposure, availability, attitude, attribution, policy, provenance, valid time, transaction time, world branch, and mind-instance lineage as separable concepts.

## Repository status

This branch is an **installable deterministic research prototype**. It is not a production memory service and it is not a public-benchmark SOTA claim.

The runnable v0.2 core was integrated into `main` through reviewed PR #49. The merge commit is `069c5f4b16b2f594aec48924161ae8944f39652e`; post-merge package, distribution, and deterministic-reproduction checks passed on that exact commit.

Implemented and executable here:

- a Python package under `src/mindmap/`;
- independent declarative gold semantics for the canonical fixture suite;
- complete generic and normalized typed reference ledgers;
- branch, mind-copy, attribution, policy, availability, bitemporal, and alternative-support fixtures;
- deterministic semantic-conformance and Track X mechanism tests;
- synthetic raw-evidence/verifier experiments with explicit information firewalls;
- a development-only candidate → context gate → prompt → answer audit;
- committed compact result artifacts and GitHub Actions verification.

Not integrated or not yet established here:

- Track E observer/physical-fault packages from draft PRs #36/#37;
- a production database, server, or multi-user deployment;
- an unrestricted LLM extraction and answer pipeline;
- a held-out natural-language generalization result for Track X v0.2;
- superiority over an equal-information generic event ledger;
- a public GateMem/LoCoMo/LongMemEval architecture result;
- a universal benefit from always-on graph retrieval.

Public GateMem endpoint work remains in separate reviewed/review-gated PRs #46/#47/#50. Those endpoint controls do **not** constitute a MindMap effectiveness result. Pending Track E heads are preserved in `docs/LOST_WORK_REGISTER.md` rather than silently absorbed into this release.

## Quick start

Requirements:

- Python 3.11 or newer;
- Git;
- no API key for the deterministic core below.

Clone the runnable default branch:

```bash
git clone https://github.com/kwd421/MindMap.git
cd MindMap
python -m venv .venv
```

Activate the environment, then run:

```bash
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python tools/check_repository_contract.py
python -m pytest -q
```

`release_contract_v0_2.json` is the machine-readable **enumerated v0.2 release contract**. The checker validates every path, command, status statement, stale-claim guard, result entry, Python declaration, package metadata field, and license rule listed in that manifest. It does not claim to infer arbitrary future prose references that have not been added to the manifest.

## Reproduce the stable deterministic core

### 1. Canonical semantic conformance

```bash
python experiments/s_track_conformance.py
```

This checks that the independent gold interpreter, complete generic ledger, and normalized typed ledger agree on the fixed canonical semantics. Equality is the expected result under equal information.

Reproducibility contract: **semantic regeneration / zero disagreement**. The Track S summary can include Python/platform identity, so this is not a cross-environment byte-identity claim.

### 2. Track X v0.1 raw-verifier mechanism audit

```bash
python experiments/track_x_v01.py --output-dir /tmp/track_x_v01
```

This is a deterministic information-firewall and mechanism audit. Its templates and controlled faults are not unrestricted natural language and must not be reported as production accuracy.

Reproducibility contract: **committed artifact drift comparison** for the declared v0.1 CSV/JSON outputs.

### 3. Track X v0.3 development context-gate audit

```bash
python experiments/track_x_v03_context_gate_p0.py --output-dir /tmp/track_x_v03_context_gate
```

This development-only audit separates:

```text
R  candidate evidence before governance
G  pre-reader verification/gating
P  evidence actually admitted to the prompt surface
A  downstream answer/use
```

It reads Session-B development passages only. It is not a Session-A-held-out or public-benchmark result.

Reproducibility contract: **same-environment deterministic double-run plus held-out boundary**. The dedicated workflow requires `heldout_read=false` and checks its frozen row/topology invariants.

## What the deterministic results mean

A clean symbolic system reaching 100% means only that the implementation satisfies the frozen semantics or controlled fixture contract. It does **not** estimate real conversational accuracy.

The evidence hierarchy is:

1. unit and conformance tests;
2. deterministic synthetic mechanism audits;
3. independently authored held-out synthetic text;
4. protected public-benchmark endpoint controls;
5. matched end-to-end comparisons with one frozen extractor/reader and equal budgets;
6. production evidence.

Only levels actually completed may be claimed.

## Actual repository layout

```text
.github/workflows/              CI and declared reproduction checks
archive/                        superseded research drafts
data/                           synthetic development/freeze metadata
docs/                           protocols, status, audits, lost-work register
experiments/                    executable controlled studies
results/                        compact committed deterministic artifacts
src/mindmap/                    installable reference implementation
tests/                          semantic and experiment invariants
tools/                          release/distribution contract checks
LICENSE                         MIT license text
pyproject.toml                  package and distribution metadata
release_contract_v0_2.json      enumerated runnable-release contract
PREREG_V0_2.md                  current preregistration candidate
SCHEMA_V0_2.md                  current canonical schema candidate
```

There is no active `benchmarks/` directory in this runnable core. Public benchmark data remain external and pinned by the relevant protected-runner work rather than copied into this repository.

## Main research tracks

### Track S — semantic conformance

Question: do complete equal-information generic and typed implementations compute the same finite semantics?

Expected result: equality. A typed oracle advantage would indicate unequal information, unequal validators, or an implementation defect.

### Track E — lifecycle and fault behavior

The canonical Track E P0/P1 implementations are **not integrated in `main`**. They remain review-gated in draft PRs #36/#37 at the exact heads recorded in `docs/LOST_WORK_REGISTER.md`.

Their research question is which faults are observable, preventable, localizable, repairable, or non-identifiable under declared witnesses. Comparative claims belong to enforcement, repair blast radius, residue, concurrency, auditability, or cost—not abstract schema expressiveness.

### Track X — raw evidence and external validity

Question: under identical input capability, model, prompt, retrieval budget, answer budget, retry budget, and cost accounting, which pre-generation memory mechanisms improve permitted evidence delivery while preventing unauthorized, deleted, stale, or cross-branch evidence from entering generation?

Synthetic Track X tests fine-grained mechanisms. Public Track X tests external realism. Neither substitutes for the other.

## Development discipline

- Gold answers must not be generated by the system being evaluated.
- `receipt`, `belief`, and `first-person attribution` remain distinct.
- Correct `refuse` and `no_memory` actions are not generic uncertainty abstentions.
- Stateful benchmark methods require checkpoint-isolated replay or verified snapshot clones.
- Raw evidence and every derived claim retain provenance.
- Corrections create revision history rather than silent overwrite.
- Null, generic-favourable, and falsifying outcomes remain visible.
- CI executes the commands advertised in this README.

## License

The executable research core is released under the MIT License. See `LICENSE`.

See `docs/IMPLEMENTATION_STATUS.md` for the exact implemented/proven boundary, `docs/LOST_WORK_REGISTER.md` for intentionally excluded pending research, and `PREREG_V0_2.md` for the current experimental hypotheses and stopping rules.
