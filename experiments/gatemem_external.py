#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

from mindmap.track_x.gatemem_baselines import (
    AlwaysNoMemoryGateMemAgent,
    RawLexicalConfig,
    RawLexicalGateMemAgent,
)
from mindmap.track_x.gatemem_official import (
    PINNED_GATEMEM_COMMIT,
    git_revision,
    run_external_gatemem,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a protected Track X baseline on a pinned local GateMem checkout. "
            "No benchmark data are copied into the MindMap repository."
        )
    )
    parser.add_argument("--gatemem-checkout", type=Path, required=True)
    parser.add_argument(
        "--domain",
        choices=("medical", "education", "household", "office"),
        required=True,
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--method",
        choices=("raw_lexical", "always_no_memory"),
        required=True,
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--bm25-k1", type=float, default=1.2)
    parser.add_argument("--bm25-b", type=float, default=0.75)
    parser.add_argument("--recency-weight", type=float, default=0.0)
    parser.add_argument("--max-answer-characters", type=int, default=6000)
    parser.add_argument(
        "--expected-gatemem-commit",
        default=PINNED_GATEMEM_COMMIT,
    )
    parser.add_argument("--allow-dirty-checkout", action="store_true")
    parser.add_argument("--skip-official-scorer", action="store_true")
    parser.add_argument("--gate-by-action", action="store_true")
    parser.add_argument("--scorer-python", default=sys.executable)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    method_config: dict[str, Any]

    if args.method == "raw_lexical":
        config = RawLexicalConfig(
            top_k=args.top_k,
            k1=args.bm25_k1,
            b=args.bm25_b,
            recency_weight=args.recency_weight,
            max_answer_characters=args.max_answer_characters,
        )
        method_config = {
            "top_k": config.top_k,
            "k1": config.k1,
            "b": config.b,
            "recency_weight": config.recency_weight,
            "max_answer_characters": config.max_answer_characters,
        }
        factory = lambda: RawLexicalGateMemAgent(config)
    else:
        method_config = {}
        factory = AlwaysNoMemoryGateMemAgent

    repo_root = Path(__file__).resolve().parents[1]
    try:
        repository_revision = git_revision(repo_root)
    except Exception:
        repository_revision = None

    result = run_external_gatemem(
        checkout=args.gatemem_checkout,
        domain=args.domain,
        output_dir=args.output_dir,
        agent_factory=factory,
        method_name=args.method,
        method_config=method_config,
        expected_commit=args.expected_gatemem_commit,
        require_clean_checkout=not args.allow_dirty_checkout,
        invoke_official_scorer=not args.skip_official_scorer,
        scorer_python=args.scorer_python,
        gate_by_action=args.gate_by_action,
        repository_revision=repository_revision,
    )

    print(f"output_dir={result.output_dir}")
    print(f"predictions={result.prediction_count}")
    print(f"gatemem_commit={result.checkout.observed_commit}")
    print(f"run_metadata_sha256={result.run_metadata_sha256}")
    if result.official_score is not None:
        print(f"official_score_return_code={result.official_score.return_code}")
        print(f"official_summary_sha256={result.official_score.summary_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
