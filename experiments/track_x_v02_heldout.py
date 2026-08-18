#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from mindmap.track_x.v02_authorship import validate_authorship_note
from mindmap.track_x.v02_evaluate import evaluate_heldout


def _cell(value: object) -> object:
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
    fieldnames = list(materialized[0])
    path.parent.mkdir(parents=True, exist_ok=True)
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
                raise ValueError("held-out result column order changed")
            writer.writerow({key: _cell(value) for key, value in row.items()})


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(repository_root: Path, output_dir: Path) -> dict[str, object]:
    heldout_root = repository_root / "data" / "track_x_v02" / "heldout"
    declaration = validate_authorship_note(heldout_root / "AUTHORSHIP.md")
    verification_rows, downstream_rows, summary = evaluate_heldout(repository_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    verification_path = output_dir / "verification_rows.csv"
    _write_rows(verification_path, verification_rows)

    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in downstream_rows:
        grouped[str(row["treatment"])].append(row)
    downstream_paths: list[Path] = []
    for treatment, rows in sorted(grouped.items()):
        path = output_dir / f"downstream_{treatment}.csv"
        _write_rows(path, rows)
        downstream_paths.append(path)

    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    deterministic = (verification_path, *downstream_paths, summary_path)
    metadata = {
        "study": summary["study"],
        "interpretation": summary["interpretation"],
        "authorship": {
            "base_freeze_commit": declaration.base_freeze_commit,
            "heldout_branch": declaration.heldout_branch,
            "heldout_commit": declaration.heldout_commit,
            "changed_paths": list(declaration.changed_paths),
        },
        "python": sys.version,
        "platform": platform.platform(),
        "script_sha256": hashlib.sha256(
            Path(__file__).resolve().read_bytes()
        ).hexdigest(),
        "output_sha256": {path.name: _sha256(path) for path in deterministic},
        "deterministic_outputs": [path.name for path in deterministic],
    }
    (output_dir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the frozen Track X v0.2 evaluator on Session-A-authored "
            "held-out passages."
        )
    )
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/track_x_v02_heldout"),
    )
    args = parser.parse_args()
    summary = run(args.repository_root.resolve(), args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if summary["generic_typed_disagreements"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
