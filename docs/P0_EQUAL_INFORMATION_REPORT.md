# NCM-Ψ P0 Equal-Information Audit v0.1

**Status:** deterministic symbolic P0; not an LLM or public-benchmark result  
**Date:** 2026-08-17

## Research question

When a complete generic event ledger and a typed NCM-Ψ ledger receive byte-equivalent information and enforce equivalent finite invariants, does the typed representation have a semantic correctness advantage? Which fault classes can either representation actually detect?

## Design

- 14 hand-authored topology fixtures and 46 explicit expected query outputs.
- Target spaces: world state, exposure, availability, attitude, first-person attribution, merge eligibility, disclosure, provenance, and source attribution.
- Three systems: `generic_basic`, `generic_audited`, and `typed`.
- `generic_audited` and `typed` are independent implementations of intentionally equivalent finite invariants.
- 18 injected faults: 8 enforceable, 8 well-formed semantic/extraction corruptions, and 2 missing-event faults.
- Seven deliberately wrong semantic mutants test whether the fixture set can detect known mistakes.
- Gold answers are literal fixture data; no candidate resolver generates them.

## Clean conformance

| System | Queries | Accuracy | All-correct fixtures | Validator findings |
|---|---:|---:|---:|---:|
| generic_basic | 46 | 100.00% | 100.00% | 0 |
| generic_audited | 46 | 100.00% | 100.00% | 0 |
| typed | 46 | 100.00% | 100.00% | 0 |

**Result:** all three systems agree with independent gold on every clean query. This rejects any claim that the typed schema is inherently more expressive or more accurate under equal information and complete semantics.

## Fault-class results

| System | Fault class | Faults | Detection | Localization | Silent-wrong | Safe outcome | Coverage | Accuracy when answered |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| generic_basic | enforceable | 8 | 12.50% | 12.50% | 7.41% | 92.59% | 96.30% | 92.31% |
| generic_basic | missing_event | 2 | 0.00% | 0.00% | 50.00% | 50.00% | 100.00% | 50.00% |
| generic_basic | well_formed_semantic | 8 | 0.00% | 0.00% | 50.00% | 50.00% | 100.00% | 50.00% |
| generic_audited | enforceable | 8 | 100.00% | 100.00% | 0.00% | 100.00% | 37.04% | 100.00% |
| generic_audited | missing_event | 2 | 0.00% | 0.00% | 50.00% | 50.00% | 100.00% | 50.00% |
| generic_audited | well_formed_semantic | 8 | 0.00% | 0.00% | 50.00% | 50.00% | 100.00% | 50.00% |
| typed | enforceable | 8 | 100.00% | 100.00% | 0.00% | 100.00% | 37.04% | 100.00% |
| typed | missing_event | 2 | 0.00% | 0.00% | 50.00% | 50.00% | 100.00% | 50.00% |
| typed | well_formed_semantic | 8 | 0.00% | 0.00% | 50.00% | 50.00% | 100.00% | 50.00% |

### Main findings

1. `generic_audited` and `typed` tie exactly: both detect and localize all eight enforceable faults, contain every affected query, and produce no silent wrong answer in that class.
2. The typed reference implementation performs more instrumented checks than the generic audit implementation. This Python check count is not a production latency benchmark, but it provides no evidence of a typed efficiency advantage.
3. Both complete systems fail identically on every well-formed semantic corruption and every missing-event fault. Their silent-wrong rate is 50% of the queries in each of those two fault classes.
4. The simple generic ledger catches only duplicate identifiers. Its lower abstention rate is not safety: it silently answers incorrectly on malformed inputs that the complete validators contain.

## Exact fault audit

| Fault | Class | Changes an evaluated answer | G audited detects | Typed detects | G silent wrong | T silent wrong |
|---|---|---:|---:|---:|---:|---:|
| `about_branch_swap` | well_formed_semantic | yes | no | no | 2 | 2 |
| `adoption_before_receipt` | enforceable | no | yes | yes | 0 | 0 |
| `attitude_laundering` | well_formed_semantic | yes | no | no | 1 | 1 |
| `authorized_false_declassification` | well_formed_semantic | yes | no | no | 2 | 2 |
| `branch_cycle` | enforceable | no | yes | yes | 0 | 0 |
| `copy_claims_direct_observation` | enforceable | no | yes | yes | 0 | 0 |
| `correlated_identity_reclassification` | well_formed_semantic | yes | no | no | 2 | 2 |
| `dropped_initial_exposure` | missing_event | yes | no | no | 1 | 1 |
| `dropped_revoke_event` | missing_event | yes | no | no | 2 | 2 |
| `duplicate_event_id` | enforceable | no | yes | yes | 0 | 0 |
| `false_independent_origin` | well_formed_semantic | yes | no | no | 2 | 2 |
| `lineage_cycle` | enforceable | no | yes | yes | 0 | 0 |
| `missing_required_source_family` | enforceable | yes | yes | yes | 0 | 0 |
| `snapshot_includes_post_cutoff` | enforceable | no | yes | yes | 0 | 0 |
| `speaker_instance_swap` | well_formed_semantic | yes | no | no | 1 | 1 |
| `unauthorized_state_replication` | enforceable | no | yes | yes | 0 | 0 |
| `wrong_fork_valid_time` | well_formed_semantic | yes | no | no | 1 | 1 |
| `wrong_valid_from` | well_formed_semantic | yes | no | no | 1 | 1 |

The enforceable suite includes authorization, attribution, adoption ordering, snapshot cutoff, lineage and world-branch cycles, missing required fields, and duplicate IDs. The well-formed suite includes false source independence, wrong fork time, actor swaps, temporal shifts, attitude laundering, about-world swaps, correlated identity/lineage/transfer reclassification, and false declassification.

## Mutation adequacy

| Mutant | Killed | Failed queries | Failed fixtures |
|---|---:|---:|---:|
| `receipt_implies_belief` | 1 | 2 | 2 |
| `identity_fork_first_person` | 1 | 3 | 3 |
| `forget_erases_history` | 1 | 1 | 1 |
| `flatten_policy` | 1 | 3 | 2 |
| `system_time_fork` | 1 | 1 | 1 |
| `same_origin_independent` | 1 | 2 | 1 |
| `branch_collapse` | 1 | 2 | 2 |

All seven preregistered semantic mutants are killed. This does not prove completeness, but it shows that the fixed fixtures distinguish receipt from belief, identity forks from first-person continuity, historical exposure from current availability, source-family independence, branch-valid time from system time, and derivation-aware policy.

## Decision

The P0 result supports the current PR pivot: **typed NCM-Ψ storage is not a semantic-oracle accuracy contribution.** A fully audited generic ledger can implement the same finite semantics. The remaining empirical claims must concern one or more of:

- earlier or more reliable enforcement in a real database/runtime;
- fault localization, repair blast radius, and operational diagnostics;
- natural-language extraction and topology generalization;
- calibrated abstention and independent raw-evidence verification;
- implementation and governance cost under matched production workloads.

The strongest negative result is equally important: **well-formed false metadata and omitted events defeat both complete ledgers.** More schema cannot repair missing or confidently wrong evidence. The next experiment should therefore test independent extraction/verifier channels and raw-evidence fallback on held-out language/topology families.

## Reproduction

```bash
python experiments/p0_equal_information_audit.py --output-dir results/p0_equal_information
python -m pytest -q
```

The output manifest contains SHA-256 hashes. A second execution produced byte-identical CSV files.

## Limitations

- symbolic fixtures, not natural dialogue;
- hand-authored topology set, so no population-level p-value is appropriate;
- intentionally equivalent finite invariant coverage for the two complete systems;
- no PostgreSQL constraints, crash/replay harness, or concurrent transactions;
- no learned confidence calibration, LLM extractor, or reader model;
- check counts are implementation diagnostics, not production cost estimates.
