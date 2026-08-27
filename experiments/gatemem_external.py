#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
import importlib.metadata
import json
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
from mindmap.track_x.gatemem_reader import (
    DEFAULT_READER_MODEL_ID,
    DEFAULT_READER_MODEL_REVISION,
    ExtractiveReaderConfig,
    RawLexicalSharedReaderGateMemAgent,
    TransformersExtractiveReader,
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
        choices=(
            "raw_lexical",
            "raw_lexical_reader",
            "always_no_memory",
        ),
        required=True,
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--bm25-k1", type=float, default=1.2)
    parser.add_argument("--bm25-b", type=float, default=0.75)
    parser.add_argument("--recency-weight", type=float, default=0.0)
    parser.add_argument("--max-answer-characters", type=int, default=6000)
    parser.add_argument("--reader-model", default=DEFAULT_READER_MODEL_ID)
    parser.add_argument("--reader-revision", default=DEFAULT_READER_MODEL_REVISION)
    parser.add_argument("--reader-max-sequence-length", type=int, default=384)
    parser.add_argument("--reader-stride", type=int, default=128)
    parser.add_argument("--reader-max-answer-tokens", type=int, default=30)
    parser.add_argument("--reader-null-margin", type=float, default=0.0)
    parser.add_argument(
        "--expected-gatemem-commit",
        default=PINNED_GATEMEM_COMMIT,
    )
    parser.add_argument("--allow-dirty-checkout", action="store_true")
    parser.add_argument("--skip-official-scorer", action="store_true")
    parser.add_argument("--gate-by-action", action="store_true")
    parser.add_argument("--scorer-python", default=sys.executable)
    return parser.parse_args()


def _lexical_config(args: argparse.Namespace) -> RawLexicalConfig:
    return RawLexicalConfig(
        top_k=args.top_k,
        k1=args.bm25_k1,
        b=args.bm25_b,
        recency_weight=args.recency_weight,
        max_answer_characters=args.max_answer_characters,
    )


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _write_reader_runtime(
    output_dir: Path,
    *,
    config: ExtractiveReaderConfig,
    reader: TransformersExtractiveReader,
) -> str:
    payload = {
        "schema_version": "track-x-gatemem-b1b-reader-runtime-v0.1",
        "classification": (
            "aggregate reader cost/provenance only; no benchmark text or per-query answer"
        ),
        "config": asdict(config),
        "stats": reader.stats().to_json(),
        "packages": {
            "torch": _package_version("torch"),
            "transformers": _package_version("transformers"),
            "safetensors": _package_version("safetensors"),
        },
    }
    path = output_dir / "reader_runtime.json"
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return sha256(path.read_bytes()).hexdigest()


def main() -> int:
    args = parse_args()
    method_config: dict[str, Any]
    shared_reader: TransformersExtractiveReader | None = None
    reader_config: ExtractiveReaderConfig | None = None

    if args.method in {"raw_lexical", "raw_lexical_reader"}:
        lexical_config = _lexical_config(args)
        method_config = {
            "top_k": lexical_config.top_k,
            "k1": lexical_config.k1,
            "b": lexical_config.b,
            "recency_weight": lexical_config.recency_weight,
            "max_answer_characters": lexical_config.max_answer_characters,
        }
        if args.method == "raw_lexical":
            factory = lambda: RawLexicalGateMemAgent(lexical_config)
        else:
            reader_config = ExtractiveReaderConfig(
                model_id=args.reader_model,
                revision=args.reader_revision,
                max_sequence_length=args.reader_max_sequence_length,
                stride=args.reader_stride,
                max_answer_tokens=args.reader_max_answer_tokens,
                null_margin=args.reader_null_margin,
            )
            shared_reader = TransformersExtractiveReader(reader_config)
            method_config["reader"] = asdict(reader_config)
            factory = lambda: RawLexicalSharedReaderGateMemAgent(
                lexical_config,
                shared_reader,
            )
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

    reader_runtime_sha256: str | None = None
    if shared_reader is not None and reader_config is not None:
        reader_runtime_sha256 = _write_reader_runtime(
            result.output_dir,
            config=reader_config,
            reader=shared_reader,
        )

    print(f"output_dir={result.output_dir}")
    print(f"predictions={result.prediction_count}")
    print(f"gatemem_commit={result.checkout.observed_commit}")
    print(f"run_metadata_sha256={result.run_metadata_sha256}")
    if reader_runtime_sha256 is not None:
        print(f"reader_runtime_sha256={reader_runtime_sha256}")
    if result.official_score is not None:
        print(f"official_score_return_code={result.official_score.return_code}")
        print(f"official_summary_sha256={result.official_score.summary_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
