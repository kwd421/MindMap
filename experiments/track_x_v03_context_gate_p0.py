#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from mindmap.track_x.v03_context_gate import (
    ContextGateRow,
    evaluate_development_context_gate,
)


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _write_json(path: Path, value: Any) -> str:
    data = _canonical_json_bytes(value)
    path.write_bytes(data)
    return sha256(data).hexdigest()


def _write_csv(path: Path, rows: Iterable[Mapping[str, object]]) -> str:
    materialized = [dict(row) for row in rows]
    if not materialized:
        raise ValueError("cannot write an empty context-gate result table")
    fieldnames = list(materialized[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(materialized)
    return sha256(path.read_bytes()).hexdigest()


def run(*, repository_root: Path, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows, summary = evaluate_development_context_gate(repository_root)

    row_dicts = [row.to_dict() for row in rows]
    rows_hash = _write_csv(output_dir / "rows.csv", row_dicts)
    summary_hash = _write_json(output_dir / "summary.json", summary)

    metadata = {
        "schema_version": "track-x-v0.3-context-gate-run-v0.1",
        "classification": (
            "fixed deterministic development-only mechanism audit; "
            "no held-out or public-benchmark claim"
        ),
        "repository_root": str(repository_root.resolve()),
        "development_bundle": (
            "data/track_x_v02/development/session_b.json"
        ),
        "heldout_read": False,
        "base_freeze_commit": "b7faf750df7f9db018b97ec224b0c83142c4efe4",
        "row_count": len(rows),
        "artifact_sha256": {
            "rows.csv": rows_hash,
            "summary.json": summary_hash,
        },
    }
    metadata_hash = _write_json(output_dir / "run_metadata.json", metadata)
    metadata["artifact_sha256"]["run_metadata.json"] = metadata_hash
    # Re-write after inserting its first-pass content hash. The external file
    # hash remains the filesystem digest printed by the CLI, while the embedded
    # value commits to the metadata fields before self-reference.
    _write_json(output_dir / "run_metadata.json", metadata)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Track X v0.3 development-only candidate/context/answer "
            "surface audit."
        )
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run(
        repository_root=args.repository_root,
        output_dir=args.output_dir,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
