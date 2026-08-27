# Canonical temporal referential-integrity amendment

**Status:** review candidate  
**Base:** `main@069c5f4b16b2f594aec48924161ae8944f39652e`  
**Scope:** `CommonEvent` input validity only

## Problem

The fixed canonical suite compared Gold, Generic, and Typed answers after all
events had been loaded, but it did not reject an event that referred to an
entity created at a later system time. Two adversarial fixtures exposed distinct
failure modes:

- lineage and replication referred to a destination mind before its creation;
  Gold and Generic returned `False`, while Typed returned `True` because its
  final projection contained the later mind;
- restore lineage referred to a destination mind before its creation; all three
  implementations returned `True`, so implementation agreement hid the common
  oracle error.

## Normative contract

For every reference enumerated in the finite runtime table below:

```text
target.created_system_time <= referencing_event.system_time
```

Equality is allowed. Lexical ordering of event IDs at the same system time does
not change validity. A missing target or a target created only at a later system
time is invalid input and must fail closed before Gold, Generic, or Typed answer
a query.

The runtime table is explicit so that a broad schema claim cannot be inferred
from a few passing examples.

| Referencing event | Reference fields and namespace |
|---|---|
| `mind_create` | actor principal -> principal |
| `world_create` | parent attribute -> world branch |
| `placement` | destination mind -> mind; about-world -> branch |
| `lineage` | source/destination -> mind; snapshot -> snapshot; authorization -> authorization |
| `evidence` | actor -> principal/mind; source/destination context -> placement; about-world -> branch |
| `world_claim` | about-world -> branch; attitude context -> placement |
| `attitude` | destination -> mind; about-world -> branch; attitude context -> placement |
| `exposure` | source/destination -> mind and placement; object -> namespace selected by `object_kind`; authorization -> authorization |
| `policy` | actor -> principal; destination -> mind; object -> namespace selected by `object_kind` |
| `justification` | untyped derivation member -> evidence (finite-runtime compatibility subset) |
| `snapshot_member` | snapshot -> snapshot; object -> namespace selected by `object_kind` |
| `authorization` | actor -> principal; source/destination -> mind |

Exposure objects support the schema's `evidence`, `assertion`, `claim`, and
`snapshot` namespaces. Snapshot members additionally support `attitude` and
`policy`. Existing sparse events that omit `object_kind` in exposure or policy
records retain the v0.2 compatibility default of `evidence`; new producers
should emit the kind explicitly.

The current query surface is evidence-centric. Exposure and policy rows of
another kind may be ingested without colliding with a same-string evidence ID,
but they do not satisfy or modify `EVER_EXPOSED`, `AVAILABLE`, `ATTRIBUTION`, or
evidence-policy answers. A future kind-specific query implementation needs its
own conformance cases before it can claim claim/assertion/snapshot lifecycle
support.

The finite `CommonEvent` projection does not yet contain the standalone
`Snapshot` entity specified in `SCHEMA_V0_2.md`. In this runtime only, the first
complete manifest entry is the snapshot identifier's creation event; a member
whose snapshot ID, object kind, or object ID is absent, empty, or whitespace-only
cannot create one. A lineage reference before that first entry is invalid. This
is a compatibility rule, not a claim that the full schema's snapshot lifecycle
has been implemented.

`derivation_members` is also still an untyped tuple. The finite runtime accepts
only evidence members; assertion/claim members fail with an explicit unsupported
kind error until the runtime carries the schema's `source_kind`. Missing and
future evidence members fail closed. A later claim reusing the same string ID
does not retroactively invalidate an earlier evidence justification.

The validator is shared input-schema infrastructure. Gold, Generic, and Typed
remain separate answer evaluators, but each constructor invokes the same input
validity gate so direct use cannot bypass it.

## Verification boundary

The two known future-destination fixtures must be rejected at all three
constructor entry points. This is three wiring checks over **one shared schema
validator**, not three independent semantic validators. Accepted valid logs are
then answered by the separate Gold, Generic, and Typed evaluators.

Isolated reference matrices test future and missing targets without relying on
an aggregate fixture that can stop at the first error. Equal-system-time
controls must remain accepted. Object-kind controls must prove that a real claim
is not looked up in the evidence namespace. The pre-existing fixed suite must
retain zero Gold/Generic/Typed disagreement.

The shared gate intentionally changes the old Track X v0.1 structured-only
treatment for malformed `wrong-world` and `wrong-mind` candidates: silent wrong
use becomes schema rejection/abstention. That is a post-hoc intervention on the
downstream system, not an improvement by the raw-evidence verifier. The result
document and deterministic artifacts therefore report the before/after counts
and preserve the causal boundary.

This amendment does **not** prove:

- complete lifecycle or merge provenance;
- cycle detection or uniqueness for every domain identifier;
- distributed serializability or durable-store enforcement;
- valid-time causality beyond the explicit bitemporal rules;
- the complete standalone Snapshot lifecycle from `SCHEMA_V0_2.md`;
- a typed `JustificationMember.source_kind` projection;
- that unlisted future `CommonEvent` fields automatically receive a reference
  rule.

Those remain separate schema and implementation obligations.
