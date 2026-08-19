#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


METHOD_ALIASES = {
    "always_abstain": ("always_abstain", "abstain", "always-abstain"),
    "raw_bm25": ("raw_bm25", "bm25", "raw-bm25"),
}
DATA_FLAGS = (
    "--gatemem-root",
    "--gatemem-dir",
    "--data-root",
    "--data-dir",
    "--dataset-root",
)
OUTPUT_FLAGS = ("--output-dir", "--output", "--predictions", "--predictions-path")
METHOD_FLAGS = ("--method", "--baseline", "--agent")
DOMAIN_FLAGS = ("--domains", "--domain")


@dataclass(frozen=True, slots=True)
class Candidate:
    path: str
    score: int
    has_main: bool
    contains_bm25: bool
    contains_abstain: bool
    contains_argparse: bool


@dataclass(frozen=True, slots=True)
class Attempt:
    method: str
    candidate: str
    command: list[str]
    returncode: int
    stdout_path: str
    stderr_path: str
    produced_files: list[str]


def _run(
    command: list[str],
    *,
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
    timeout: int = 1800,
) -> int:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            stdout=stdout,
            stderr=stderr,
            timeout=timeout,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
    return completed.returncode


def discover(root: Path) -> list[Candidate]:
    rows: list[Candidate] = []
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        lowered = text.lower()
        has_main = "if __name__" in text
        contains_bm25 = "bm25" in lowered
        contains_abstain = "abstain" in lowered
        contains_argparse = "argparse" in lowered or "typer" in lowered or "click" in lowered
        gatemem = "gatemem" in lowered or "gatemem" in relative.lower()
        score = (
            8 * int(gatemem)
            + 5 * int(has_main)
            + 4 * int(contains_argparse)
            + 3 * int(contains_bm25)
            + 3 * int(contains_abstain)
            + 2 * int("experiment" in relative.lower() or "script" in relative.lower())
        )
        if score >= 10:
            rows.append(
                Candidate(
                    path=relative,
                    score=score,
                    has_main=has_main,
                    contains_bm25=contains_bm25,
                    contains_abstain=contains_abstain,
                    contains_argparse=contains_argparse,
                )
            )
    return sorted(rows, key=lambda row: (-row.score, row.path))


def _help(root: Path, candidate: Candidate, audit_dir: Path) -> tuple[str, int]:
    slug = candidate.path.replace("/", "__")
    stdout = audit_dir / "help" / f"{slug}.stdout.txt"
    stderr = audit_dir / "help" / f"{slug}.stderr.txt"
    returncode = _run(
        [sys.executable, candidate.path, "--help"],
        cwd=root,
        stdout_path=stdout,
        stderr_path=stderr,
        timeout=120,
    )
    text = stdout.read_text(encoding="utf-8", errors="ignore") + "\n" + stderr.read_text(
        encoding="utf-8", errors="ignore"
    )
    return text, returncode


def _options(help_text: str) -> set[str]:
    return set(re.findall(r"(?<!\w)(--[a-zA-Z][a-zA-Z0-9_-]*)", help_text))


def _first_supported(options: set[str], candidates: Iterable[str]) -> str | None:
    return next((flag for flag in candidates if flag in options), None)


def _commands_for(
    *,
    candidate: Candidate,
    help_text: str,
    gatemem_root: Path,
    method: str,
    method_output: Path,
) -> list[list[str]]:
    options = _options(help_text)
    data_flag = _first_supported(options, DATA_FLAGS)
    output_flag = _first_supported(options, OUTPUT_FLAGS)
    method_flag = _first_supported(options, METHOD_FLAGS)
    domain_flag = _first_supported(options, DOMAIN_FLAGS)
    base = [sys.executable, candidate.path]
    if data_flag:
        data_value = (
            gatemem_root / "bench" / "data"
            if data_flag in {"--data-dir", "--dataset-root"}
            else gatemem_root
        )
        base += [data_flag, str(data_value)]
    if output_flag:
        if output_flag in {"--predictions", "--predictions-path", "--output"}:
            base += [output_flag, str(method_output / "predictions.jsonl")]
        else:
            base += [output_flag, str(method_output)]
    if domain_flag == "--domains":
        base += [domain_flag, "medical", "office", "education", "household"]
    elif domain_flag == "--domain":
        # A single-domain CLI is attempted once per official domain below.
        pass

    aliases = METHOD_ALIASES[method]
    commands: list[list[str]] = []
    if method_flag:
        for alias in aliases:
            commands.append([*base, method_flag, alias])
    else:
        # Some PRs expose one script per method or use a fixed default.
        commands.append(base)

    if domain_flag == "--domain":
        expanded: list[list[str]] = []
        for command in commands:
            for domain in ("medical", "office", "education", "household"):
                expanded.append([*command, domain_flag, domain])
        commands = expanded
    return commands


def _produced_files(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def run_discovery(
    pr43_root: Path,
    gatemem_root: Path,
    output_root: Path,
) -> dict[str, object]:
    output_root.mkdir(parents=True, exist_ok=True)
    candidates = discover(pr43_root)
    (output_root / "candidates.json").write_text(
        json.dumps([asdict(row) for row in candidates], indent=2) + "\n",
        encoding="utf-8",
    )

    attempts: list[Attempt] = []
    successes: dict[str, dict[str, object]] = {}
    for candidate in candidates:
        help_text, help_returncode = _help(pr43_root, candidate, output_root)
        if help_returncode not in {0, 1, 2}:
            continue
        for method in ("always_abstain", "raw_bm25"):
            if method == "raw_bm25" and not candidate.contains_bm25:
                continue
            if method == "always_abstain" and not candidate.contains_abstain:
                continue
            if method in successes:
                continue
            method_output = output_root / "runs" / method / candidate.path.replace("/", "__")
            method_output.mkdir(parents=True, exist_ok=True)
            commands = _commands_for(
                candidate=candidate,
                help_text=help_text,
                gatemem_root=gatemem_root,
                method=method,
                method_output=method_output,
            )
            for index, command in enumerate(commands, start=1):
                stdout = method_output / f"attempt-{index}.stdout.txt"
                stderr = method_output / f"attempt-{index}.stderr.txt"
                try:
                    returncode = _run(
                        command,
                        cwd=pr43_root,
                        stdout_path=stdout,
                        stderr_path=stderr,
                    )
                except subprocess.TimeoutExpired:
                    returncode = 124
                    stderr.write_text("command timed out\n", encoding="utf-8")
                produced = _produced_files(method_output)
                attempt = Attempt(
                    method=method,
                    candidate=candidate.path,
                    command=command,
                    returncode=returncode,
                    stdout_path=stdout.relative_to(output_root).as_posix(),
                    stderr_path=stderr.relative_to(output_root).as_posix(),
                    produced_files=produced,
                )
                attempts.append(attempt)
                if returncode == 0 and any(
                    name.endswith((".json", ".jsonl", ".csv")) for name in produced
                ):
                    successes[method] = {
                        "candidate": candidate.path,
                        "command": command,
                        "produced_files": produced,
                    }
                    break

    result = {
        "classification": (
            "exploratory PR #43 entry-point discovery; an attempt is not an "
            "accepted official benchmark result until prediction coverage and "
            "official metrics are validated"
        ),
        "candidates": [asdict(row) for row in candidates],
        "attempts": [asdict(row) for row in attempts],
        "successes": successes,
    }
    (output_root / "discovery.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr43-root", type=Path, required=True)
    parser.add_argument("--gatemem-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    result = run_discovery(
        args.pr43_root.resolve(),
        args.gatemem_root.resolve(),
        args.output_root.resolve(),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    # Discovery itself succeeds even when no executable public command is found;
    # the missing command is an explicit R1 blocker rather than hidden failure.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
