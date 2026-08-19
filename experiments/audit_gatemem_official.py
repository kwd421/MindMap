#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


OFFICIAL_DOMAINS = ("medical", "office", "education", "household")
FORBIDDEN_METHOD_TOKENS = (
    "hidden_label",
    "gold_record",
    "gold_answer",
    "expected_answer",
    "memory_ops",
    "record_refs",
    "deletion_target",
    "future_turn",
)
CHECKPOINT_CONTAINER_KEYS = {
    "checkpoints",
    "evaluation_checkpoints",
    "eval_checkpoints",
    "probes",
}
CHECKPOINT_ID_KEYS = {
    "checkpoint_id",
    "query_id",
    "probe_id",
}


@dataclass(frozen=True, slots=True)
class FileManifestRow:
    path: str
    bytes: int
    sha256: str


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout.strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _manifest(root: Path, paths: Iterable[Path]) -> list[FileManifestRow]:
    rows: list[FileManifestRow] = []
    for path in sorted(set(paths)):
        if not path.is_file():
            continue
        rows.append(
            FileManifestRow(
                path=path.relative_to(root).as_posix(),
                bytes=path.stat().st_size,
                sha256=_sha256(path),
            )
        )
    return rows


def _load_json(path: Path) -> Any:
    if path.suffix.lower() == ".jsonl":
        rows: list[Any] = []
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"invalid JSONL at {path}:{line_number}: {exc}"
                    ) from exc
        return rows
    return json.loads(path.read_text(encoding="utf-8"))


def _walk_json(value: Any, *, path: tuple[str, ...] = ()):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk_json(child, path=(*path, str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_json(child, path=(*path, str(index)))


def _json_inventory(data_files: list[Path], data_root: Path) -> dict[str, Any]:
    top_level_types: Counter[str] = Counter()
    key_frequency: Counter[str] = Counter()
    checkpoint_ids: set[str] = set()
    checkpoint_container_rows: list[dict[str, Any]] = []
    parse_failures: list[str] = []
    files_by_domain: Counter[str] = Counter()

    for path in data_files:
        relative = path.relative_to(data_root).as_posix()
        domain = next((d for d in OFFICIAL_DOMAINS if d in path.parts), "unknown")
        files_by_domain[domain] += 1
        try:
            payload = _load_json(path)
        except Exception as exc:  # audit preserves every unreadable file
            parse_failures.append(
                f"{relative}: {type(exc).__name__}: {exc}"
            )
            continue
        top_level_types[type(payload).__name__] += 1
        for object_path, value in _walk_json(payload):
            if isinstance(value, dict):
                lowered = {
                    str(key).lower(): child for key, child in value.items()
                }
                key_frequency.update(lowered.keys())
                for id_key in CHECKPOINT_ID_KEYS:
                    if id_key in lowered and lowered[id_key] is not None:
                        checkpoint_ids.add(str(lowered[id_key]))
            if object_path:
                key = object_path[-1].lower()
                if key in CHECKPOINT_CONTAINER_KEYS and isinstance(value, list):
                    checkpoint_container_rows.append(
                        {
                            "file": relative,
                            "json_path": "/".join(object_path),
                            "rows": len(value),
                        }
                    )

    return {
        "json_files": len(data_files),
        "files_by_domain": dict(sorted(files_by_domain.items())),
        "top_level_types": dict(top_level_types),
        "parse_failures": parse_failures,
        "unique_explicit_checkpoint_ids": len(checkpoint_ids),
        "checkpoint_container_rows": checkpoint_container_rows,
        "checkpoint_container_total": sum(
            int(row["rows"]) for row in checkpoint_container_rows
        ),
        "most_common_keys": key_frequency.most_common(80),
    }


def _readme_contract(gatemem_root: Path) -> dict[str, Any]:
    readme = (gatemem_root / "README.md").read_text(encoding="utf-8")
    normalized = readme.replace(",", "")
    advertised_episodes = bool(
        re.search(
            r"(?:Episodes[-|: ]+|\*\*Episodes\*\*\s*\|\s*)91\b",
            normalized,
            re.I,
        )
    )
    advertised_checkpoints = bool(
        re.search(
            r"(?:Checkpoints[-|: ]+|\*\*Checkpoints\*\*\s*\|\s*)2218\b",
            normalized,
            re.I,
        )
    )
    domains_present = {
        domain: bool(re.search(rf"\b{re.escape(domain)}\b", readme, re.I))
        for domain in OFFICIAL_DOMAINS
    }
    required_phrases = {
        "utility": "Utility" in readme,
        "access_control": (
            "Access Control" in readme or "Access-Control" in readme
        ),
        "active_forgetting": (
            "Active Forgetting" in readme or "Active-Forgetting" in readme
        ),
        "prediction_jsonl": "predictions.jsonl" in readme,
    }
    return {
        "advertised_episodes_91": advertised_episodes,
        "advertised_checkpoints_2218": advertised_checkpoints,
        "domains_present": domains_present,
        "required_phrases": required_phrases,
    }


def _python_entry_points(root: Path) -> list[str]:
    rows: list[str] = []
    for path in sorted(root.rglob("*.py")):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "if __name__" in text and (
            "gatemem" in path.as_posix().lower()
            or "gatemem" in text.lower()
        ):
            rows.append(path.relative_to(root).as_posix())
    return rows


def _boundary_scan(mindmap_root: Path) -> dict[str, Any]:
    findings: dict[str, list[dict[str, Any]]] = defaultdict(list)
    candidate_files: list[str] = []
    for path in sorted(mindmap_root.rglob("*.py")):
        relative = path.relative_to(mindmap_root).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        joined = "\n".join(lines).lower()
        if "gatemem" in joined or "gatemem" in relative.lower():
            candidate_files.append(relative)
        for line_number, line in enumerate(lines, start=1):
            lowered = line.lower()
            for token in FORBIDDEN_METHOD_TOKENS:
                if token in lowered:
                    findings[token].append(
                        {
                            "path": relative,
                            "line": line_number,
                            "text": line.strip()[:240],
                        }
                    )
    return {
        "candidate_files": sorted(candidate_files),
        "token_findings": dict(sorted(findings.items())),
        "note": (
            "Static token hits are review leads, not automatic leakage findings; "
            "tests, adapters, and evaluator code may legitimately name these fields."
        ),
    }


def audit(
    gatemem_root: Path,
    mindmap_root: Path,
    output: Path,
    *,
    expected_gatemem_commit: str,
    expected_mindmap_commit: str,
    expected_scorer_sha256: str,
) -> dict[str, Any]:
    data_root = gatemem_root / "bench" / "data"
    scorer_path = gatemem_root / "bench" / "scripts" / "score_predictions.py"
    if not data_root.is_dir():
        raise FileNotFoundError(
            f"official GateMem data root missing: {data_root}"
        )
    if not scorer_path.is_file():
        raise FileNotFoundError(
            f"official GateMem scoring entrypoint missing: {scorer_path}"
        )

    observed_gatemem_commit = _git(gatemem_root, "rev-parse", "HEAD")
    observed_mindmap_commit = _git(mindmap_root, "rev-parse", "HEAD")
    scorer_sha256 = _sha256(scorer_path)
    if observed_gatemem_commit != expected_gatemem_commit:
        raise RuntimeError(
            "GateMem revision mismatch: "
            f"{observed_gatemem_commit} != {expected_gatemem_commit}"
        )
    if observed_mindmap_commit != expected_mindmap_commit:
        raise RuntimeError(
            "MindMap target revision mismatch: "
            f"{observed_mindmap_commit} != {expected_mindmap_commit}"
        )
    if scorer_sha256 != expected_scorer_sha256:
        raise RuntimeError(
            "official scoring entrypoint hash mismatch: "
            f"{scorer_sha256} != {expected_scorer_sha256}"
        )

    data_files = [
        path
        for path in data_root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".json", ".jsonl"}
    ]
    official_manifest = _manifest(gatemem_root, data_files)
    contract = _readme_contract(gatemem_root)
    inventory = _json_inventory(data_files, data_root)

    required_contract_ok = (
        contract["advertised_episodes_91"]
        and contract["advertised_checkpoints_2218"]
        and all(contract["domains_present"].values())
        and all(contract["required_phrases"].values())
    )

    result = {
        "study": (
            "GateMem official public benchmark R0 reproducibility audit "
            "for the PR #46 producing commit"
        ),
        "classification": (
            "source, scorer, implementation, and capability audit; "
            "not an architecture-effect result"
        ),
        "upstream": {
            "repository": "rzhub/GateMem",
            "commit": observed_gatemem_commit,
            "remote": _git(gatemem_root, "remote", "get-url", "origin"),
            "scorer_entrypoint": "bench/scripts/score_predictions.py",
            "scorer_sha256": scorer_sha256,
            "readme_contract": contract,
            "required_contract_ok": required_contract_ok,
            "data_inventory": inventory,
            "data_manifest_rows": len(official_manifest),
            "data_manifest_bytes": sum(
                row.bytes for row in official_manifest
            ),
        },
        "mindmap_target": {
            "pull_request": 46,
            "commit": observed_mindmap_commit,
            "remote": _git(mindmap_root, "remote", "get-url", "origin"),
            "entry_points": _python_entry_points(mindmap_root),
            "boundary_scan": _boundary_scan(mindmap_root),
        },
        "official_data_manifest": [
            asdict(row) for row in official_manifest
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if not required_contract_ok:
        raise RuntimeError(
            "official README/toolkit contract did not match frozen expectations"
        )
    if inventory["parse_failures"]:
        raise RuntimeError(
            "one or more official JSON/JSONL data files could not be parsed"
        )
    if inventory["unique_explicit_checkpoint_ids"] != 2218:
        raise RuntimeError(
            "official checkpoint coverage changed: "
            f"{inventory['unique_explicit_checkpoint_ids']} != 2218"
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gatemem-root", type=Path, required=True)
    parser.add_argument("--mindmap-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--expected-gatemem-commit",
        required=True,
    )
    parser.add_argument(
        "--expected-mindmap-commit",
        required=True,
    )
    parser.add_argument(
        "--expected-scorer-sha256",
        required=True,
    )
    args = parser.parse_args()
    result = audit(
        args.gatemem_root.resolve(),
        args.mindmap_root.resolve(),
        args.output.resolve(),
        expected_gatemem_commit=args.expected_gatemem_commit,
        expected_mindmap_commit=args.expected_mindmap_commit,
        expected_scorer_sha256=args.expected_scorer_sha256,
    )
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "study",
                    "classification",
                    "upstream",
                    "mindmap_target",
                )
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
