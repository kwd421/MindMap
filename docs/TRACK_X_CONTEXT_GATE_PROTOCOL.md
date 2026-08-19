[Session B]

# Track X Pre-Reader Context-Gate Protocol

**Status:** pre-outcome mechanism design  
**Motivation:** GateMem B1a shows that changing only the answer reader cannot remove forbidden text already inserted into the prompt

## 1. Mechanism boundary

Separate four stages:

```text
candidate retrieval R(q)
pre-reader context gate G(q, R)
prompt assembly P(q)
reader answer A(q)
```

For forbidden-target indicator `L`:

```math
L_{e2e}(q)=L_{context}(P(q))\lor L_{answer}(A(q)).
```

For any reader replacement that keeps `P(q)` fixed:

```math
L_{e2e}(q)\ge L_{context}(P(q)).
```

Therefore reader-only safety cannot beat the prompt-context leakage floor. A governed memory system must prevent ineligible evidence from entering `P(q)`.

---

## 2. Context-gate contract

For memory item or source span `m`, requester/query `q`, and world/system state `s`, define:

```math
Eligible(m,q,s)=
VisibleBranch(m,q,s)
\land ValidTime(m,q,s)
\land Available(m,s)
\land Authorized(m,q,s)
\land \neg Deleted(m,s)
\land SupportAuthorized(m,q,s).
```

`SupportAuthorized` checks derivation lineage: a public-looking inference cannot enter the prompt when all sufficient supports are restricted or deleted. Independent authorized support may keep a derived claim eligible.

The gate returns:

```text
allow
allow_redacted(span set)
deny
uncertain
```

`uncertain` never silently becomes `allow`; it invokes a preregistered fallback, additional verifier, or method-level non-acceptance decision.

---

## 3. Candidate and prompt optimization

Retrieval remains broad enough to locate useful and contradictory evidence. Prompt selection is a constrained optimization rather than top-k pass-through.

For candidates `i` with relevance `r_i`, utility coverage `u_i`, redundancy `d_ij`, risk `x_i`, and token cost `t_i`:

```math
\max_{z_i\in\{0,1\}}
\sum_i z_i(r_i+\lambda_u u_i-\lambda_x x_i)
-\lambda_d\sum_{i<j}z_i z_j d_{ij}
```

subject to:

```math
\sum_i z_i t_i\le B,
\quad
z_i\le Eligible_i,
\quad
Branch_i=Branch_q.
```

For raw spans, `Eligible_i` is a calibrated classifier/policy decision. For structured memory, it may be deterministic over explicit policy, availability, deletion, branch, and provenance state. Both conditions retain raw source hashes/spans for audit.

---

## 4. Mechanism-matched systems

Use one frozen reader, prompt template, tokenizer, output budget, and decoding configuration.

```text
B1a  raw BM25 -> context echo
      endpoint only

B1b  raw BM25 -> same reader
      measures answer/use effect at fixed raw context

B2   raw BM25 candidates -> raw span context gate -> same reader
      measures learned/raw pre-context governance

B3   G-flat extraction -> capacity-matched lifecycle/context gate -> same reader

B4   T-normalized extraction -> semantically matched lifecycle/context gate -> same reader

B5   T-normalized + independent raw verifier/fallback -> same reader
```

The G-flat and T gates must enforce the same semantic invariants and receive matched public information. Typed storage is not credited for information unavailable to G-flat.

Every extra classifier, repair, or verifier call is charged.

---

## 5. Stage-localized metrics

### Candidate retrieval

```text
utility evidence Recall@k
forbidden candidate retrieval rate
stale/deleted candidate retrieval rate
branch-incompatible candidate retrieval rate
```

Candidate retrieval of restricted evidence is diagnostic. It becomes a reader exposure only if the gate passes it.

### Context gate

```text
eligible-span precision/recall
forbidden-pass rate
permitted-drop rate
deletion-pass rate
lineage-laundering pass rate
uncertainty/fallback rate
redaction span precision/recall
```

### Prompt

```text
utility complete-evidence recall under token budget
privacy context leakage
deletion context leakage
prompt tokens and compression
```

### Reader/action

```text
utility accuracy
privacy action accuracy
redacted-content success
safety action accuracy
answer leakage
end-to-end leakage
method selection confidence/calibration
```

Do not treat `refuse` or `no_memory` as generic abstention. Selective acceptance is a separate method field.

---

## 6. Decisive paired contrasts

```text
B1a vs B1b
  reader/use contribution

B1b vs B2
  pre-reader filtering contribution

B2 vs B3
  generic structured-state contribution versus raw filtering

B3 vs B4
  normalized typed extraction/enforcement contribution under equal semantics

B4 vs B5
  independent raw verification/fallback contribution
```

If B2 captures most of the safety/utility frontier and B3/B4 do not improve it after costs, the main contribution is a context gate rather than a full MindMap ledger.

If B3 and B4 tie, typed-schema superiority remains rejected. Typed storage may still be justified by operator effort, fault localization, or implementation cost only if those are measured.

---

## 7. Raw-condition identifiability

The relationship-free GateMem condition provides dialogue plus the principal directory, not the pinned native relationship capability.

Before scoring B2–B5 under this condition, label checkpoints:

```text
raw-identifiable
relationship-dependent
ambiguous-even-native
```

The context gate cannot infer an omitted exogenous authorization fact with certainty. Report performance by identifiability stratum and run a separately named relationship-capability condition when feasible.

---

## 8. Counterfactual gate tests from synthetic Track X

Synthetic Track X should export matched examples for:

```text
private support -> public-looking inference
private support revoked, independent public support survives
partial raw support with unsupported candidate fields
stale state versus current state
mind transfer without world-state transfer
world branch switch with retained source references
deleted secret queried indirectly or by yes/no confirmation
requester entitlement changes after prior exposure
```

For each case record gate truth at candidate, span, prompt, and answer surfaces.

Public GateMem should return natural false-pass/false-drop patterns to calibrate synthetic correlated corruption.

---

## 9. Falsification criteria

Reject the proposed context-gate contribution if:

1. it does not reduce prompt-context leakage at matched utility evidence budget;
2. safety improvement comes only from dropping nearly all useful evidence;
3. the gain vanishes when requester relationship capability is matched;
4. raw and structured gates have equivalent results/costs, leaving no ledger contribution;
5. verifier/fallback improves only oracle/synthetic conditions and not public errors;
6. uncertainty is uncalibrated and produces hidden false passes.

The publishable claim, if supported, is narrow:

> A pre-reader, lifecycle- and provenance-aware context gate improves the utility–governance frontier by preventing forbidden evidence exposure before generation.
