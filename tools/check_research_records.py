from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"^EXP-[0-9]{8}-[0-9]{3}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=root, check=False, capture_output=True, text=True
    )


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def walk_fraction_pairs(value: Any, location: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        if "numerator" in value or "denominator" in value:
            numerator = value.get("numerator")
            denominator = value.get("denominator")
            if not isinstance(numerator, int) or isinstance(numerator, bool):
                errors.append(f"{location}.numerator must be an integer")
            if not isinstance(denominator, int) or isinstance(denominator, bool):
                errors.append(f"{location}.denominator must be an integer")
            if isinstance(denominator, int) and denominator <= 0:
                errors.append(f"{location}.denominator must be positive")
            if (
                isinstance(numerator, int)
                and isinstance(denominator, int)
                and (numerator < 0 or numerator > denominator)
            ):
                errors.append(f"{location} must satisfy 0 <= numerator <= denominator")
        for key, child in value.items():
            errors.extend(walk_fraction_pairs(child, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(walk_fraction_pairs(child, f"{location}[{index}]"))
    return errors


def check_artifact_files(record: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    for artifact in record.get("artifact_files", []):
        relative = Path(artifact["path"])
        if relative.is_absolute() or ".." in relative.parts:
            errors.append(f"artifact path must be repository-relative: {relative}")
            continue
        path = root / relative
        if not path.is_file():
            errors.append(f"artifact does not exist: {relative}")
            continue
        actual = sha256_file(path)
        if actual != artifact["sha256"]:
            errors.append(
                f"artifact hash mismatch for {relative}: expected "
                f"{artifact['sha256']}, got {actual}"
            )
    return errors


def check_source(record: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    source = record["source"]
    for key in ("source_revision", "checkout_revision"):
        revision = source[key]
        if not SHA_RE.fullmatch(revision):
            continue
        exists = git(root, "cat-file", "-e", f"{revision}^{{commit}}")
        if exists.returncode != 0:
            errors.append(f"source.{key} is not a local git commit: {revision}")

    if source["dirty"]:
        reconstruction = source.get("reconstructability")
        if reconstruction is None:
            errors.append("dirty source requires source.reconstructability")
        elif reconstruction["status"] == "reconstructable":
            patch_path = reconstruction.get("patch_path")
            patch_sha = reconstruction.get("patch_sha256")
            if not patch_path or not patch_sha:
                errors.append("reconstructable dirty source requires patch_path and patch_sha256")
            else:
                errors.extend(
                    check_artifact_files(
                        {"artifact_files": [{"path": patch_path, "sha256": patch_sha}]},
                        root,
                    )
                )
        elif "unreconstructable" not in record["claim_boundary"].lower():
            errors.append(
                "unreconstructable dirty source must be explicit in claim_boundary"
            )
    return errors


def check_timing(record: dict[str, Any], root: Path, relative_path: Path) -> list[str]:
    errors: list[str] = []
    started_at = record["started_at"]
    ended_at = record["ended_at"]
    if started_at is None or ended_at is None:
        timing = record.get("timing")
        if not timing or timing.get("precision") not in {"day", "unknown"}:
            errors.append("null execution timestamp requires timing.precision day/unknown")
    else:
        start = parse_datetime(started_at)
        end = parse_datetime(ended_at)
        if end < start:
            errors.append("ended_at precedes started_at")

    prereg = record.get("preregistration_commit")
    if prereg is None:
        if record["study_class"] in {"confirmatory", "reproduction"}:
            errors.append(
                f"{record['study_class']} record requires preregistration_commit"
            )
        return errors

    if git(root, "cat-file", "-e", f"{prereg}^{{commit}}").returncode != 0:
        errors.append(f"preregistration_commit is not a local git commit: {prereg}")
        return errors
    source_revision = record["source"]["source_revision"]
    if git(root, "merge-base", "--is-ancestor", source_revision, prereg).returncode != 0:
        errors.append("source_revision must be an ancestor of preregistration_commit")
    frozen = git(root, "show", f"{prereg}:{relative_path.as_posix()}")
    if frozen.returncode != 0:
        errors.append("record was absent from preregistration_commit")
    else:
        try:
            frozen_record = json.loads(frozen.stdout)
        except json.JSONDecodeError:
            errors.append("record at preregistration_commit is invalid JSON")
        else:
            comparisons = [
                ("study_class", record["study_class"], frozen_record.get("study_class")),
                ("method_arms", record["method_arms"], frozen_record.get("method_arms")),
                ("models", record["models"], frozen_record.get("models")),
                ("controls", record["controls"], frozen_record.get("controls")),
                ("sample", record["sample"], frozen_record.get("sample")),
                (
                    "primary_outcome",
                    record["results"].get("primary_outcome"),
                    frozen_record.get("results", {}).get("primary_outcome"),
                ),
                (
                    "stopping_rule",
                    record["results"].get("stopping_rule"),
                    frozen_record.get("results", {}).get("stopping_rule"),
                ),
            ]
            for label, current, original in comparisons:
                if current != original:
                    errors.append(f"preregistered field changed after freeze: {label}")

    if started_at is not None:
        commit_time_result = git(root, "show", "-s", "--format=%cI", prereg)
        if commit_time_result.returncode == 0:
            commit_time = parse_datetime(commit_time_result.stdout.strip())
            if commit_time > parse_datetime(started_at):
                errors.append("preregistration commit time is after run start")
    return errors


def check_record(
    path: Path, root: Path, validator: Draft202012Validator
) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"unreadable JSON: {exc}"]

    for error in sorted(validator.iter_errors(record), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        errors.append(f"schema {location}: {error.message}")

    experiment_id = record.get("experiment_id", "")
    if path.stem != experiment_id:
        errors.append("filename must equal experiment_id")
    if errors:
        return record, errors

    errors.extend(walk_fraction_pairs(record))
    errors.extend(check_artifact_files(record, root))
    errors.extend(check_source(record, root))
    errors.extend(check_timing(record, root, path.relative_to(root)))
    return record, errors


def check_cost_ledger(records: dict[str, dict[str, Any]], root: Path) -> list[str]:
    errors: list[str] = []
    ledger_path = root / "docs" / "research" / "COST_LEDGER.csv"
    with ledger_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    by_id: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_id.setdefault(row["experiment_id"], []).append(row)
    for experiment_id, record in records.items():
        matches = by_id.get(experiment_id, [])
        if len(matches) != 1:
            errors.append(f"cost ledger must contain exactly one row for {experiment_id}")
            continue
        try:
            estimated = float(matches[0]["estimated_usd"])
        except ValueError:
            errors.append(f"cost ledger estimated_usd is not numeric for {experiment_id}")
            continue
        if abs(estimated - float(record["cost"]["provider_usd"])) > 0.0000005:
            errors.append(f"cost ledger does not reconcile for {experiment_id}")
    unknown = sorted(set(by_id) - set(records))
    if unknown:
        errors.append(f"cost ledger has unknown experiment IDs: {', '.join(unknown)}")
    return errors


def check_markdown_references(records: dict[str, dict[str, Any]], root: Path) -> list[str]:
    errors: list[str] = []
    known = set(records)
    claim_text = (root / "docs" / "research" / "CLAIM_EVIDENCE_LEDGER.md").read_text(
        encoding="utf-8"
    )
    referenced = set(re.findall(r"EXP-[0-9]{8}-[0-9]{3}", claim_text))
    missing = sorted(referenced - known)
    if missing:
        errors.append(f"claim ledger references missing records: {', '.join(missing)}")

    experiment_text = (root / "docs" / "research" / "EXPERIMENT_LEDGER.md").read_text(
        encoding="utf-8"
    )
    headings = set(re.findall(r"^## (EXP-[0-9]{8}-[0-9]{3})\b", experiment_text, re.M))
    if headings != known:
        errors.append(
            "experiment ledger headings differ from record IDs: "
            f"missing={sorted(known - headings)}, extra={sorted(headings - known)}"
        )
    return errors


def run(root: Path) -> list[str]:
    records_dir = root / "docs" / "research" / "records"
    schema_path = root / "docs" / "research" / "record.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    paths = sorted(records_dir.glob("EXP-*.json"))
    errors: list[str] = []
    records: dict[str, dict[str, Any]] = {}
    for path in paths:
        record, record_errors = check_record(path, root, validator)
        if record is not None and ID_RE.fullmatch(record.get("experiment_id", "")):
            experiment_id = record["experiment_id"]
            if experiment_id in records:
                errors.append(f"duplicate experiment ID: {experiment_id}")
            records[experiment_id] = record
        errors.extend(f"{path.relative_to(root)}: {error}" for error in record_errors)
    if not paths:
        errors.append(f"no experiment records found in {records_dir}")
    if records:
        errors.extend(check_cost_ledger(records, root))
        errors.extend(check_markdown_references(records, root))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    errors = run(root)
    if errors:
        print("research record validation failed")
        for error in errors:
            print(f"- {error}")
        return 1
    count = len(list((root / "docs" / "research" / "records").glob("EXP-*.json")))
    print(f"research record validation passed: {count} record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
