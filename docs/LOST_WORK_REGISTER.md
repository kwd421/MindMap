# Lost-Work and Pending-Research Register

This register exists so a minimal runnable release cannot silently erase or misrepresent review-gated work that remains on separate branches.

## Track E pending work

### PR #36 — canonical observer and lifecycle-fault P0

```text
PR:     #36
branch: research/track-e-v0.2-canonical
head:   d7e68693486410a5419700045ca7099cd1ebe234
status: separate draft; not integrated into PR #49
hub:    Issue #7
```

Contains the separate `src/mindmap/track_e/` observer package, `experiments/track_e_v02_p0.py`, tests, results, and audit for the canonical observer/fault-harness P0.

Reason not integrated here: PR #36 has its own scientific review gates. Release PR #49 is a default-branch/reproducibility consolidation and must not silently accept those research claims merely to make a status table look complete.

### PR #37 — physical projection/repair P1

```text
PR:     #37
branch: research/track-e-v0.3-physical
head:   8880ba4a8880f9fe91e62c54cbb763eb21882e42
base:   research/track-e-v0.2-canonical
status: separate draft; not integrated into PR #49
hub:    Issue #7
```

Adds matched physical projection/repair faults, authoritative journal/projection witnesses, deterministic rebuild repair, and cost accounting.

Reason not integrated here: it depends on PR #36 and remains research-review gated. It should be reviewed and merged or superseded through the Track E line, not absorbed into the runnable-core release.

## Public Track X pending work

PRs #46 and #47 remain separate public benchmark endpoint evidence:

```text
#46 research/track-x-v0.7-gatemem-opaque-firewall
#47 research/gatemem-official-repro-audit
```

They are not part of the MindMap architecture-effect claim and are intentionally not folded into the runnable core merely because they are externally validated endpoint controls.

## Merge rule

Before merging a future release candidate, compare this register against open PRs and active branch heads. If a listed work item is integrated, superseded, or abandoned, update this file with the exact replacement commit/PR and reason. Silence or age is not a basis for deleting the entry.
