from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from mindmap.repository_contract import (
    MANIFEST_NAME,
    load_release_manifest,
    validate_repository,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = load_release_manifest(REPOSITORY_ROOT)
README = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
PYPROJECT = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
LICENSE = (REPOSITORY_ROOT / "LICENSE").read_text(encoding="utf-8")


def test_current_repository_satisfies_release_contract() -> None:
    report = validate_repository(REPOSITORY_ROOT)
    assert report.ok, report.render()
    assert report.checked_paths == len(MANIFEST["required_paths"])
    assert report.checked_commands == len(MANIFEST["readme_commands"])
    assert report.checked_results == len(MANIFEST["result_entries"])


@pytest.mark.parametrize("required_path", MANIFEST["required_paths"])
def test_every_enumerated_required_path_is_fail_closed(required_path: str) -> None:
    mutated = deepcopy(MANIFEST)
    index = mutated["required_paths"].index(required_path)
    mutated["required_paths"][index] = f"__missing_contract_path__/{index}"
    report = validate_repository(REPOSITORY_ROOT, manifest_override=mutated)
    assert not report.ok
    assert f"missing release-contract path: __missing_contract_path__/{index}" in report.errors


@pytest.mark.parametrize("command", MANIFEST["readme_commands"])
def test_every_enumerated_readme_command_is_fail_closed(command: str) -> None:
    mutated = deepcopy(MANIFEST)
    index = mutated["readme_commands"].index(command)
    replacement = f"python __missing_release_command_{index}.py"
    mutated["readme_commands"][index] = replacement
    report = validate_repository(REPOSITORY_ROOT, manifest_override=mutated)
    assert not report.ok
    assert f"README is missing release-contract command: {replacement}" in report.errors


@pytest.mark.parametrize("statement", MANIFEST["readme_required_statements"])
def test_every_enumerated_status_statement_is_fail_closed(statement: str) -> None:
    mutated = deepcopy(MANIFEST)
    index = mutated["readme_required_statements"].index(statement)
    replacement = f"__missing_status_statement_{index}__"
    mutated["readme_required_statements"][index] = replacement
    report = validate_repository(REPOSITORY_ROOT, manifest_override=mutated)
    assert not report.ok
    assert f"README is missing release-contract status statement: {replacement}" in report.errors


@pytest.mark.parametrize("snippet", MANIFEST["readme_forbidden_snippets"])
def test_every_enumerated_stale_claim_is_fail_closed(snippet: str) -> None:
    report = validate_repository(
        REPOSITORY_ROOT,
        readme_text_override=README + "\n" + snippet + "\n",
    )
    assert not report.ok
    assert f"README contains forbidden stale/overbroad claim: {snippet}" in report.errors


def test_license_expression_mismatch_is_fail_closed() -> None:
    mutated = deepcopy(MANIFEST)
    mutated["package"]["license_expression"] = "Apache-2.0"
    report = validate_repository(REPOSITORY_ROOT, manifest_override=mutated)
    assert not report.ok
    assert any("license_expression" in error for error in report.errors)


def test_license_text_corruption_is_fail_closed() -> None:
    report = validate_repository(REPOSITORY_ROOT, license_text_override="MIT License\n")
    assert not report.ok
    assert any("LICENSE is missing required MIT text" in error for error in report.errors)


def test_python_range_mismatch_is_fail_closed() -> None:
    mutated = deepcopy(MANIFEST)
    mutated["python"]["requires_python"] = ">=3.12"
    report = validate_repository(REPOSITORY_ROOT, manifest_override=mutated)
    assert not report.ok
    assert any("requires-python must exactly match" in error for error in report.errors)


def test_pyproject_legacy_license_form_is_fail_closed() -> None:
    legacy = PYPROJECT.replace('license = "MIT"', 'license = {text = "MIT"}')
    report = validate_repository(REPOSITORY_ROOT, pyproject_text_override=legacy)
    assert not report.ok
    assert any("project.license must match" in error for error in report.errors)


@pytest.mark.parametrize("entry_index", range(len(MANIFEST["result_entries"])))
def test_every_result_entry_is_fail_closed(entry_index: int) -> None:
    mutated = deepcopy(MANIFEST)
    mutated["result_entries"][entry_index]["path"] = (
        f"results/__missing_release_result_{entry_index}.json"
    )
    report = validate_repository(REPOSITORY_ROOT, manifest_override=mutated)
    assert not report.ok
    assert (
        f"missing release-contract result: results/__missing_release_result_{entry_index}.json"
        in report.errors
    )


def test_current_stable_python_matrix_is_part_of_the_contract() -> None:
    assert MANIFEST["python"]["ci_versions"] == ["3.11", "3.12", "3.13", "3.14"]


def test_empty_directory_fails_closed_on_missing_manifest(tmp_path: Path) -> None:
    report = validate_repository(tmp_path)
    assert not report.ok
    assert report.checked_paths == 0
    assert any(MANIFEST_NAME in error for error in report.errors)


def test_non_directory_root_fails_closed(tmp_path: Path) -> None:
    file_root = tmp_path / "not-a-directory"
    file_root.write_text("x", encoding="utf-8")
    report = validate_repository(file_root)
    assert not report.ok
    assert report.checked_paths == 0
    assert report.errors == (f"repository root is not a directory: {file_root.resolve()}",)
