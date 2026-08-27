# Claim–evidence ledger

Status vocabulary: `design`, `exploratory`, `supported`, `contradicted`,
`superseded`, `open`. A supported claim remains limited to its listed scope.

| Claim ID | Claim | Status | Supporting evidence | Counter-evidence / limitation | Scope |
|---|---|---|---|---|---|
| C-001 | Complete equal-information generic and typed implementations agree on the fixed clean semantics. | supported | Track S: 75/75 gold/generic/typed agreement; repository tests | finite authored fixtures only | deterministic canonical suite |
| C-002 | A post-retrieval frozen reader reduces answer leakage but does not repair forbidden prompt exposure. | supported | EXP-20260827-001; 2,218 matched B1a/B1b contexts; answer leakage fell while context/e2e remained high | utility collapsed; GateMem only | pinned GateMem negative control |
| C-003 | The current B2 information-surface implementation is ready for performance claims. | open | 86 local tests and 9/9 surface cases passed at `f1d7b80...`; newer CI surface checks green | surface audit is not an outcome study; parser false-positive history; current head still moving | interface readiness only |
| C-004 | Pre-reader governance improves the utility–safety frontier over raw retrieval. | open | mechanism rationale | no frozen B2 outcome yet | none |
| C-005 | MindMap outperforms other long-term-memory systems on a public benchmark. | open | none | no matched official comparison | none |
| C-006 | Explicit backup, lineage, fork/merge, and reconstruction semantics are useful engineering abstractions. | design | canonical model and fictional-source inspiration | operational advantage not yet measured | architecture hypothesis |
| C-007 | MindMap implements complete deletion. | contradicted | none | current evidence distinguishes answer suppression from persistent context exposure; all storage surfaces not audited | no such claim permitted |

## Claim update rule

Every status change must identify an experiment ID, exact revision, denominators,
and the narrowest valid scope. A GitHub green check proves its declared command
ran; it does not by itself prove an architecture or benchmark claim.
