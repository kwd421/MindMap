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

For every entity reference in a `CommonEvent`:

```text
target.created_system_time <= referencing_event.system_time
```

Equality is allowed. Lexical ordering of event IDs at the same system time does
not change validity. A missing target or a target created only at a later system
time is invalid input and must fail closed before Gold, Generic, or Typed answer
a query.

The current amendment checks references involving:

- principals and mind instances;
- world branches and parent branches;
- mind placements;
- evidence, world claims, and attitudes;
- lineage source and destination minds;
- exposure source/destination minds, evidence, and authorization;
- evidence/attitude snapshot members;
- authorization source and destination minds.

The validator is shared input-schema infrastructure. Gold, Generic, and Typed
remain separate answer evaluators, but each constructor invokes the same input
validity gate so direct use cannot bypass it.

## Verification boundary

The two known future-destination fixtures must be rejected by all three
constructors. A separate reference matrix tests other entity classes, and an
equal-system-time control must remain accepted. The pre-existing fixed suite
must retain zero Gold/Generic/Typed disagreement.

This amendment does **not** prove:

- complete lifecycle or merge provenance;
- cycle detection or uniqueness for every domain identifier;
- distributed serializability or durable-store enforcement;
- valid-time causality beyond the explicit bitemporal rules;
- that every future `CommonEvent` field has already been assigned a reference
  rule.

Those remain separate schema and implementation obligations.
