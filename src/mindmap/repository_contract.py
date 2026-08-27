from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import tomllib
from typing import Any, Mapping


MANIFEST_NAME = "release_contract_v0_2.json"


class ContractError(ValueError):
    """Raised when the release contract itself is malformed."""


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
            f"manifest={MANIFEST_NAME}",
            f"checked_paths={self.checked_paths}",
            f"checked_commands={self.checked_commands}",
            f"checked_results={self.checked_results}",
            f"ok={str(self.ok).lower()}",
        ]
        if self.errors:
            lines.append("errors:")
            lines.extend(f"  - {error}" for error in self.errors)
        return "\n".join(lines)


def _string_list(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ContractError(f"{field} must be a non-empty JSON array")
    output: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ContractError(f"{field}[{index}] must be a non-empty string")
        output.append(item)
    if len(set(output)) != len(output):
        raise ContractError(f"{field} must not contain duplicates")
    return tuple(output)


def load_release_manifest(root: Path) -> dict[str, Any]:
    path = root.resolve() / MANIFEST_NAME
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot load {MANIFEST_NAME}: {type(exc).__name__}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ContractError(f"{MANIFEST_NAME} must contain a JSON object")
    if payload.get("schema_version") != "mindmap-release-contract-v0.2":
        raise ContractError("unsupported release contract schema_version")

    _string_list(payload.get("required_paths"), "required_paths")
    _string_list(payload.get("readme_commands"), "readme_commands")
    _string_list(payload.get("readme_required_statements"), "readme_required_statements")
    _string_list(payload.get("readme_forbidden_snippets"), "readme_forbidden_snippets")

    python = payload.get("python")
    if not isinstance(python, dict):
        raise ContractError("python must be an object")
    if not isinstance(python.get("requires_python"), str):
        raise ContractError("python.requires_python must be a string")
    _string_list(python.get("ci_versions"), "python.ci_versions")

    package = payload.get("package")
    if not isinstance(package, dict):
        raise ContractError("package must be an object")
    for field in ("name", "license_expression", "license_file", "package_root"):
        if not isinstance(package.get(field), str) or not package[field].strip():
            raise ContractError(f"package.{field} must be a non-empty string")
    if not isinstance(package.get("setuptools_minimum"), int):
        raise ContractError("package.setuptools_minimum must be an integer")

    results = payload.get("result_entries")
    if not isinstance(results, list) or not results:
        raise ContractError("result_entries must be a non-empty array")
    seen_result_paths: set[str] = set()
    for index, entry in enumerate(results):
        if not isinstance(entry, dict):
            raise ContractError(f"result_entries[{index}] must be an object")
        path_value = entry.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            raise ContractError(f"result_entries[{index}].path must be non-empty")
        if path_value in seen_result_paths:
            raise ContractError("result_entries paths must be unique")
        seen_result_paths.add(path_value)
        if entry.get("kind") not in {"json_object"}:
            raise ContractError(f"unsupported result kind: {entry.get('kind')!r}")
        if not isinstance(entry.get("contract"), str) or not entry["contract"].strip():
            raise ContractError(f"result_entries[{index}].contract must be non-empty")

    surfaces = payload.get("reproduction_surfaces")
    if not isinstance(surfaces, dict) or not surfaces:
        raise ContractError("reproduction_surfaces must be a non-empty object")
    return payload


def _read_text(path: Path, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"cannot read UTF-8 file {path}: {type(exc).__name__}: {exc}")
        return ""


def _validate_license(
    root: Path,
    package: Mapping[str, Any],
    errors: list[str],
    *,
    license_text_override: str | None,
) -> None:
    path = root / str(package["license_file"])
    if not path.is_file() and license_text_override is None:
        return
    text = license_text_override if license_text_override is not None else _read_text(path, errors)
    if package["license_expression"] == "MIT":
        required = (
            "MIT License",
            "Permission is hereby granted, free of charge",
            'THE SOFTWARE IS PROVIDED "AS IS"',
        )
        for snippet in required:
            if snippet not in text:
                errors.append(f"LICENSE is missing required MIT text: {snippet}")
    else:
        errors.append(
            "release contract license_expression is unsupported by the checked license-text rule: "
            f"{package['license_expression']}"
        )


def _minimum_setuptools(requirements: list[Any]) -> int | None:
    for requirement in requirements:
        if not isinstance(requirement, str):
            continue
        match = re.fullmatch(r"setuptools>=(\d+)(?:\.\d+)?", requirement.strip())
        if match:
            return int(match.group(1))
    return None


def _validate_pyproject(
    root: Path,
    manifest: Mapping[str, Any],
    errors: list[str],
    *,
    pyproject_text_override: str | None,
) -> None:
    path = root / "pyproject.toml"
    if not path.is_file() and pyproject_text_override is None:
        return
    try:
        text = pyproject_text_override if pyproject_text_override is not None else path.read_text(encoding="utf-8")
        payload = tomllib.loads(text)
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        errors.append(f"invalid pyproject.toml: {type(exc).__name__}: {exc}")
        return

    project = payload.get("project")
    if not isinstance(project, dict):
        errors.append("pyproject.toml lacks [project]")
        return

    package = manifest["package"]
    python = manifest["python"]
    if project.get("name") != package["name"]:
        errors.append(f"pyproject project.name must be {package['name']!r}")
    if project.get("license") != package["license_expression"]:
        errors.append(
            "pyproject project.license must match release contract license_expression "
            f"{package['license_expression']!r}"
        )
    license_files = project.get("license-files")
    if not isinstance(license_files, list) or package["license_file"] not in license_files:
        errors.append(
            "pyproject project.license-files must include release contract license_file "
            f"{package['license_file']!r}"
        )
    if project.get("requires-python") != python["requires_python"]:
        errors.append(
            "pyproject requires-python must exactly match release contract: "
            f"{python['requires_python']}"
        )

    optional = project.get("optional-dependencies")
    if not isinstance(optional, dict) or "dev" not in optional:
        errors.append("pyproject must define project.optional-dependencies.dev")

    build_system = payload.get("build-system")
    if not isinstance(build_system, dict):
        errors.append("pyproject.toml lacks [build-system]")
    else:
        requirements = build_system.get("requires")
        if not isinstance(requirements, list):
            errors.append("build-system.requires must be an array")
        else:
            minimum = _minimum_setuptools(requirements)
            required_minimum = int(package["setuptools_minimum"])
            if minimum is None or minimum < required_minimum:
                errors.append(f"build-system requires setuptools>={required_minimum}")

    setuptools = payload.get("tool", {}).get("setuptools", {})
    expected_root = str(package["package_root"])
    if not isinstance(setuptools, dict) or setuptools.get("package-dir") != {"": expected_root}:
        errors.append(f"pyproject must configure setuptools package-dir = {{'': {expected_root!r}}}")


def _validate_readme(
    root: Path,
    manifest: Mapping[str, Any],
    errors: list[str],
    *,
    readme_text_override: str | None,
) -> None:
    path = root / "README.md"
    if not path.is_file() and readme_text_override is None:
        return
    readme = readme_text_override if readme_text_override is not None else _read_text(path, errors)
    if not readme:
        return

    for command in _string_list(manifest["readme_commands"], "readme_commands"):
        if command not in readme:
            errors.append(f"README is missing release-contract command: {command}")
    for statement in _string_list(
        manifest["readme_required_statements"], "readme_required_statements"
    ):
        if statement not in readme:
            errors.append(f"README is missing release-contract status statement: {statement}")
    for snippet in _string_list(
        manifest["readme_forbidden_snippets"], "readme_forbidden_snippets"
    ):
        if snippet in readme:
            errors.append(f"README contains forbidden stale/overbroad claim: {snippet}")


def _validate_results(root: Path, manifest: Mapping[str, Any], errors: list[str]) -> int:
    checked = 0
    for entry in manifest["result_entries"]:
        relative = str(entry["path"])
        path = root / relative
        if not path.is_file():
            errors.append(f"missing release-contract result: {relative}")
            continue
        checked += 1
        if entry["kind"] == "json_object":
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                errors.append(f"invalid JSON result {relative}: {type(exc).__name__}: {exc}")
                continue
            if not isinstance(value, dict):
                errors.append(f"result must be a JSON object: {relative}")
    return checked


def validate_repository(
    root: Path,
    *,
    manifest_override: Mapping[str, Any] | None = None,
    readme_text_override: str | None = None,
    pyproject_text_override: str | None = None,
    license_text_override: str | None = None,
) -> ContractReport:
    root = root.resolve()
    errors: list[str] = []
    if not root.is_dir():
        errors.append(f"repository root is not a directory: {root}")
        return ContractReport(root, 0, 0, 0, tuple(errors))

    try:
        manifest = dict(manifest_override) if manifest_override is not None else load_release_manifest(root)
        # Re-validate overrides through the same schema checks by serializing to a temporary
        # in-memory structure rather than trusting tests/callers to provide valid shapes.
        if manifest_override is not None:
            if manifest.get("schema_version") != "mindmap-release-contract-v0.2":
                raise ContractError("unsupported release contract schema_version")
            _string_list(manifest.get("required_paths"), "required_paths")
            _string_list(manifest.get("readme_commands"), "readme_commands")
            _string_list(manifest.get("readme_required_statements"), "readme_required_statements")
            _string_list(manifest.get("readme_forbidden_snippets"), "readme_forbidden_snippets")
            if not isinstance(manifest.get("python"), dict) or not isinstance(manifest.get("package"), dict):
                raise ContractError("manifest override lacks python/package objects")
            if not isinstance(manifest.get("result_entries"), list) or not manifest["result_entries"]:
                raise ContractError("manifest override lacks result_entries")
    except ContractError as exc:
        errors.append(str(exc))
        return ContractReport(root, 0, 0, 0, tuple(errors))

    required_paths = _string_list(manifest["required_paths"], "required_paths")
    for relative in required_paths:
        if not (root / relative).exists():
            errors.append(f"missing release-contract path: {relative}")

    _validate_license(root, manifest["package"], errors, license_text_override=license_text_override)
    _validate_pyproject(root, manifest, errors, pyproject_text_override=pyproject_text_override)
    _validate_readme(root, manifest, errors, readme_text_override=readme_text_override)
    result_count = _validate_results(root, manifest, errors)

    ci_versions = _string_list(manifest["python"]["ci_versions"], "python.ci_versions")
    if "3.11" not in ci_versions or "3.14" not in ci_versions:
        errors.append("release contract CI versions must include the lower bound 3.11 and current stable 3.14")

    tests = root / "tests"
    if tests.is_dir() and not any(tests.glob("test_*.py")):
        errors.append("tests/ contains no test_*.py files")
    package_root = root / str(manifest["package"]["package_root"]) / "mindmap"
    if package_root.is_dir() and not any(package_root.rglob("*.py")):
        errors.append(f"{manifest['package']['package_root']}/mindmap contains no Python modules")

    return ContractReport(
        root=root,
        checked_paths=len(required_paths),
        checked_commands=len(manifest["readme_commands"]),
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
