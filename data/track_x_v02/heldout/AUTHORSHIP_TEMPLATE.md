# Track X v0.2 Held-Out Passage Authorship

**Author session:** Session A  
**Required output:** `data/track_x_v02/heldout/session_a.json`

## Declaration to complete

Before writing the held-out passages, Session A should record:

```text
[Session A] ACCEPT WITH PASSAGE CONTRIBUTION
Base/freeze commit:
I did not edit or use the Track X v0.2 primary extractor, verifier,
thresholds, development passages, evaluator, or answer outputs while writing
these passages.
```

After writing the passages, record:

```text
Held-out branch:
Held-out commit:
Changed paths:
  data/track_x_v02/heldout/session_a.json
  data/track_x_v02/heldout/AUTHORSHIP.md
Topology families covered:
  F08–F14 exactly once each
```

## Allowed content

`session_a.json` must contain seven authored passage bundles using the same compact schema as:

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

The held-out contribution commit must not modify:

```text
src/mindmap/track_x/**
experiments/**
tests/**
docs/TRACK_X_V02_PROTOCOL.md
data/track_x_v02/development/**
```

A change outside the two allowed held-out paths invalidates blind evaluation unless both sessions explicitly amend the protocol before running outcomes.
