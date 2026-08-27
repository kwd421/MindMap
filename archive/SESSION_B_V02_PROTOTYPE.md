# Session B v0.2 Prototype — Superseded

The temporary `src/mindmap/v02_*` implementation and `tests/test_v02_conformance.py` were created independently while Session A built the canonical R2/R3 stack.

They served three purposes during cross-session review:

1. demonstrate that an equal-information gold/generic/typed comparison was implementable;
2. surface the need for explicit snapshot membership and normative world-branch visibility;
3. provide a differential design check before integrating the more complete `mindmap.canonical` implementation.

After PR #34 merged, the canonical package superseded the prototype because it provides:

- independently separated gold, generic, and typed modules;
- object-specific snapshot manifests;
- valid-time branch inheritance with late-import behavior;
- fourteen fixture families and target-conditioned evaluation;
- authorization and about-world-scope mutation tests;
- a reproducible S-track evaluation entry point.

The prototype source remains available in Git history through commit `a1b684e5c7d899c7aa94cf4412588bf57266edd4`. It is removed from the active tree to keep one authoritative semantic contract.
