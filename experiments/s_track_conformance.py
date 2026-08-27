#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import platform
import sys
from pathlib import Path

from mindmap.canonical.evaluate import evaluate_fixtures, summarize
from mindmap.canonical.fixtures import all_fixtures


def serialize(value):
    if isinstance(value, tuple):
        return "|".join(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def run(output_dir: Path) -> dict[str, object]:
    fixtures = all_fixtures()
    rows = evaluate_fixtures(fixtures)
    summary = summarize(rows)
    output_dir.mkdir(parents=True, exist_ok=True)

    with (output_dir / "s_track_conformance_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "fixture_id",
                "family",
                "query_id",
                "target_space",
                "invariant",
                "expected",
                "gold",
                "generic",
                "typed",
                "all_agree",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "fixture_id": row.fixture_id,
                    "family": row.family,
                    "query_id": row.query_id,
                    "target_space": row.target_space,
                    "invariant": row.invariant,
                    "expected": serialize(row.expected),
                    "gold": serialize(row.gold),
                    "generic": serialize(row.generic),
                    "typed": serialize(row.typed),
                    "all_agree": int(row.all_agree),
                }
            )

    manifest = {
        "study": "NCM-Psi v0.2 Track S semantic conformance",
        "interpretation": "fixed declarative conformance suite; no inferential statistics",
        "python": sys.version,
        "platform": platform.platform(),
        "fixtures": [fixture.fixture_id for fixture in fixtures],
        **summary,
    }
    (output_dir / "s_track_conformance_summary.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = run(root / "results")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["n_failures"]:
        raise SystemExit(1)
