# Memory Integrity Envelope — provisional engineering contract

This is an engineering consequence of Track E v0.1, not a cryptographic novelty claim.

```text
TransactionEnvelope(
  transaction_id,
  parent_commit_hash,
  expected_event_ids,
  event_hashes_or_set_commitment,
  semantic_config_hash,
  actor_or_authority_id,
  authentication_material,
  committed_system_time
)

ProjectionCheckpoint(
  projection_id,
  ledger_head_hash,
  system_time_cutoff,
  projector_version,
  configuration_hash,
  projection_state_hash,
  created_system_time
)
```

Required properties include an authenticated append-only commitment chain, idempotent replay, deterministic hashing, key rotation, independently verifiable receipts, ledger-head-bound projections, and deletion/revocation manifests covering every derived structure in scope.

The envelope proves commitment and integrity relative to an authority. It does not prove semantic truth.

## Non-identifiability lemma

Let `H0` be a valid history without event `e`, and `H1` a history in which `e` occurred but all evidence of `e` was removed before observation. If:

```text
Obs(H0) = Obs(H1)
```

then no detector operating only on `Obs` can distinguish the histories without error. An authenticated receipt, counterpart acknowledgement, expected-event manifest, or other external observation is required to break the equivalence.

This is an observability boundary shared by generic and typed ledgers; it is not a schema-specific defect.