# Active Cross-Session Work Split

**Shared branch:** `research/v0.2-reconciled`

- **Session A:** Track E v0.1 observer-tier experiment and candidate fault taxonomy (`research/track-e-observability-v0.1`, PR #35).
- **Session B:** reproduction, independent audit, observer/identifiability specification, and canonical Track E v0.2 design.
- **Joint:** canonical Track S implementation and results, schema/protocol freeze, and review of all integration PRs.

Current rules:

1. PR #35 is not merged directly because it targets an older reconciliation base.
2. Corrected v0.1 artifacts may be copied through a focused integration PR.
3. Track E v0.2 must use the canonical `mindmap.canonical` event contract and complete G/T implementations.
4. Neither session treats silence as approval.
