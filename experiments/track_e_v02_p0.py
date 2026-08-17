from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import sys
from pathlib import Path

from mindmap.track_e.evaluate import evaluate_suite
from mindmap.track_e.fixtures import all_fault_cases


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/track_e_v02_p0"),
    )
    args = parser.parse_args()

    cases = all_fault_cases()
    rows, summary = evaluate_suite(cases)
    summary = {
        **summary,
        "n_fault_archetypes": sum(not case.clean_control for case in cases),
        "n_identifiable_fault_archetypes": sum(
            not case.clean_control and case.identifiable for case in cases
        ),
        "n_non_identifiable_archetypes": sum(
            not case.clean_control and not case.identifiable for case in cases
        ),
        "n_clean_controls": sum(case.clean_control for case in cases),
        "case_ids": [case.case_id for case in cases],
        "required_surface_counts": {
            surface.name: sum(case.required_surface is surface for case in cases)
            for surface in sorted(
                {case.required_surface for case in cases}, key=int
            )
        },
    }

    rows_path = args.output_dir / "rows.csv"
    summary_path = args.output_dir / "summary.json"
    _write_csv(rows_path, rows)
    _write_json(summary_path, summary)

    metadata = {
        "study": summary["study"],
        "python": sys.version,
        "platform": platform.platform(),
        "github_sha": os.environ.get("GITHUB_SHA"),
        "rows_sha256": _sha256(rows_path),
        "summary_sha256": _sha256(summary_path),
        "deterministic_outputs": [rows_path.name, summary_path.name],
        "interpretation": summary["interpretation"],
    }
    _write_json(args.output_dir / "run_metadata.json", metadata)

    failures: list[str] = []
    for observer, values in summary["observers"].items():
        if values["identifiable_detection_recall"] != 1.0:
            failures.append(f"{observer}: identifiable recall != 1")
        if values["clean_false_alarm_rate"] != 0.0:
            failures.append(f"{observer}: clean false alarm != 0")
        if values["non_identifiable_detected"] != 0:
            failures.append(f"{observer}: non-identifiable case alerted")
    if summary["outcome_disagreements"]:
        failures.append("generic/typed detection-containment outcomes disagree")

    print(json.dumps(summary, sort_keys=True, indent=2))
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
