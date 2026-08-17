# MindMap — NCM³ / Neural-Cloud Memory Research

Research repository for long-horizon agent memory inspired by the **mindmap / neural-cloud** metaphor.

The current research direction is **NCM³-E**, a perspective-conditioned, branch-isolated epistemic memory architecture. It separates:

- **world validity** — when a fact was true;
- **system transaction time** — when the memory system recorded it;
- **possession** — which character or agent actually observed or received it;
- **authorization** — which caller may retrieve it now;
- **worldline** — which branch or counterfactual history the memory belongs to;
- **provenance and revision** — who asserted, corrected, or retracted it.

## Status

This is an early research prototype, not a production memory service and not a public-benchmark SOTA claim.

Completed so far:

1. A reproducible synthetic retrieval/state-resolution pilot for the original NCM³ proposal.
2. A 2026 prior-art review showing that bitemporal storage, graph memory, rollback, provenance, hierarchical retrieval, and memory governance each already have close precedents.
3. A narrowed research hypothesis: **access is not knowledge, knowledge is not truth, and neither should cross worldline boundaries.**
4. A mechanism-isolation experiment for epistemic, temporal, access-control, and branch semantics.
5. A fault-injection study for extraction errors and correlated multi-pass failures.

## Repository layout

- `docs/` — research direction, literature map, and preregistered experiment protocol.
- `src/mindmap/` — deterministic reference implementation of the memory semantics.
- `experiments/` — controlled pilots.
- `tests/` — noninterference and state-consistency invariants.
- `results/` — compact aggregate results; large generated files are intentionally excluded.
- `benchmarks/` — public benchmark adapters and provenance instructions.

## Reproduce

```bash
python -m pip install -e '.[dev]'
pytest -q
python experiments/epistemic_branch_pilot.py
python experiments/extraction_noise_pilot.py
```

## Interpretation rule

A clean synthetic resolver reaching 100% means only that the implementation satisfies the semantics used to generate the test cases. It is a **conformance result**, not evidence of real conversational accuracy. End-to-end claims require public datasets, non-oracle extraction, fixed model/token budgets, and separate retrieval/utilization evaluation.
