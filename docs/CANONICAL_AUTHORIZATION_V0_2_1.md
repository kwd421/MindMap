# Canonical authorization contract v0.2.1

**Status:** amendment candidate; explicit cross-session review required  
**Base schema:** `SCHEMA_V0_2.md`  
**Base main:** `069c5f4b16b2f594aec48924161ae8944f39652e`

## Purpose

This amendment closes two finite-semantics ambiguities in same-principal state replication. It is a correctness constraint on the existing v0.2 model, not a claim that typed storage is more expressive or more accurate than an equal-information generic ledger.

## 1. Authorization has stable scope

For an authorization identifier `a`, define its replication scope as:

```text
Scope(a) = (source_mind_instance_id, destination_mind_instance_id)
```

Every revision carrying the same authorization identifier MUST retain the same scope. If two revisions of one identifier disagree on source or destination, the authorization history is invalid/ambiguous and MUST NOT authorize a transfer.

For a replication exposure `x`, authorization is eligible only if:

```text
x.authorization_id = a
AND x.source_mind_instance_id = Scope(a).source
AND x.destination_mind_instance_id = Scope(a).destination
```

An authorization issued for `M1 -> M2` therefore cannot be replayed to authorize `M3 -> M4`, even when all four mind instances belong to the same principal and the second pair has otherwise eligible lineage.

This augments, rather than replaces, the existing replication preconditions:

```text
same principal
AND eligible lineage kind
AND active scoped authorization
AND copy-eligible source state
AND no non-commutative identity-bearing conflict
```

## 2. Same-system-time conflicting revisions are ambiguous

Schema v0.2 carries transaction/system time but does not carry an independent within-time journal sequence suitable for ordering two different revisions recorded at the exact same system time.

Therefore, for one authorization identifier, let `t*` be the maximum visible system time. If the visible revisions at `t*` contain both `grant` and `revoke`, the state is **ambiguous** and resolution MUST fail closed.

Implementations MUST NOT resolve that conflict using accidental representation details such as:

```text
event_id lexical order
row insertion order
operation lexical order
Python container order
```

Equivalent duplicate revisions carrying the same operation at `t*` are semantically one operation for this finite contract.

A future schema may add an authenticated journal sequence or explicit supersession relation. Until then, a same-time conflicting authorization transition has no canonical winner.

## 3. Independent implementation requirement

Track S retains three independently implemented paths:

```text
GoldSemantics
GenericLedger
TypedLedger
```

The authorization rules may share the written specification above, but the answer-producing implementations MUST NOT call one another or a single shared resolver whose output would create self-agreement.

## 4. Required regression cases

The amendment is not accepted unless all three paths satisfy these cases:

1. **wrong scope:** grant `AUTH-1` for `M1 -> M2`; replication `M3 -> M4` citing `AUTH-1` is not acquired;
2. **matching scope:** grant `AUTH-1` for `M3 -> M4`; otherwise valid replication succeeds;
3. **scope mutation:** revisions of `AUTH-1` change from `M1 -> M2` to `M3 -> M4`; resolution rejects the authorization history;
4. **same-time conflict:** same-scope grant and revoke occur at the same system time; resolution rejects the ambiguous history.

The current candidate implementation freezes these cases in `tests/test_canonical_authorization_contract.py`.

## 5. Research boundary

This amendment establishes none of the following by itself:

- production access-control completeness;
- cryptographic authorization authenticity;
- distributed consensus or serializability;
- lifecycle fault-detection advantage for typed storage;
- public benchmark improvement;
- a Track E P0/P1 result.

Its role is narrower: prevent an authorization ID from becoming an unscoped capability token and prevent Gold/G/T from assigning different semantics to simultaneous conflicting revisions.

## 6. Integration decision

If both sessions explicitly accept this amendment and its regressions remain green, the next schema edit should fold these rules into the normative authorization/replication constraints of `SCHEMA_V0_2.md` (or advance the schema revision explicitly) rather than leaving this file as a permanent parallel source of truth.
