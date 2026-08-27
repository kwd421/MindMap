# Track X v0.2 Held-Out Passage Authorship

**Author session:** Session A  
**Required data output:** `data/track_x_v02/heldout/session_a.json`

Copy this file to:

```text
data/track_x_v02/heldout/AUTHORSHIP.md
```

and complete the following declaration before committing:

```text
[Session A] ACCEPT WITH PASSAGE CONTRIBUTION
Base/freeze commit: <full freeze declaration SHA>
I did not edit or use the Track X v0.2 primary extractor, verifier,
thresholds, development passages, evaluator, or answer outputs while writing
these passages.

Held-out branch: research/track-x-v0.2-heldout-<suffix>
Changed paths:
- data/track_x_v02/heldout/session_a.json
- data/track_x_v02/heldout/AUTHORSHIP.md
```

Do **not** put the contribution's final commit SHA inside `AUTHORSHIP.md`; a commit cannot reliably contain its own hash. GitHub CI computes the final head SHA, and Session A records it in the Issue #7 handoff after committing.

## Passage bundles

`session_a.json` contains seven authored bundles using the same compact schema as:

```text
data/track_x_v02/development/session_b.json
```

Required held-out topology families:

```text
restore_manifest_gap
cross_world_reference_context
protected_only_revocation
independent_public_survives
same_origin_dedup
authorized_replication
temporal_negative_controls
```

Each bundle contains:

- one information-complete manually written passage;
- one intentionally ambiguous version;
- at least one misleading nearby passage;
- one controlled candidate-field mutation;
- no answer labels or evaluator-only fields.

## Forbidden changes

The held-out contribution commit may modify only the two declared paths. In particular, it must not modify:

```text
src/mindmap/track_x/**
experiments/**
tests/**
.github/workflows/**
docs/TRACK_X_V02_PROTOCOL.md
data/track_x_v02/development/**
data/track_x_v02/FREEZE_V02.json
```

After committing, Session A posts in Issue #7:

```text
[Session A] ACCEPT WITH PASSAGE CONTRIBUTION
Base/freeze commit: <SHA>
Held-out branch: <branch>
Held-out head commit: <computed SHA>
Changed paths: the two allowed held-out files only
```

A change outside the two allowed paths invalidates blind evaluation unless both sessions amend the protocol before held-out outcomes are run.