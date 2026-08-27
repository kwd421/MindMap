# MindMap Implementation Status

**Status:** runnable-core integration candidate  
**Coordination hubs:** Issue #7 for canonical/lifecycle work; Issue #4 for public Track X  
**Source integration point:** `research/track-x-v0.3-context-gate-p0@28937e0aa5aca410d32a77fe3a3ac24508feb6be`

## 1. Why this document exists

The previous default `main` branch contained research documents and the original collision audit, while its README described package, test, and experiment paths that existed only on research branches. An external reader following the default README would therefore fail before reaching the implemented reference code.

This integration candidate fixes that release-surface defect. It does not manufacture a new scientific result. It exposes one coherent, installable snapshot and labels each artifact by what it actually establishes.

## 2. Current implementation matrix

| Component | Present | Executable/tested contract | What it establishes | What it does not establish |
|---|---:|---|---|---|
| Python package / `pyproject.toml` | yes | editable install and wheel build | repository is installable | production deployment readiness |
| Canonical event model | yes | unit and conformance tests | frozen finite semantics can be represented | natural-language extraction quality |
| Independent gold interpreter | yes | compared against generic and typed code paths | avoids resolver self-agreement in canonical fixtures | a population estimate |
| Complete generic ledger | yes | clean canonical agreement | equal-information generic control | lower engineering cost in every deployment |
| Normalized typed ledger | yes | clean canonical agreement | typed implementation of the same semantics | intrinsic oracle superiority |
| Track S conformance | yes | deterministic regenerated result | implementation agreement on fixed fixtures | real conversational accuracy |
| Track E observer/fault families | code in the integrated stack | unit/fixed-suite contracts | observability and omission boundaries | database-scale concurrency or production repair |
| Track X v0.1 raw verifier | yes | deterministic output drift checks | information-firewall/mechanism plumbing | unrestricted natural language |
| Track X v0.2 authored development bundles | yes | schema/authorship/freeze tests | independent-authorship protocol and development surface | Session-A held-out result |
| Track X v0.3 context-gate P0 | yes | development-only deterministic double-run | candidate → gate → prompt → answer decomposition | learned gate or public benchmark effect |
| Public GateMem endpoint controls | separate PRs #46/#47 | official protected scorer and independent reproduction | deterministic endpoint/provenance controls | MindMap architecture effectiveness |
| LoCoMo/LongMemEval matched architecture study | no accepted result | protocol only | future external-validity target | any current public SOTA claim |
| Production server/database/API | no | none | not applicable | deployable memory service |

## 3. Canonical state spaces implemented

The canonical model distinguishes at least:

```text
WORLD
  what is true in a world branch at a valid time

EVER_EXPOSED
  whether evidence ever entered a mind-instance history

AVAILABLE
  whether that evidence is currently retrievable by that mind instance

ATTITUDE
  whether a mind believes, disbelieves, suspects, or suspends

ATTRIBUTION
  direct observation, report, evidence copy, state replication,
  snapshot inheritance, reconstruction, or unknown attribution

DISCLOSE
  whether a requester may receive a proposition now

JUSTIFICATION
  which sufficient support path authorizes or explains the result
```

These state spaces are intentionally not collapsed. In particular:

```text
receipt ≠ belief ≠ first-person memory
historical exposure ≠ current availability
a fact being true ≠ a requester being allowed to learn it
world branching ≠ mind copying
memory transfer ≠ branch merge
```

## 4. Reproducible commands

The README-advertised deterministic core is:

```bash
python -m pip install -e '.[dev]'
python tools/check_repository_contract.py
python -m pytest -q
python experiments/s_track_conformance.py
python experiments/track_x_v01.py --output-dir /tmp/track_x_v01
python experiments/track_x_v03_context_gate_p0.py --output-dir /tmp/track_x_v03_context_gate
```

The ordinary CI workflow executes these commands or their deterministic drift-check equivalent. A separate Track X v0.3 workflow runs that audit twice and rejects byte drift or held-out-path access.

## 5. Evidence classes

### A. Fixed deterministic conformance

Valid claims:

- the independent gold, generic, and typed implementations agree on the checked fixture semantics;
- declared invariants and mutants behave as tested;
- generated artifacts reproduce byte-for-byte under the frozen code path.

Invalid extrapolations:

- expected user-facing accuracy;
- population confidence intervals from alpha-renamed or Cartesian fixtures;
- superiority over released memory products.

### B. Synthetic mechanism audits

Valid claims:

- a controlled candidate error can be traced through retrieval/candidate, gate, prompt, and answer surfaces;
- an independent raw witness may correct or block some structured errors under the fixture contract;
- missing or materially ambiguous evidence can require abstention.

Invalid extrapolations:

- unrestricted language generalization;
- model calibration;
- public benchmark superiority.

### C. Public deterministic endpoints

PRs #46/#47 establish only the behaviour of two GateMem endpoint controls under the official pinned scorer:

```text
always_no_memory
  no utility, no leakage, full utility over-refusal

raw_lexical context echo
  partial required-pattern coverage, severe privacy/deletion exposure
```

They do not evaluate the integrated MindMap architecture.

## 6. Integration acceptance gates

This release candidate is acceptable as the runnable default only when all of the following pass on its exact head:

1. `python -m pip install -e '.[dev]'`;
2. a no-dependency wheel build;
3. `python tools/check_repository_contract.py`;
4. the complete pytest suite;
5. Track S semantic conformance regeneration;
6. Track X v0.1 committed-output drift comparison;
7. Track X v0.3 deterministic double-run comparison;
8. no read of `data/track_x_v02/heldout/session_a.json` by the development-only v0.3 job;
9. README path and command checks;
10. a clean PR diff against `main` with this status document and no claim broadening.

A green earlier research-branch CI is supporting evidence, not a substitute for a green integration-head CI.

## 7. Remaining implementation priorities

In order:

1. merge or otherwise publish one runnable default branch;
2. freeze a common answer reader and token/call/retry budget;
3. implement checkpoint-isolated stateful public evaluation;
4. audit raw-versus-relationship capability identifiability;
5. run raw retrieval versus pre-reader context gate;
6. compare G-flat and T-normalized under equal information and validators;
7. test independent raw fallback on natural public extraction errors;
8. add LoCoMo and LongMemEval external utility/update evidence;
9. implement a production storage/runtime prototype only after the semantics and lifecycle API stabilize.

## 8. Claim rule

The strongest current repository-wide statement is:

> MindMap contains an executable reference semantics and a set of deterministic mechanism/fault audits for perspective-, branch-, provenance-, policy-, and lifecycle-aware agent memory. Public endpoint infrastructure has also been reproduced independently. A matched end-to-end public benchmark comparison of the complete architecture remains future work.
