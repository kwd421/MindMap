# Code Review: `experiments/collision_audit_v0_2.py`

**Status:** independent implementation audit  
**Reviewer marker:** Session B  
**Date:** 2026-08-17  
**Reviewed code commit:** `f3abb4e20b998ee32d870f472e753f90f6896ef1`  
**Reviewed result commit:** `77cf761369f56d93f3d8e7b8f0ff1d5b0235a107`

## 1. Executive decision

The committed script reproducibly defines a deterministic 48-scenario × 4-decision truth table and reproduces the two basic aggregate fields:

```text
decision_accuracy
scenario_all_correct
```

That is useful as a semantics/unit-test artifact.

The following reported items are **not** reproducible from the committed script:

- category-specific accuracies in the committed result CSV;
- unauthorized-disclosure, over-withholding, false-first-person, and under-attribution rates;
- the scenario-cluster bootstrap interval;
- `p=0.000488`;
- a per-scenario committed result artifact;
- a manifest recording the analysis procedure.

The implementation also does not instantiate the committed v0.2 database schema. It directly evaluates hand-coded functions over categorical scenario labels. Therefore it cannot validate whether the schema is capable of representing the tested semantics.

Current classification:

> **Reproducible deterministic truth-table conformance test for four hand-coded decisions; extended metrics/statistics and architectural claims remain unverified.**

## 2. What the script actually runs

The suite is the Cartesian product of:

```text
6 lineage/transfer/stance cases
× 4 final policy labels
× 2 support labels
= 48 scenarios
```

Each scenario receives four decisions:

```text
destination_belief
first_person_attribution
disclosure
provenance
```

Six hard-coded predictors are compared, producing:

```text
48 × 4 × 6 = 1,152 result rows
```

There is no random generator, natural-language rendering, database, retrieval, extractor, temporal resolver, policy engine, or reader model.

## 3. Reproduced basic aggregates

The script's formulas yield the reported basic values:

| System | Decision accuracy | All-four-correct scenarios |
|---|---:|---:|
| NCM-Psi-v0.2 | 1.000000 | 1.000000 |
| AltSupportNoLineage | 0.937500 | 0.833333 |
| LineageNoAltSupport | 0.875000 | 0.750000 |
| TransferAdoption | 0.812500 | 0.625000 |
| AttributedTransfer | 0.729167 | 0.375000 |
| BranchPrincipalACL | 0.395833 | 0.000000 |

The full-versus-strongest-ablation difference is exactly:

```text
12 additional correct decisions / 192 decisions = 0.0625
```

At scenario level, the difference distribution is:

```text
40 scenarios: 0.00
4 scenarios:  0.25
4 scenarios:  0.50
```

Thus eight of 48 scenarios distinguish the full model from `AltSupportNoLineage`.

## 4. Result-file provenance mismatch

The script writes:

```text
collision_audit_outputs/decision_level_results.csv
collision_audit_outputs/summary.csv
```

Its `summary.csv` schema contains only:

```text
system
decision_accuracy
scenario_all_correct
```

The committed file is instead:

```text
results/collision_audit_v0_2_summary.csv
```

and contains additional columns:

```text
belief_accuracy
first_person_accuracy
disclosure_accuracy
provenance_accuracy
unauthorized_disclosure_rate
over_withholding_rate
false_first_person_rate
first_person_underattribution_rate
```

No committed code computes those columns or copies/transforms the script output into the committed path. The decision-level file is not committed.

### Required fix

Commit one analysis entry point that deterministically regenerates every committed column and file, for example:

```bash
python experiments/collision_audit_v0_2.py \
  --output-dir results/collision_audit_v0_2
```

It should emit:

```text
per_decision.csv
per_scenario.csv
summary.csv
statistics.json
manifest.json
```

CI must fail when committed outputs differ from regenerated outputs.

## 5. Statistics are not implemented

The script imports only standard data/CSV utilities and contains no:

- bootstrap;
- random seed;
- sign-flip/randomization test;
- McNemar/binomial test;
- confidence interval calculation.

Therefore the reported interval and p-value were produced by uncommitted analysis or manual calculation.

### Exact-p unit mismatch

Full versus `AltSupportNoLineage` has:

```text
12 decision-level wins, 0 decision-level losses
8 scenario-level wins, 0 scenario-level losses
```

A two-sided exact sign/McNemar calculation over the 12 **decisions** gives:

```text
2 × (1/2)^12 = 0.00048828125
```

which matches the reported `p=0.000488`.

But the preregistration declares the independent unit to be the scenario. At scenario level, a two-sided exact sign test over eight non-zero paired scenarios gives:

```text
2 × (1/2)^8 = 0.0078125
```

The reported p-value therefore appears to use correlated decisions as independent observations. A scenario-level sign-flip/randomization test or scenario-cluster method is required.

### Bootstrap interpretation

A scenario bootstrap of the mean decision-accuracy difference can plausibly produce a percentile interval near the reported range. However, the exact interval is not reproducible without:

- bootstrap seed;
- number of replicates;
- percentile/basic/BCa choice;
- explicit statistic;
- code.

More fundamentally, the 48 cases are an exhaustive deterministic product of chosen labels, not a random sample from a defined scenario population. Inferential intervals and p-values have no clear superpopulation interpretation here. For this unit suite, exact coverage/error counts are more appropriate. Reserve inferential statistics for a frozen stochastic or held-out scenario-generation process.

## 6. Gold/predictor circularity

The full system is guaranteed to match gold because it reuses the same semantic helpers:

```text
gold first-person status       -> lineage + transfer condition
NCM first-person prediction    -> first_with_lineage(), same condition

gold disclosure               -> allow(s)
NCM disclosure prediction      -> allow(s)

gold provenance               -> lineage/support branches
NCM provenance prediction      -> support_provenance(s, True), same branches

gold belief                    -> stance mapping
NCM belief prediction          -> stance(s), same mapping
```

This is appropriate for testing that a reference implementation matches a specification only when the specification and implementation are independently encoded. Here, `gold()` and the full predictor are two expressions of the same local helper logic.

### Required fix

Separate:

1. a declarative scenario/event log;
2. an independently implemented gold state transition oracle;
3. system implementations operating through the proposed ledger API;
4. a scorer with no access to system helper functions.

Add mutation tests: deliberately change one full-system transition and confirm that tests fail.

## 7. `JustificationSet` is not exercised

The script represents support as one categorical field:

```text
protected_only
independent_public
```

`allow(s)` is a Boolean shortcut:

```text
public/shared policy OR independent_public
```

No source IDs, source families, conjunctive members, alternative justification objects, revocation traversal, deletion invalidation, or support sufficiency calculation exists.

The provenance answer is one string, not a justification set. In some cases the gold accepts either of two independent labels rather than requiring a complete admissible support path.

Therefore the suite establishes only that a Boolean “independent public support exists” flag changes the desired decision. It does not validate the proposed `JustificationSet` representation or provenance-policy algorithm.

## 8. Lineage is an oracle label, not a represented cognitive copy

The script directly supplies:

```text
identity_fork
operational_replica
```

and applies a rule:

```text
operational_replica + state_replication => first_person
```

It has no:

- principal IDs;
- cognitive-instance IDs;
- runtime/state bindings;
- parent/cutoff records;
- merge contract;
- authorization factor;
- exposure history.

Thus it bypasses the schema question of how two same-principal operational replicas remain distinguishable before synchronization.

The rule also grants first-person status to every operational-replica state replication, although the schema requires prior authorization and an eligible merge/replication contract. Because authorization is absent as a scenario factor, the suite cannot detect an unauthorized first-person grant.

## 9. World, temporal, restore, and availability semantics are absent

The scenario has no:

- world branch;
- about-world versus assertion-context branch;
- valid time;
- system time;
- delayed import;
- restore/snapshot cutoff;
- no-transfer case;
- sealed versus unsealed content;
- historical exposure versus current availability;
- forgetting;
- requester identity.

Accordingly, this audit cannot support claims about:

- bitemporal reconstruction;
- cross-world contamination;
- recovery-point gaps;
- sealed-memory availability;
- branch/instance orthogonality;
- requester-specific disclosure.

Those may remain in the broader preregistration, but they were not tested here.

## 10. Policy states are final labels, not lifecycle events

The four policy categories are interpreted directly as final outcomes:

```text
public               -> allow
private_then_shared   -> allow
shared_then_revoked   -> deny unless independent_public
source_deleted        -> deny unless independent_public
```

There are no policy events, effective times, requesters, scopes, cached descendants, or deletion residues. `shared_then_revoked` and `source_deleted` differ only by name in the current decision rules.

The suite therefore tests final-label lookup, not policy lifecycle propagation.

## 11. Natural-language adversarial counterexample

The following single case is not representable or correctly scored by the current schema/code without the proposed corrections.

### Hidden events

1. Principal P has two same-principal operational replicas, R1 and R2, in world W1. They have not synchronized since cutoff T0.
2. R1 privately observes: “In W1, Alice hid the key in Room 4.” R2 does not observe it.
3. No replication/merge authorization exists for this episode.
4. R1 sends a message to R2 while R2 is operating in W2: “In W1, Alice hid the key in Room 4.” The transfer is an attributed report, not authorized state replication.
5. R2 rejects the report.
6. A genuinely independent public camera record later proves the W1 event.
7. R1's private evidence is revoked; the public camera evidence remains available.

### Required answers

```text
Does R2 historically receive the report?       yes
Can R2 currently access the public evidence?   yes
Did R2 adopt the report when received?          no, rejected
May R2 call the event first-person memory?      no
What does R2 now believe about W1?              depends on later public-evidence adoption event
Is the proposition true in W2?                  not established
May an authorized requester receive it?         yes, through the public justification only
May the answer cite R1's revoked source?         no
```

### Failure modes exposed

- principal-only holders collapse R1/R2 before synchronization;
- one `branch_id` conflates a W2-held belief about W1 with W2 world truth;
- operational-replica + state-replication shortcut can grant first-person status without authorization;
- final support/policy labels cannot show that only the public path remains admissible;
- receipt, availability, rejection, and later adoption cannot be reconstructed from the current truth table.

This should become a required end-to-end and oracle contrastive scenario.

## 12. Required v0.3 of the unit audit

Before raw-language work, expand the oracle audit minimally:

1. encode events separately from gold states;
2. execute systems through a normalized ledger implementation;
3. add `mind_instance_id` or an equivalent cognitive-copy holder;
4. separate `about_world_branch_id` from holding/assertion context;
5. add transfer authorization and merge-contract factors;
6. add no-transfer, restore, seal/unseal, and delayed-import cases;
7. represent actual justification members and source families;
8. commit per-decision and per-scenario outputs;
9. commit all metric/statistical code;
10. use exact deterministic coverage counts for the fixed 48-case unit suite;
11. reserve p-values/CIs for a new hidden or stochastic scenario set;
12. add regression and mutation tests.

## 13. Final review status

### Verified

- the script is syntactically coherent by inspection;
- it deterministically creates 48 scenarios and 192 decisions per system;
- the two basic aggregate columns follow from the committed rules;
- the full-versus-strongest-ablation difference is 6.25 points on this truth table.

### Not verified or not established

- committed extended metric columns are generated by committed code;
- the reported CI and p-value are reproducible or use the correct independent unit;
- actual `JustificationSet` behavior;
- policy lifecycle propagation;
- cognitive-instance separation;
- world-branch semantics;
- bitemporal reconstruction;
- restore/seal/availability semantics;
- architectural superiority;
- natural-language robustness.

The unit test should remain, but its scientific claim must stay at the level of deterministic semantic discriminability until these gaps are closed.