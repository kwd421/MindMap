from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "docs" / "research" / "records"
ID_RE = re.compile(r"^EXP-[0-9]{8}-[0-9]{3}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REQUIRED = {
    "schema_version",
    "experiment_id",
    "title",
    "status",
    "study_class",
    "research_question_ids",
    "hypothesis_ids",
    "started_at",
    "ended_at",
    "source",
    "dataset",
    "method_arms",
    "models",
    "controls",
    "sample",
    "results",
    "cost",
    "claim_boundary",
}
STUDY_CLASSES = {
    "smoke",
    "development",
    "pilot",
    "confirmatory",
    "reproduction",
    "replication",
}


def check_record(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path}: unreadable JSON: {exc}"]

    missing = sorted(REQUIRED - set(record))
    if missing:
        errors.append(f"{path}: missing keys: {', '.join(missing)}")

    experiment_id = record.get("experiment_id", "")
    if not ID_RE.fullmatch(experiment_id):
        errors.append(f"{path}: invalid experiment_id {experiment_id!r}")
    if path.stem != experiment_id:
        errors.append(f"{path}: filename must equal experiment_id")
    if record.get("study_class") not in STUDY_CLASSES:
        errors.append(f"{path}: invalid study_class")

    source = record.get("source", {})
    for key in ("repository", "source_revision", "checkout_revision", "dirty", "deviations"):
        if key not in source:
            errors.append(f"{path}: source.{key} is required")
    for key in ("source_revision", "checkout_revision"):
        value = source.get(key, "")
        if not SHA_RE.fullmatch(value):
            errors.append(f"{path}: source.{key} must be a 40-character lowercase git SHA")

    cost = record.get("cost", {})
    if not isinstance(cost.get("provider_usd"), (int, float)):
        errors.append(f"{path}: cost.provider_usd must be numeric")
    if not str(record.get("claim_boundary", "")).strip():
        errors.append(f"{path}: claim_boundary must be non-empty")
    return errors


def main() -> int:
    paths = sorted(RECORDS.glob("EXP-*.json"))
    errors: list[str] = []
    seen: set[str] = set()
    for path in paths:
        errors.extend(check_record(path))
        experiment_id = path.stem
        if experiment_id in seen:
            errors.append(f"duplicate experiment ID: {experiment_id}")
        seen.add(experiment_id)

    if not paths:
        errors.append(f"no experiment records found in {RECORDS}")
    if errors:
        print("research record validation failed")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"research record validation passed: {len(paths)} record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
