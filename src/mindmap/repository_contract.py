from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tomllib
from typing import Iterable


REQUIRED_PATHS: tuple[str, ...] = (
    "README.md",
    "LICENSE",
    "pyproject.toml",
    "PREREG_V0_2.md",
    "SCHEMA_V0_2.md",
    "docs/IMPLEMENTATION_STATUS.md",
    "src/mindmap/__init__.py",
    "src/mindmap/canonical/model.py",
    "src/mindmap/canonical/gold.py",
    "src/mindmap/canonical/generic.py",
    "src/mindmap/canonical/typed.py",
    "src/mindmap/track_x/v03_context_gate.py",
    "tests/test_canonical_conformance.py",
    "experiments/s_track_conformance.py",
    "experiments/track_x_v01.py",
    "experiments/track_x_v03_context_gate_p0.py",
    "results/s_track_conformance_summary.json",
    "results/track_x_v01/summary.json",
    "data/track_x_v02/FREEZE_V02.json",
    "data/track_x_v02/heldout/AUTHORSHIP_TEMPLATE.md",
)

README_COMMANDS: tuple[str, ...] = (
    "python -m pip install -e '.[dev]'",
    "python tools/check_repository_contract.py",
    "python -m pytest -q",
    "python experiments/s_track_conformance.py",
    "python experiments/track_x_v01.py --output-dir /tmp/track_x_v01",
    (
        "python experiments/track_x_v03_context_gate_p0.py "
        "--output-dir /tmp/track_x_v03_context_gate"
    ),
)

README_REQUIRED_STATEMENTS: tuple[str, ...] = (
    "world truth ≠ a principal's belief ≠ first-person memory ≠ current disclosure permission",
    "This branch is an **installable deterministic research prototype**.",
    "There is no active `benchmarks/` directory in this runnable core.",
    "CI executes the commands advertised in this README.",
    "docs/IMPLEMENTATION_STATUS.md",
)

README_FORBIDDEN_STALE_SNIPPETS: tuple[str, ...] = (
    "- `benchmarks/` — public benchmark adapters",
    "python experiments/epistemic_branch_pilot.py\npython experiments/extraction_noise_pilot.py",
)

RESULT_FILES: tuple[str, ...] = (
    "results/s_track_conformance_summary.json",
    "results/track_x_v01/summary.json",
)


@dataclass(frozen=True, slots=True)
class ContractReport:
    root: Path
    checked_paths: int
    checked_commands: int
    checked_results: int
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors

    def render(self) -> str:
        lines = [
            "MindMap repository contract",
            f"root={self.root}",
            f"checked_paths={self.checked_paths}",
            f"checked_commands={self.checked_commands}",
            f"checked_results={self.checked_results}",
            f"ok={str(self.ok).lower()}",
        ]
        if self.errors:
            lines.append("errors:")
            lines.extend(f"  - {error}" for error in self.errors)
        return "\n".join(lines)


def _missing_paths(root: Path, paths: Iterable[str]) -> list[str]:
    return [path for path in paths if not (root / path).exists()]


def _read_text(path: Path, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"cannot read UTF-8 file {path}: {type(exc).__name__}: {exc}")
        return ""


def _validate_license(root: Path, errors: list[str]) -> None:
    path = root / "LICENSE"
    if not path.is_file():
        return
    text = _read_text(path, errors)
    required = (
        "MIT License",
        "Permission is hereby granted, free of charge",
        'THE SOFTWARE IS PROVIDED "AS IS"',
    )
    for snippet in required:
        if snippet not in text:
            errors.append(f"LICENSE is missing required MIT text: {snippet}")


def _validate_pyproject(root: Path, errors: list[str]) -> None:
    path = root / "pyproject.toml"
    if not path.is_file():
        return
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        errors.append(f"invalid pyproject.toml: {type(exc).__name__}: {exc}")
        return

    project = payload.get("project")
    if not isinstance(project, dict):
        errors.append("pyproject.toml lacks [project]")
        return
    if project.get("name") != "mindmap-ncm":
        errors.append("pyproject project.name must be 'mindmap-ncm'")
    if project.get("license") != {"text": "MIT"}:
        errors.append("pyproject project.license must match the checked-in MIT LICENSE")
    requires_python = project.get("requires-python")
    if not isinstance(requires_python, str) or ">=3.11" not in requires_python:
        errors.append("pyproject requires-python must include >=3.11")

    optional = project.get("optional-dependencies")
    if not isinstance(optional, dict) or "dev" not in optional:
        errors.append("pyproject must define project.optional-dependencies.dev")

    setuptools = payload.get("tool", {}).get("setuptools", {})
    if not isinstance(setuptools, dict) or setuptools.get("package-dir") != {"": "src"}:
        errors.append("pyproject must configure setuptools package-dir = {'': 'src'}")


def _validate_readme(root: Path, errors: list[str]) -> None:
    readme_path = root / "README.md"
    if not readme_path.is_file():
        return
    readme = _read_text(readme_path, errors)
    if not readme:
        return

    for command in README_COMMANDS:
        if command not in readme:
            errors.append(f"README is missing advertised verified command: {command}")
    for statement in README_REQUIRED_STATEMENTS:
        if statement not in readme:
            errors.append(f"README is missing required status statement: {statement}")
    for snippet in README_FORBIDDEN_STALE_SNIPPETS:
        if snippet in readme:
            errors.append(f"README retains stale repository claim: {snippet}")


def _validate_results(root: Path, errors: list[str]) -> int:
    checked = 0
    for relative in RESULT_FILES:
        path = root / relative
        if not path.is_file():
            continue
        checked += 1
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON result {relative}: {type(exc).__name__}: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"result must be a JSON object: {relative}")
    return checked


def validate_repository(root: Path) -> ContractReport:
    root = root.resolve()
    errors: list[str] = []

    if not root.is_dir():
        errors.append(f"repository root is not a directory: {root}")
        return ContractReport(root, 0, 0, 0, tuple(errors))

    missing = _missing_paths(root, REQUIRED_PATHS)
    errors.extend(f"missing required path: {path}" for path in missing)

    _validate_license(root, errors)
    _validate_pyproject(root, errors)
    _validate_readme(root, errors)
    result_count = _validate_results(root, errors)

    tests = root / "tests"
    if tests.is_dir() and not any(tests.glob("test_*.py")):
        errors.append("tests/ contains no test_*.py files")

    package = root / "src" / "mindmap"
    if package.is_dir() and not any(package.rglob("*.py")):
        errors.append("src/mindmap contains no Python modules")

    return ContractReport(
        root=root,
        checked_paths=len(REQUIRED_PATHS),
        checked_commands=len(README_COMMANDS),
        checked_results=result_count,
        errors=tuple(errors),
    )


def main() -> int:
    repository_root = Path(__file__).resolve().parents[2]
    report = validate_repository(repository_root)
    print(report.render())
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
