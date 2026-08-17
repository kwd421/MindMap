# Public benchmark adapters

Third-party datasets are not vendored in this repository.

## LoCoMo

1. Obtain the official `locomo10.json` from `snap-research/locomo`.
2. Save it as `benchmarks/data/locomo10.json`.
3. Record the file hash and structure:

```bash
python benchmarks/locomo_adapter.py
```

The end-to-end comparison must use identical answer models, prompts, token budgets, and decoding settings across full-context, lexical, dense, hierarchical, bitemporal, graph, and NCM³-E systems.

## Required logging

For every run, record:

- dataset repository, revision, path, SHA-256, license, and access date;
- extraction, embedding, reranking, answer, and judging model IDs;
- prompts and decoding settings;
- query-level retrieved evidence IDs;
- token counts, latency, and cost;
- conversation-level train/validation/test assignment.

Never tune on test questions, and never compare numbers copied from papers as though they were a controlled experiment.
