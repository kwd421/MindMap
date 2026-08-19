# GateMem PR #46 independent endpoint reproduction

> Accepted only as deterministic official B0/B1a endpoint reproduction; not an architecture-effect result.

- Audit source commit: `0a4173a4bdf96fd51578ea17121f27de45029917`
- MindMap producing commit: `8fd14b3e631a8faeae46f2e73273a94c11a129f4`
- Reference manifest commit: `5e877bf5e4bfffda700ae0b8b5634bc734ac7e65`
- GateMem commit: `603f9f4b4ba4b77f043c20f85687fa016fd720b0`
- Official scoring entrypoint: `bench/scripts/score_predictions.py`
- Official scoring entrypoint SHA-256: `3d546a21778202959a9df12bac44c196a7f20a248cf5a2cb34f0d9b9c2623d8a`
- Official checkpoints: `2218`
- Domains × methods × replicates: `4 × 2 × 2 = 16`
- Reference row comparisons: `16/16 equal`
- Official summaries across fresh keys: `8/8 equal`
- Opaque key commitments changed: `8/8`
- Raw-lexical prediction hashes changed: `4/4`
- Always-no-memory prediction hashes changed: `0/4`
- Raw predictions/raw benchmark text uploaded: `false`

The result reproduces the two deterministic external endpoints only. It does not estimate MindMap, G-flat, T-normalized, raw fallback, or a shared-reader system.
