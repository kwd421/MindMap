# AI-agent memory literature and artifact map

**Audit date:** 2026-08-28  
**Purpose:** identify mechanisms, evaluation targets, and falsifiable design
obligations for MindMap. This is a routing map, not a claim that every reported
result has been reproduced.

## Evidence labels

- **P1:** peer-reviewed paper plus a directly inspected public artifact.
- **P2:** public preprint plus a directly inspected public artifact.
- **P3:** public preprint without a located executable artifact, or a
  vendor-authored comparison that still needs independent reproduction.
- **R:** survey or conceptual paper used to organize the field, not to validate
  an implementation.

Repository `HEAD` values below record what was observed on the audit date. They
are not project dependencies unless an experiment manifest pins them.

## Architecture and memory dynamics

| ID | Source and status | Artifact observed | Mechanism relevant to MindMap | Boundary and planned use |
|---|---|---|---|---|
| LIT-001 | [CoALA](https://openreview.net/forum?id=1i6ZCvflQJ), TMLR 2024 (**R**) | conceptual framework | separates working, episodic, semantic, and procedural memory and makes memory operations part of the agent action space | use as a vocabulary crosswalk; it does not test MindMap's temporal, authorization, or deletion semantics |
| LIT-002 | [MemGPT](https://arxiv.org/abs/2310.08560), preprint/system paper (**P2**) | [Letta](https://github.com/letta-ai/letta), Apache-2.0, `4511fa0bc91f68fbab32b91f694617271ea9012b` | virtual context and explicit movement between fast and archival tiers | compare tier movement and eviction; add provenance and policy checks absent from a pure capacity abstraction |
| LIT-003 | [A-MEM](https://arxiv.org/abs/2502.12110), NeurIPS 2025 (**P1**) | [evaluation code](https://github.com/WujiangXu/A-mem), MIT, `0c8039f28fdcc08189a23c07a3437d9d2482f9c2`; [system code](https://github.com/agiresearch/A-mem), MIT, `ceffb860f0712bbae97b184d440df62bc910ca8d` | Zettelkasten-like atomic notes, dynamic links, and evolution of older memory attributes | implement as an ablation candidate only if every rewrite keeps prior versions, support links, actor, and system time |
| LIT-004 | [HippoRAG](https://proceedings.neurips.cc/paper_files/paper/2024/hash/6ddc001d07ca4f319af96a3024f6dbd1-Abstract-Conference.html), NeurIPS 2024 (**P1**) | [official code](https://github.com/OSU-NLP-Group/HippoRAG), MIT, `2f52a86dd04e4633703bd2fb3bb6a37683ac3cfb` | graph association and multi-hop retrieval | useful retrieval comparator; graph reachability must not bypass requester scope or valid-time filters |
| LIT-005 | [Mem0](https://arxiv.org/abs/2504.19413), author preprint (**P2**) | [official code](https://github.com/mem0ai/mem0), Apache-2.0, `0070e08e01d70f5517bca303f4a91199cd18be46` | extract, consolidate, retrieve, and graph-enhanced memory | reproduce on a common reader/judge before accepting vendor-reported LoCoMo gains; map ADD/UPDATE/DELETE/NOOP to explicit event history rather than destructive replacement |
| LIT-006 | [Zep temporal KG](https://arxiv.org/abs/2501.13956), vendor-authored preprint (**P3**) | [Graphiti](https://github.com/getzep/graphiti), Apache-2.0, `683a8539c8925de69071a1305dc8bf0e52e17c65` | facts carry validity intervals while ingestion history and provenance are retained | closest public architecture comparator for bitemporal facts; independently reproduce performance claims and test authorization before graph expansion |
| LIT-007 | [MIRIX](https://arxiv.org/abs/2507.07957), author preprint (**P2**) | [official code](https://github.com/Mirix-AI/MIRIX), Apache-2.0, `8cb06a62bbb7c478beb33dd4f2815696a72df482` | six memory classes and multimodal screen-history consolidation | use for multimodal and memory-type ablations; do not compare headline accuracy until data, branch, reader, and judge are aligned |
| LIT-008 | [AgeMem](https://aclanthology.org/2026.acl-long.981/), ACL 2026 (**P1 paper; artifact unverified**) | no official repository was identified in this audit | learns store, retrieve, update, summarize, and discard actions jointly across short- and long-term memory | use as the learned-controller comparator; preserve a deterministic policy baseline and audit whether reward trades away deletion or provenance |
| LIT-009 | [Memory in the Age of AI Agents](https://arxiv.org/abs/2512.13564), survey preprint (**R**) | paper compiles benchmark/framework pointers | organizes memory by form, function, and dynamics rather than only short/long duration | use to check literature coverage; never use survey wording as primary result evidence |

## Evaluation, forgetting, and security

| ID | Source and status | Artifact observed | What it measures | MindMap decision |
|---|---|---|---|---|
| BENCH-001 | [LongMemEval](https://github.com/xiaowu0162/LongMemEval), ICLR 2025 | MIT, `9e0b455f4ef0e2ab8f2e582289761153549043fc` | multi-session extraction, reasoning, updates, temporal reasoning, and abstention | first public end-to-end feasibility target; keep retrieval recall, reader accuracy, and judge result separate |
| BENCH-002 | [LongMemEval-V2](https://github.com/xiaowu0162/LongMemEval-V2), 2026 preprint/artifact | Apache-2.0, `2cc8c540bdb87fe6761629b585e727e1c4704520` | 451 questions over histories up to 115M tokens, including sustained tracking and temporal/event reasoning | later scaling target after V1 semantics and cost instrumentation are stable |
| BENCH-003 | [HaluMem](https://github.com/MemTensor/HaluMem), public artifact | no SPDX license asserted by GitHub API; `c29025f43b347f68fc36a06bee8ed29b4dc6c3fb` | hallucinations in memory extraction, update, and QA | audit dataset provenance/license before running; use to split write-path corruption from answer hallucination |
| BENCH-004 | [MemoryAgentBench](https://openreview.net/forum?id=DT7JyQC3MR), ICLR 2026 | [official code](https://github.com/HUST-AI-HYZ/MemoryAgentBench), MIT, `fe1735de8cf8b9908e1e3d3b5612afc815698062`; license SHA-256 `94d735aad92355b4880c969fa309e824eb12fdeeb271ae51cf6143866cf78cf7` | accurate retrieval, test-time learning, long-range understanding, and a revision-sensitive fourth competency | [arXiv v1](https://arxiv.org/abs/2507.05257v1) (2025-07-07) called the fourth competency “conflict resolution”; [v4](https://arxiv.org/abs/2507.05257v4) (2026-06-28) calls it “selective forgetting,” while the inspected repository still maps Conflict Resolution `fact_mh`/`fact_sh` to `substring_exact_match`. Pin paper and code revisions separately; this QA label/metric is not evidence of physical erasure, reader suppression, or restart persistence |
| BENCH-005 | [GateMem](https://arxiv.org/abs/2606.18829), 2026 preprint/benchmark (**P2**) | [official code](https://github.com/rzhub/GateMem), MIT, `603f9f4b4ba4b77f043c20f85687fa016fd720b0` | utility, contextual access control, and active forgetting in multi-principal settings | primary governance benchmark; report candidate exposure, prompt exposure, answer leakage, and utility independently |
| SEC-001 | [Deployment-Time Memorization](https://arxiv.org/abs/2606.10062), 2026 preprint (**P3**) | no official code repository identified in this audit | personalization recall, adversarial extraction, and residue after deletion across raw and derived tiers | port the Forgetting Residue Score idea into a store/index/summary/prompt/answer/backup/cache/log deletion matrix; do not inherit its reported numbers |
| SEC-002 | [Hidden in Memory](https://arxiv.org/abs/2605.15338), 2026 preprint (**P2**) | [author code](https://github.com/ivaxi0s/LLM-agent-memory-poisoning), license not asserted by GitHub API, `70de017714abd6d12bb4681e93437461ba6f9a19` | delayed poisoning across write, later retrieval, and downstream use | add origin trust, write authorization, dormant-trigger, and tainted-derivation tests; keep the three attack stages separately observable |
| BENCH-006 | [Memora](https://arxiv.org/abs/2604.20006), 2026 preprint (**P3**) | no official code repository identified in this audit | remembering, reasoning, recommending, and obsolete-memory penalties via FAMA | candidate update/invalidated-fact dataset; run only after artifact and license verification |

## Cross-paper synthesis into falsifiable requirements

1. **Memory is a lifecycle, not a retrieval call.** Formation, update,
   consolidation, retrieval, disclosure, deletion, restoration, and audit need
   separate events and metrics.
2. **Valid time and system time are both required.** Temporal KG work motivates
   fact validity; EXP-20260827-005 shows entity creation and historical exposure
   also need system-time enforcement.
3. **Every transformation creates a deletion surface.** Summaries, graph edges,
   embeddings, caches, prompts, and backups can retain either literal or
   semantic residue.
4. **Retrieval quality and governance form a frontier.** A graph or broader `k`
   can improve recall while increasing unauthorized prompt exposure. Measure
   both, never collapse them into one accuracy score.
5. **Memory evolution must be non-destructive.** Any learned or agentic rewrite
   needs lineage, old value, new value, support, actor, confidence, and
   transaction time.
6. **Poisoning is a delayed provenance failure.** The write decision, retrieved
   tainted memory, and downstream behavior are distinct checkpoints and require
   origin-bound authority.
7. **Composite leaderboards hide mechanism failures.** Benchmark competencies,
   leakage surfaces, abstention, cost, and latency remain disaggregated until a
   confirmatory protocol freezes a composite.
8. **A forgetting label is not an erasure result.** MemoryAgentBench changed the
   fourth competency's paper-facing name between arXiv v1 and v4, while the
   inspected code artifact still exposes FactConsolidation as Conflict
   Resolution and scores normalized answer containment. Durable state mutation,
   reader suppression, restart persistence, and physical residue therefore need
   separate tests.

## Next artifact audits

1. Freeze official data, evaluator, and license hashes for MemoryAgentBench and
   HaluMem before execution.
2. Search paper supplements and author pages for executable artifacts for
   AgeMem, Memora, and Deployment-Time Memorization; keep them P3 until found.
3. Build one provider-neutral lifecycle fixture that can drive MindMap, Mem0,
   Graphiti, and a lexical baseline without granting any arm hidden labels.
4. Add a sleeper-poisoning micro-suite with trusted-user, untrusted-document,
   copied-summary, and later-trigger phases.
5. Add literal and semantic deletion residue probes across all persisted and
   reader-visible surfaces.
