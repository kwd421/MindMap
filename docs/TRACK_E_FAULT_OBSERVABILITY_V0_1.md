# Track E v0.1 — Fault Observability under Equal Information

## Status and claim boundary

This is a fixed, synthetic lifecycle **fault-observability audit** for the MindMap / NCM-Ψ research program. It is not an end-to-end language experiment, a public-benchmark result, or a population-effect estimate.

The experiment follows the representation-equivalence pivot in PR #30:

- complete generic and typed ledgers receive the same events and invariant rules;
- semantic-answer superiority is not expected under equal information;
- the empirical target is fault detection, localization, residue prevention, repairability, and cost.

## Design

The suite contains 17 archetypes: 14 observable faults, one deliberately non-identifiable omission, and two clean controls. Each archetype is alpha-renamed 20 times, yielding 340 case variants and 2,040 system-case rows.

| System | Local schema/references | Cross-event lifecycle invariants | External commitment/projection binding |
|---|---:|---:|---:|
| G-Raw | minimal ID collision only | no | no |
| T-Local | yes | no | no |
| G-Complete | yes | yes | no |
| T-Canonical | yes | yes | no |
| G-Envelope | yes | yes | yes |
| T-Envelope | yes | yes | yes |

`G-Complete` and `T-Canonical` deliberately share the same invariant specification. `G-Envelope` and `T-Envelope` also share the same envelope rules. Their equality is the null expectation, not an architecture win.

## Fault archetypes

Local/referential: missing required field, invalid enum, unknown reference, and conflicting duplicate ID.

Cross-event semantic: unauthorized transfer; transfer by a source that never acquired the evidence; first-person state replication into an identity fork; adoption without exposure; snapshot post-cutoff inclusion; ambiguous same-time policy; and policy laundering through a derived summary.

Externally committed: a dropped revoke despite an event-set envelope; fork-cutoff tampering despite a committed hash; and a stale projection bound to the wrong ledger head.

Non-identifiable: a dropped revoke when no command, receipt, envelope, or other commitment survives.

Clean controls: direct observation remains direct after later hearsay; requester-specific revocation of public evidence does not revoke unrelated requesters.

## Aggregate result

| System | Observable-fault recall | UISR on observable faults | Recall over all faults | Clean false alarms |
|---|---:|---:|---:|---:|
| G-Envelope | 100.00% | 0.00% | 93.33% | 0.00% |
| T-Envelope | 100.00% | 0.00% | 93.33% | 0.00% |
| G-Complete | 78.57% | 21.43% | 73.33% | 0.00% |
| T-Canonical | 78.57% | 21.43% | 73.33% | 0.00% |
| T-Local | 28.57% | 71.43% | 26.67% | 0.00% |
| G-Raw | 7.14% | 92.86% | 6.67% | 0.00% |

All detected cases were localized to a mutated event ID in this fixed suite. Microsecond timings are exploratory Python timings, not portable performance claims.

## Three-tier observability model

### Intrinsic invalidity

The surviving ledger is internally inconsistent, so local or cross-event invariants can detect the fault: missing fields, unknown references, unauthorized transfer, adoption without exposure, invalid identity-fork replication, snapshot-cutoff violation, or provenance/policy laundering.

### Extrinsic inconsistency

The surviving ledger is semantically well-formed but disagrees with an authenticated external commitment or projection head. Examples are a missing committed revoke, a changed fork cutoff, or a stale cache. A transaction receipt, authenticated command log, Merkle-style commitment, or projection manifest is required.

### Non-identifiable omission

Let H0 be a valid history in which no revoke was issued, and H1 a history in which a revoke was issued but every trace was dropped. If the detector sees only the surviving ledger L:

```text
Obs(H0) = L = Obs(H1)
```

then every detector over `Obs` gives the same output for H0 and H1. A detector that accepts H0 cannot identify H1 without a false alarm. An external receipt, counterpart acknowledgement, expected-event manifest, or equivalent witness is necessary to break the equivalence.

## Architecture consequence

Separate the semantic ledger from integrity evidence:

```text
TransactionEnvelope(
  transaction_id,
  parent_commit_hash,
  expected_event_ids_or_event_set_commitment,
  event_hashes,
  semantic_config_hash,
  authority_id,
  authentication_material,
  committed_system_time
)

ProjectionCheckpoint(
  projection_id,
  ledger_head_hash,
  system_time_cutoff,
  projector_version,
  configuration_hash,
  projection_state_hash
)
```

These are established tamper-evident logging ideas, not new cryptography. The defensible contribution candidate is the lifecycle fault taxonomy, benchmark, impossibility boundary, and observability/cost frontier for agent memory.

## Negative results and narrowing decisions

1. Complete typed and generic systems tied exactly, as expected.
2. Local typing alone detected 4 of 14 observable archetypes.
3. Cross-event semantic validation detected 11 of 14.
4. External commitments were necessary for the remaining three observable cases.
5. No tested representation could detect the uncommitted omission.
6. This experiment does not establish that database constraints outperform a complete application validator; independent implementations and real transaction faults are required.

## Limitations

- fixed hand-designed archetypes; no population inference;
- alpha-renaming checks identifier invariance, not topology generalization;
- generic and typed complete validators share one invariant engine;
- no database transactions, signatures, Merkle tree, concurrency, crash injection, LLM extraction, retrieval, or reader;
- localization is easy because mutations are small and known;
- timings are interpreter/environment specific.

## Next falsification experiment

Implement the same lifecycle grammar independently in:

1. `G-Raw`: JSON/event table with structural checks;
2. `G-Complete`: generic bitemporal table plus independently written application validators;
3. `T-Canonical`: normalized relational schema with declarative constraints and an independently written cross-record validator.

Inject partial commits, out-of-order replay, duplicate delivery, lost command versus lost event, index invalidation loss, snapshot corruption, policy races, and fork/restore cutoff tampering. Measure detection timing, localization, repair, residue, replay divergence, false alarms, latency, write amplification, and storage. The primary comparison is T-Canonical versus G-Complete; G-Raw is only a control for the value of invariants.