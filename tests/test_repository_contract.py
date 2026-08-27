from __future__ import annotations

from pathlib import Path

from mindmap.repository_contract import REQUIRED_PATHS, validate_repository


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_current_repository_satisfies_advertised_contract() -> None:
    report = validate_repository(REPOSITORY_ROOT)
    assert report.ok, report.render()
    assert report.checked_paths == len(REQUIRED_PATHS)
    assert report.checked_commands >= 6
    assert report.checked_results == 2


def test_empty_directory_fails_closed_with_missing_paths(tmp_path: Path) -> None:
    report = validate_repository(tmp_path)
    assert not report.ok
    assert any(error.startswith("missing required path:") for error in report.errors)
    assert "missing required path: README.md" in report.errors
    assert "missing required path: pyproject.toml" in report.errors


def test_non_directory_root_fails_closed(tmp_path: Path) -> None:
    file_root = tmp_path / "not-a-directory"
    file_root.write_text("x", encoding="utf-8")
    report = validate_repository(file_root)
    assert not report.ok
    assert report.checked_paths == 0
    assert report.errors == (f"repository root is not a directory: {file_root.resolve()}",)
