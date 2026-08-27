# MindMap Implementation Status

**Status:** runnable v0.2 core on `main`  
**Main merge provenance:** PR #49 → `069c5f4b16b2f594aec48924161ae8944f39652e`  
**Coordination hubs:** Issue #7 for canonical/lifecycle work; Issue #4 for public Track X  
**Source integration point:** `research/track-x-v0.3-context-gate-p0@28937e0aa5aca410d32a77fe3a3ac24508feb6be`

## 1. Why this document exists

The previous default `main` branch contained research documents and the original collision audit, while its README described package, test, and experiment paths that existed only on research branches. PR #49 consolidated the already implemented runnable core and merged it to `main` after cross-session review.

The merge does not manufacture a new scientific result. It exposes one coherent, installable default snapshot and labels each artifact by what it actually establishes. Post-merge workflow `33079708843` passed on exact main commit `069c5f4b16b2f594aec48924161ae8944f39652e`.

## 2. Current implementation matrix

| Component | Present on `main` | Executable/tested contract | What it establishes | What it does not establish |
|---|---:|---|---|---|
| Python package / `pyproject.toml` | yes | editable install, wheel/sdist build, clean distribution install | repository is installable | production deployment readiness |
| Canonical event model | yes | unit and conformance tests | frozen finite semantics can be represented | natural-language extraction quality |
| Independent gold interpreter | yes | compared against generic and typed code paths | avoids resolver self-agreement in canonical fixtures | a population estimate |
| Complete generic ledger | yes | clean canonical agreement | equal-information generic control | lower engineering cost in every deployment |
| Normalized typed ledger | yes | clean canonical agreement | typed implementation of the same semantics | intrinsic oracle superiority |
| Track S conformance | yes | semantic regeneration / zero disagreement | implementation agreement on fixed fixtures | cross-environment byte identity or real conversational accuracy |
| Track E observer/fault P0/P1 | **no** | separate draft PRs #36/#37 | pending lifecycle/fault research line | any Track E result from current `main` |
| Track X v0.1 raw verifier | yes | committed artifact drift comparison | information-firewall/mechanism plumbing | unrestricted natural language |
| Track X v0.2 authored development bundles | yes | schema/authorship/freeze tests | independent-authorship protocol and development surface | Session-A held-out result |
| Track X v0.3 context-gate P0 | yes | same-environment deterministic double-run + held-out boundary | candidate → gate → prompt → answer decomposition | learned gate or public benchmark effect |
| Public GateMem endpoint controls | separate PRs #46/#47/#50 | protected scorer / endpoint comparisons under their own review gates | external endpoint/provenance evidence | MindMap architecture effectiveness |
| LoCoMo/LongMemEval matched architecture study | no accepted result | protocol only | future external-validity target | any current public SOTA claim |
| Production server/database/API | no | none | not applicable | deployable memory service |

The material excluded-work risk is recorded in `docs/LOST_WORK_REGISTER.md`. In particular:

```text
PR #36 / d7e68693486410a5419700045ca7099cd1ebe234
  Track E canonical observer/fault P0

PR #37 / 8880ba4a8880f9fe91e62c54cbb763eb21882e42
  Track E physical projection/repair P1
```

Neither is silently accepted or discarded by the runnable `main` core.

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

The release contract is enumerated in `release_contract_v0_2.json`. CI verifies the commands and declared paths in that versioned contract; it does not claim to infer arbitrary future prose references outside the manifest.

## 5. Reproducibility surfaces

The three active deterministic tracks have different reproducibility contracts and must not be conflated.

### Track S — semantic regeneration

Contract:

```text
regenerate the fixed suite
require independent gold/generic/typed semantic agreement
require zero semantic disagreement
```

The generated summary may contain Python/platform identity. The runnable core therefore makes **no repository-wide or cross-environment byte-for-byte claim** for Track S.

### Track X v0.1 — committed artifact drift comparison

Contract:

```text
regenerate the fixed v0.1 outputs
compare the declared committed CSV/JSON artifacts
fail on drift
```

This is the release's explicit committed-artifact comparison surface.

### Track X v0.3 — same-environment double-run and held-out boundary

Contract:

```text
run the development-only audit twice in one controlled workflow environment
compare the two generated bundles
require heldout_read=false
require the frozen row/topology invariants
```

This demonstrates same-environment determinism and the declared held-out boundary, not environment-independent serialization.

## 6. Evidence classes

### A. Fixed semantic conformance

Valid claims:

- the independent gold, generic, and typed implementations agree on the checked fixture semantics;
- declared invariants and mutants behave as tested;
- the Track S semantic regeneration completes with zero disagreement on the tested environment.

Invalid extrapolations:

- expected user-facing accuracy;
- cross-platform byte identity unless separately tested;
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

### C. Public endpoint studies

PRs #46/#47 establish B0/B1a external endpoint evidence, and PR #50 is the separately review-gated B1b shared-reader study. They are not part of the `main` architecture evidence surface unless later reviewed and deliberately integrated.

They do not by themselves evaluate the complete MindMap architecture.

## 7. Runnable-main verification contract

The default core is expected to retain all of the following gates:

1. `python -m pip install -e '.[dev]'` on Python 3.11, 3.12, 3.13, and 3.14;
2. wheel and sdist construction from the same head;
3. distribution metadata contains `License-Expression: MIT` and `License-File: LICENSE`;
4. clean wheel and clean sdist installation/import checks;
5. SHA-256 manifest for the built release artifacts;
6. `python tools/check_repository_contract.py` against `release_contract_v0_2.json`;
7. the complete pytest suite;
8. Track S semantic regeneration / zero disagreement;
9. Track X v0.1 committed-output drift comparison;
10. Track X v0.3 same-environment double-run plus `heldout_read=false`.

On the initial merged main commit `069c5f4b16b2f594aec48924161ae8944f39652e`, all six post-merge check jobs completed successfully in workflow `33079708843`.

## 8. Remaining implementation priorities

In order:

1. keep the enumerated runnable-main release contract green as the default branch evolves;
2. independently review or supersede pending Track E PRs #36/#37 rather than silently absorbing them;
3. finish cross-session review of public B1b PR #50 and freeze the next B2 information surface;
4. implement checkpoint-isolated stateful public evaluation before architecture comparisons;
5. audit raw-versus-relationship capability identifiability;
6. run raw retrieval versus pre-reader context gate;
7. compare G-flat and T-normalized under equal information and validators;
8. test independent raw fallback on natural public extraction errors;
9. add LoCoMo and LongMemEval external utility/update evidence;
10. implement a production storage/runtime prototype only after the semantics and lifecycle API stabilize.

## 9. Claim rule

The strongest current `main` statement is:

> MindMap contains an executable reference semantics and deterministic synthetic Track S/Track X mechanism audits for perspective-, branch-, provenance-, policy-, and lifecycle-aware agent memory. Track E observer/physical-fault studies remain separate review-gated PRs #36/#37, and public GateMem endpoint studies remain separate PRs #46/#47/#50. A matched end-to-end public benchmark comparison of the complete architecture remains future work.
