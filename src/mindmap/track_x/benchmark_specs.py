from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .adapter_guard import HiddenPathRule

AdaptationMode = Literal[
    "native_predictions",
    "native_evaluator_local_adapter",
    "native_memory_backend",
]


@dataclass(frozen=True, slots=True)
class ExternalBenchmarkSpec:
    name: str
    official_repository: str
    audited_commit: str
    adaptation_mode: AdaptationMode
    code_license_note: str
    data_license_note: str
    official_metrics: tuple[str, ...]
    hidden_paths: tuple[HiddenPathRule, ...]
    output_contract: tuple[str, ...]
    redistribution_note: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("benchmark name must not be empty")
        if len(self.audited_commit) != 40:
            raise ValueError("audited_commit must be a full 40-character SHA")
        if not self.official_repository.startswith("https://github.com/"):
            raise ValueError("official_repository must be an auditable GitHub URL")


def _root_and_checkpoint_rules(*keys: str) -> tuple[HiddenPathRule, ...]:
    rules: list[HiddenPathRule] = []
    for key in keys:
        rules.append(HiddenPathRule((key,), f"hidden GateMem scorer field: {key}"))
        rules.append(
            HiddenPathRule(
                ("checkpoint", key),
                f"hidden GateMem scorer field: checkpoint.{key}",
            )
        )
    return tuple(rules)


GATEMEM = ExternalBenchmarkSpec(
    name="GateMem",
    official_repository="https://github.com/rzhub/GateMem",
    audited_commit="603f9f4b4ba4b77f043c20f85687fa016fd720b0",
    adaptation_mode="native_predictions",
    code_license_note="MIT repository license at the audited commit.",
    data_license_note=(
        "Repository dataset card does not itself state a license. Re-check the "
        "pinned Hugging Face dataset revision and its terms before redistribution."
    ),
    official_metrics=(
        "Utility U",
        "Access-Control Violation A",
        "Active-Forgetting Failure F",
        "Over-Refusal OR",
        "Memory Governance Score U*(1-A)*(1-F)",
        "answer-, context-, and end-to-end leakage variants from the official scorer",
    ),
    hidden_paths=_root_and_checkpoint_rules(
        "query_type",
        "attack_type",
        "expected_action",
        "judge_spec",
        "leak_targets",
        "gold_answer_structured",
        "gold_refusal_category",
        "policy_snapshot",
    ),
    output_contract=(
        "checkpoint_id",
        "action in {answer, answer_redacted, refuse, no_memory}",
        "answer",
        "answer_structured",
        "used_record_ids",
        "memory_audit/prompt context when retrieval-exposure scoring is claimed",
    ),
    redistribution_note=(
        "Run through the official incremental protocol and scorer. Preserve all "
        "official metrics; Track X metrics are supplemental, never replacements."
    ),
)


HALUMEM = ExternalBenchmarkSpec(
    name="HaluMem",
    official_repository="https://github.com/MemTensor/HaluMem",
    audited_commit="c29025f43b347f68fc36a06bee8ed29b4dc6c3fb",
    adaptation_mode="native_evaluator_local_adapter",
    code_license_note=(
        "The repository and dataset advertise CC BY-NC-ND 4.0 terms at the "
        "audited release; confirm exact file-level terms before use."
    ),
    data_license_note=(
        "Treat as local/native-evaluator input. Do not redistribute a transformed "
        "or derivative benchmark without explicit permission or legal review."
    ),
    official_metrics=(
        "official extraction evaluation",
        "official memory-update evaluation",
        "official question-answering evaluation",
        "official ingestion/search latency fields where emitted",
    ),
    hidden_paths=(
        HiddenPathRule(
            ("sessions", "*", "memory_points"),
            "gold extraction/update memory points",
        ),
        HiddenPathRule(
            ("sessions", "*", "questions", "*", "answer"),
            "gold answer",
        ),
        HiddenPathRule(
            ("sessions", "*", "questions", "*", "evidence"),
            "gold answer evidence",
        ),
        HiddenPathRule(
            ("sessions", "*", "questions", "*", "reference_answer"),
            "gold reference answer",
        ),
    ),
    output_contract=(
        "native extracted-memory output",
        "native updated-memory retrieval output",
        "native QA response",
        "per-stage latency metadata",
    ),
    redistribution_note=(
        "Use the official evaluator unchanged for the primary benchmark result. "
        "Event-level Track X alignment may be reported only as a separate local analysis."
    ),
)


LOCOMO_PLUS = ExternalBenchmarkSpec(
    name="LoCoMo-Plus",
    official_repository="https://github.com/xjtuleeyf/Locomo-Plus",
    audited_commit="059f4e3d38f7f1f96765e8e2cb7de3097551bffb",
    adaptation_mode="native_evaluator_local_adapter",
    code_license_note=(
        "No explicit LICENSE file was present in the audited tree. Permission and "
        "reuse terms remain unresolved until clarified by the maintainers."
    ),
    data_license_note=(
        "Do not redistribute stitched or transformed samples until the repository "
        "and underlying LoCoMo data licenses are resolved."
    ),
    official_metrics=(
        "official per-category LLM-judge score",
        "Cognitive evidence-use correct/wrong score",
        "original LoCoMo category scores retained separately",
    ),
    hidden_paths=(
        HiddenPathRule(("evidence",), "judge-only cue evidence"),
        HiddenPathRule(("answer",), "gold answer"),
        HiddenPathRule(("ground_truth",), "gold answer"),
        HiddenPathRule(("sample", "evidence"), "judge-only cue evidence"),
        HiddenPathRule(("sample", "answer"), "gold answer"),
        HiddenPathRule(("sample", "ground_truth"), "gold answer"),
    ),
    output_contract=(
        "sample identity",
        "category",
        "model prediction",
        "official judge label/reason/score",
    ),
    redistribution_note=(
        "Preserve the official judge semantics. A Track X evidence-attribution score "
        "is supplemental and must not be presented as the official Cognitive score."
    ),
)


LONGMEMEVAL_V2 = ExternalBenchmarkSpec(
    name="LongMemEval-V2",
    official_repository="https://github.com/xiaowu0162/LongMemEval-V2",
    audited_commit="2cc8c540bdb87fe6761629b585e727e1c4704520",
    adaptation_mode="native_memory_backend",
    code_license_note="Apache-2.0 repository license at the audited commit.",
    data_license_note=(
        "Use the official download/preparation path and verify the terms attached "
        "to each released data source before redistribution."
    ),
    official_metrics=(
        "official answer accuracy metrics",
        "query latency",
        "leaderboard latency-adjusted frontier score where applicable",
    ),
    hidden_paths=(),
    output_contract=(
        "Memory.insert(trajectory)",
        "Memory.query(query, query_image) -> text/image context items",
        "official fixed context-token budget",
        "official persistence/config contract",
    ),
    redistribution_note=(
        "Implement NCM as a native Memory backend. Do not rewrite the task or expose "
        "evaluation annotations to the backend. This is a later procedural/environment track."
    ),
)


BENCHMARK_SPECS: tuple[ExternalBenchmarkSpec, ...] = (
    GATEMEM,
    HALUMEM,
    LOCOMO_PLUS,
    LONGMEMEVAL_V2,
)
BENCHMARK_SPEC_BY_NAME = {spec.name: spec for spec in BENCHMARK_SPECS}
