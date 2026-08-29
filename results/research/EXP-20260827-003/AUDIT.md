# EXP-20260827-003 audit

**Study class:** preregistered feasibility pilot  
**Execution:** 2026-08-27 14:44:34–14:45:30 UTC  
**Preregistration commit:** `e4101a5b0030ee73188c697c215c01db8ac8bb21`  
**Executed code:** detached `c2cdc7999fb2d3ea9289a81edb9f189ed03287bb`  
**Official LongMemEval harness:** `9e0b455f4ef0e2ab8f2e582289761153549043fc`

The official `src/evaluation/evaluate_qa.py` SHA-256 was
`ecce9c4c79dc89d99534ac17b383a5cbb5b9f0c69ee98adaf0684742e3d95251`.

## Frozen design

Eight questions were selected before answer inspection: one non-abstention item
from each of six question types and two abstention items. Selection used the
lowest SHA-256 rank under seed `EXP-20260827-003-v1`; the ordered question-ID
hash was `c0e75cb7dce45e7f70cc0aedfca6c1ef9fe6620bfb1b3fa09620917202720e6f`.

All three arms used `deepseek-v4-flash`, thinking disabled, temperature 0, and
the same answer instructions:

- `no_memory`: question only;
- `bm25_top3`: three locally ranked LongMemEval-S sessions;
- `oracle_context`: official evidence-only sessions.

The judge used the same model and a frozen local adaptation of LongMemEval's
official rubric. It was not the official GPT-4o metric.

## Results

| Arm | Judge-correct | Estimated cost | Mean answer latency |
|---|---:|---:|---:|
| no memory | 2 / 8 | $0.000788 | 1.386 s |
| BM25 top-3 | 7 / 8 | $0.016789 | 1.806 s |
| oracle context | 7 / 8 | $0.009586 | 1.532 s |

BM25 retrieved 12/13 official answer-bearing sessions and covered every
official answer session for 7/8 questions. All 24 answer calls and 24 judge
calls succeeded on their first attempt. A researcher review agreed with the 24
pilot-judge labels, but this was not a blinded or independent human evaluation.

Token accounting across answers and judges:

```text
cache-miss input: 118,832
cache-hit input:      128
output:             1,543
estimated cost: $0.027162316
```

The DeepSeek balance endpoint reported `$8.57` both before and immediately
after the run. Its displayed two-decimal balance did not provide a usable billed
cost for this run, so the actual billed value remains unknown and the token-rate
estimate is reported separately.

## Decisive failure

Question `a96c20ee_abs` asks where the user presented a poster for an
**undergraduate course research project**. The official answer says this was
not stated. Both BM25 and oracle context led the reader to answer **Harvard
University**, borrowing a location from a different thesis/conference-poster
event.

This is not primarily a retrieval miss: the oracle arm failed too. It is a
boundary and event-attribution failure in which semantically adjacent evidence
is substituted for the requested event. The finding motivates explicit event
identity, provenance, relation qualifiers, and abstention when the requested
event is unsupported.

One temporal question was answered correctly after BM25 retrieved only one of
two answer-bearing sessions. This shows that official answer-session recall and
answer correctness are related but not identical; both must be reported.

## Validity threats

- Eight items are too few for a stable performance estimate.
- The same model answered and judged, creating correlated error risk.
- The local rubric is not the official evaluator and was slightly clarified for
  knowledge-update strictness.
- `deepseek-v4-flash` is a hosted alias; the response did not expose a dated
  model revision beyond that returned name.
- Prompt token counts show BM25 top-3 was more expensive than oracle evidence;
  the arms measure feasibility, not a matched token-budget comparison.
- The runner omitted explicit start/end timestamps and provider response IDs
  from the JSON artifacts. Filesystem timestamps were used for this audit; the
  runner must be fixed before the next study.

## Claim boundary

The pilot establishes that the harness, frozen sample, retrieval arm, token
accounting, and paid model path work end to end. It reveals one concrete
abstention/event-attribution failure. It is not an official LongMemEval score,
not confirmatory evidence, and not a MindMap comparison.
