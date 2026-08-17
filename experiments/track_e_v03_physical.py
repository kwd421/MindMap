from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import sys
from pathlib import Path

from mindmap.track_e.physical_evaluate import evaluate_physical_suite
from mindmap.track_e.physical_fixtures import all_physical_cases


def _normalize(value):
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    return value


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [_normalize(row) for row in rows]
    fieldnames = list(normalized[0]) if normalized else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in normalized:
            writer.writerow(
                {
                    key: json.dumps(value, sort_keys=True, ensure_ascii=False)
                    if isinstance(value, (dict, list))
                    else value
                    for key, value in row.items()
                }
            )


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_normalize(value), sort_keys=True, indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/track_e_v03_physical"),
    )
    args = parser.parse_args()

    cases = all_physical_cases()
    rows, summary = evaluate_physical_suite(cases)
    summary = {
        **summary,
        "n_fault_archetypes": sum(not case.clean_control for case in cases),
        "n_identifiable_fault_archetypes": sum(
            not case.clean_control and case.identifiable for case in cases
        ),
        "n_non_identifiable_fault_archetypes": sum(
            not case.clean_control and not case.identifiable for case in cases
        ),
        "n_clean_controls": sum(case.clean_control for case in cases),
    }

    rows_path = args.output_dir / "rows.csv"
    summary_path = args.output_dir / "summary.json"
    _write_csv(rows_path, rows)
    _write_json(summary_path, summary)
    metadata = {
        "study": summary["study"],
        "interpretation": summary["interpretation"],
        "python": sys.version,
        "platform": platform.platform(),
        "github_sha": os.environ.get("GITHUB_SHA"),
        "rows_sha256": _sha256(rows_path),
        "summary_sha256": _sha256(summary_path),
    }
    _write_json(args.output_dir / "run_metadata.json", metadata)

    failures: list[str] = []
    for implementation, values in summary["implementations"].items():
        if values["identifiable_detection_recall"] != 1.0:
            failures.append(f"{implementation}: identifiable detection != 1")
        if values["clean_false_alarm_rate"] != 0.0:
            failures.append(f"{implementation}: clean false alarm != 0")
        if values["silent_incorrect_use_rate_identifiable"] != 0.0:
            failures.append(f"{implementation}: identifiable silent use != 0")
        if values["repair_success_rate"] != 1.0:
            failures.append(f"{implementation}: repair success != 1")
        if values["total_residue_after_repair"] != 0:
            failures.append(f"{implementation}: repair residue != 0")
    if summary["outcome_disagreements"]:
        failures.append("generic/typed physical outcomes disagree")

    print(json.dumps(_normalize(summary), sort_keys=True, indent=2))
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
