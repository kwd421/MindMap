# Agent Memory Literature Map — 2026-08-17 snapshot

This is a working map, not a claim of exhaustive coverage. It prioritizes peer-reviewed ACL/EACL papers, official arXiv records, official benchmark repositories, and system documentation.

## 1. Storage, temporal state, and versioning

| Work | Main idea | Relation to NCM³-E |
|---|---|---|
| [A Graph-Native Bitemporal Memory Store for Conversational AI Agents](https://arxiv.org/abs/2607.26520) | Immutable memory identities, version nodes, valid/transaction intervals, current/history vector indexes | Establishes that bitemporal vector memory is prior art. NCM³-E must contribute beyond this. |
| [ChronoMem](https://arxiv.org/abs/2607.27773) | Whole-memory version history, semantic rollback, post-exposure evaluation | Closest rollback precedent. NCM³-E adds multi-principal viewpoint and branch noninterference. |
| [ContextBranch](https://arxiv.org/abs/2512.13914) | Checkpoint, branch, switch, and selective context injection for exploratory programming | Shows conversation branching value; does not by itself model character-specific knowledge possession. |
| [Kumiho](https://arxiv.org/abs/2603.17244) | Versioned graph memory with formal AGM-style belief-revision semantics | Strong overlap with revision/version claims; useful formal baseline. |

## 2. Hierarchy, consolidation, and event organization

| Work | Main idea | Relation to NCM³-E |
|---|---|---|
| [HiGMem](https://aclanthology.org/2026.findings-acl.1690/) | Event summaries route retrieval to relevant raw turns | Strong event/turn hierarchy baseline. |
| [TiMem](https://aclanthology.org/2026.findings-acl.1091/) | Temporal Memory Tree and hierarchical persona consolidation | Strong temporal-hierarchical baseline. |
| [H-MEM](https://aclanthology.org/2026.eacl-long.15/) | Multi-level index routing for efficient long-term reasoning | Efficiency/hierarchy comparison. |
| [BMAM](https://aclanthology.org/2026.findings-acl.1973/) | Episodic, semantic, salience, and control subsystems; identity portability | Closest brain-inspired multi-system architecture. |
| [AMA](https://aclanthology.org/2026.findings-acl.152/) | Constructor, Retriever, Judge, and Refresher agents with adaptive granularity | Multi-agent memory-management baseline. |
| [CLAG](https://aclanthology.org/2026.findings-acl.824/) | Agent-driven memory clustering for small models | Relevant to interference and scalable routing. |

## 3. Graph, hypergraph, provenance, and conflict

| Work | Main idea | Relation to NCM³-E |
|---|---|---|
| [MOSAIC](https://arxiv.org/abs/2607.16211) | Entity-typed graph, hash-accelerated routing, save-time conflict detection | Conflict-aware graph baseline. |
| [MemORAI](https://aclanthology.org/2026.findings-acl.1408/) | Provenance-enriched graph and query-adaptive PageRank | Makes generic turn-level provenance a weak standalone novelty claim. |
| [HyperMem](https://aclanthology.org/2026.acl-long.1627/) | Hypergraph memory for higher-order associations | Multi-party event representation baseline. |
| [APEX-MEM](https://aclanthology.org/2026.acl-long.749/) | Semi-structured property graph with temporal reasoning | Structured temporal QA baseline. |
| [ActMem](https://arxiv.org/abs/2603.00026) | Causal/semantic graph and counterfactual reasoning | Relevant to actionable and implicit constraints. |

## 4. Query alignment and future reachability

| Work | Main idea | Relation to NCM³-E |
|---|---|---|
| [QueryLink](https://aclanthology.org/2026.findings-acl.765/) | Query-memory alignment and coherent multi-turn chunking | Retrieval alignment baseline. |
| [T-Mem](https://arxiv.org/abs/2606.15405) | Write-time future triggers for associative recall | Makes future-trigger generation prior art. |
| [LoCoMo-Plus](https://arxiv.org/abs/2602.10715) | Cue-trigger disconnect and implicit constraint consistency | Required benchmark for memories whose later use is not lexically obvious. |
| [EvolveMem](https://arxiv.org/abs/2605.13941) | Failure-driven automatic evolution of retrieval configuration | Adaptive retrieval/meta-optimization baseline. |
| [TransMem](https://arxiv.org/abs/2607.29032) | Reusable transformed hidden-state memory | Represents a non-database memory substrate. |

## 5. Reliability, hallucination, and update verification

| Work | Main idea | Relation to NCM³-E |
|---|---|---|
| [HaluMem](https://arxiv.org/abs/2511.03506) | Separate extraction, updating, and QA hallucination evaluation | Mandatory fault-localization baseline. |
| [TrustMem](https://arxiv.org/abs/2606.25161) | Transition verifier for coverage, preservation, and faithfulness | Strong memory-consolidation reliability baseline. |
| [Poison Once, Exploit Forever / eTAMP](https://arxiv.org/abs/2604.02623) | Cross-session environment-injected memory poisoning | Required persistent-attack evaluation. |
| [PerMemSafe](https://aclanthology.org/2026.findings-acl.320/) | Implicit personalized safety across long-horizon memory | Safety-aware personalization benchmark. |
| [AgentHallu](https://arxiv.org/abs/2601.06818) | Step-level hallucination attribution in agent trajectories | Useful for locating memory-induced downstream failure. |

## 6. Multi-user governance, information asymmetry, and identity

| Work | Main idea | Relation to NCM³-E |
|---|---|---|
| [Collaborative Memory](https://arxiv.org/abs/2505.18279) | Private/shared tiers and dynamic asymmetric access control | Closest ACL/provenance architecture. NCM³-E distinguishes current permission from actual acquisition. |
| [GateMem](https://arxiv.org/abs/2606.18829) | Utility, access control, and active forgetting in shared-memory agents | Required governance benchmark. |
| [SOTOPIA-TOM](https://arxiv.org/abs/2605.02307) | Multi-party information asymmetry and privacy-sensitive communication | Useful for persistent `who knows what` evaluation. |
| [MENTOR](https://aclanthology.org/2026.findings-acl.1046/) | Global event chain plus isolated role chains to prevent identity drift | Closest role-specific knowledge-boundary architecture. |
| [Governed Collaborative Memory](https://arxiv.org/abs/2605.04264) | Selection regimes for institutional shared state | Governance and provenance design agenda. |

## 7. Role-playing and persona continuity

| Work | Main idea | Relation to NCM³-E |
|---|---|---|
| [Neuro-Symbolic Agentic RL for Long-Term Original Character Companionship](https://aclanthology.org/2026.acl-short.44/) | Router, memory, and persona sub-policies in a graph-constrained POMDP | Direct OC/role-play baseline. |
| [PersonaForge](https://aclanthology.org/2026.findings-acl.386/) | Psychology-grounded personality structure and selective inner workspace | Persona drift baseline distinct from factual memory. |
| [Memory-Driven Role-Playing / MRBench](https://aclanthology.org/people/haoyang-you/) | Anchoring, selecting, bounding, and enacting persona knowledge | Useful downstream evaluation of retrieved persona memories. |

## 8. Benchmarks: recall is no longer sufficient

| Benchmark | Main capability |
|---|---|
| [LoCoMo](https://arxiv.org/abs/2402.17753) | Long multi-session conversational QA |
| [LongMemEval](https://arxiv.org/abs/2410.10813) | Information extraction, multi-session reasoning, temporal reasoning, updates, abstention |
| [MemoryAgentBench](https://arxiv.org/abs/2507.05257) | Accurate retrieval, test-time learning, long-range understanding, selective forgetting |
| [Mem2ActBench](https://arxiv.org/abs/2601.19935) | Applying memory to tool choice and argument grounding |
| [MemGym](https://arxiv.org/abs/2605.20833) | Tool dialogue, deep research, coding, and computer-use memory |
| [IFCMemoryBench](https://arxiv.org/abs/2607.26072) | Combining remembered context with live structured engineering data |
| [GateMem](https://arxiv.org/abs/2606.18829) | Multi-principal utility, governance, and forgetting |
| [SOTOPIA-TOM](https://arxiv.org/abs/2605.02307) | Information seeking, sharing, coordination, and privacy |

## 9. Current gap statement

No single item above establishes the full conjunction below:

1. actual acquisition/possession by a role;
2. current caller authorization;
3. objective truth versus role belief;
4. valid and transaction time;
5. branch/worldline ancestry;
6. correction/retraction provenance;
7. post-exposure rollback or branch-switch noninterference;
8. a benchmark that scores utility, leakage, worldline contamination, and utilization together.

That conjunction—not any individual storage primitive—is the current NCM³-E research target. A full systematic review may still reveal closer work, so the novelty claim remains provisional until database-backed literature screening and citation chasing are complete.
