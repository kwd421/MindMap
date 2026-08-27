from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_research_records", ROOT / "tools" / "check_research_records.py"
)
CHECKER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(CHECKER)


def test_research_records_are_machine_checkable() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_research_records.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_fraction_mutation_is_rejected() -> None:
    errors = CHECKER.walk_fraction_pairs(
        {"metric": {"numerator": 4, "denominator": 3}}
    )
    assert any("0 <= numerator <= denominator" in error for error in errors)


def test_artifact_hash_mutation_is_rejected(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("real bytes", encoding="utf-8")
    errors = CHECKER.check_artifact_files(
        {
            "artifact_files": [
                {"path": "artifact.txt", "sha256": "0" * 64}
            ]
        },
        tmp_path,
    )
    assert any("artifact hash mismatch" in error for error in errors)


def test_schema_rejects_unadvertised_top_level_field() -> None:
    schema = json.loads(
        (ROOT / "docs" / "research" / "record.schema.json").read_text(
            encoding="utf-8"
        )
    )
    record = json.loads(
        (
            ROOT
            / "docs"
            / "research"
            / "records"
            / "EXP-20260828-006.json"
        ).read_text(encoding="utf-8")
    )
    record["unvalidated_claim"] = True
    errors = list(Draft202012Validator(schema).iter_errors(record))
    assert any("Additional properties are not allowed" in error.message for error in errors)


def test_dirty_source_without_reconstructability_is_rejected() -> None:
    record = json.loads(
        (
            ROOT
            / "docs"
            / "research"
            / "records"
            / "EXP-20260827-001.json"
        ).read_text(encoding="utf-8")
    )
    record["source"].pop("reconstructability")
    errors = CHECKER.check_source(record, ROOT)
    assert "dirty source requires source.reconstructability" in errors
