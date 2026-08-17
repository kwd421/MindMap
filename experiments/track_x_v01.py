#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from pathlib import Path
from typing import Iterable

from mindmap.track_x.evaluate import evaluate_raw_verifier_suite
from mindmap.track_x.fixtures import all_raw_verifier_cases
from mindmap.track_x.manifest import FROZEN_MANIFEST_VERSION


def _normalize_cell(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, float):
        return format(value, ".17g")
    if isinstance(value, (tuple, list, set, frozenset)):
        return "|".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return value


def _write_rows(path: Path, rows: Iterable[dict[str, object]]) -> None:
    materialized = list(rows)
    if not materialized:
        raise ValueError(f"cannot write empty result table: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(materialized[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        for row in materialized:
            if list(row) != fieldnames:
                raise ValueError("result rows must have one deterministic column order")
            writer.writerow({key: _normalize_cell(value) for key, value in row.items()})


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(output_dir: Path) -> dict[str, object]:
    cases = all_raw_verifier_cases()
    verification_rows, downstream_rows, summary = evaluate_raw_verifier_suite(cases)
    output_dir.mkdir(parents=True, exist_ok=True)

    verification_path = output_dir / "verification_rows.csv"
    downstream_path = output_dir / "downstream_rows.csv"
    summary_path = output_dir / "summary.json"
    metadata_path = output_dir / "run_metadata.json"

    _write_rows(verification_path, verification_rows)
    _write_rows(downstream_path, downstream_rows)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    script_path = Path(__file__).resolve()
    metadata = {
        "study": summary["study"],
        "manifest_version": FROZEN_MANIFEST_VERSION,
        "interpretation": summary["interpretation"],
        "python": sys.version,
        "platform": platform.platform(),
        "script_sha256": hashlib.sha256(script_path.read_bytes()).hexdigest(),
        "verification_rows_sha256": _sha256(verification_path),
        "downstream_rows_sha256": _sha256(downstream_path),
        "summary_sha256": _sha256(summary_path),
        "deterministic_outputs": [
            verification_path.name,
            downstream_path.name,
            summary_path.name,
        ],
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the fixed Track X v0.1 leakage-free raw-verifier P0."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/track_x_v01"),
        help="directory for deterministic rows, summary, and run metadata",
    )
    args = parser.parse_args()
    summary = run(args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))

    overall = summary["verification"]["overall"]
    heldout = summary["verification"]["by_split"]["heldout"]
    if overall["clean_false_correction_rate"] != 0.0:
        return 1
    if overall["corrupted_false_accept_rate"] != 0.0:
        return 1
    if heldout["selective_risk"] != 0.0:
        return 1
    if summary["generic_typed_disagreements"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
