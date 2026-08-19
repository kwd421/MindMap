from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from .adapter_guard import canonical_json_sha256
from .gatemem_runner import ProtectedBenchmarkResult, run_protected_benchmark
from .gatemem_session import PublicGateMemAgent

PINNED_GATEMEM_COMMIT = "603f9f4b4ba4b77f043c20f85687fa016fd720b0"
SUPPORTED_GATEMEM_DOMAINS = frozenset(
    {"medical", "education", "household", "office"}
)


class GateMemOfficialError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class GateMemCheckoutAudit:
    checkout_path: str
    expected_commit: str
    observed_commit: str
    dirty: bool
    scorer_sha256: str
    episodes_sha256: str
    checkpoints_sha256: str


@dataclass(frozen=True, slots=True)
class GateMemOfficialScore:
    command: tuple[str, ...]
    return_code: int
    stdout_sha256: str
    stderr_sha256: str
    summary_sha256: str | None
    summary: dict[str, Any] | None


@dataclass(frozen=True, slots=True)
class GateMemExternalRunResult:
    output_dir: str
    prediction_count: int
    checkout: GateMemCheckoutAudit
    official_score: GateMemOfficialScore | None
    run_metadata_sha256: str


AgentFactory = Callable[[], PublicGateMemAgent]


def _sha256_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                value = json.loads(text)
            except json.JSONDecodeError as exc:
                raise GateMemOfficialError(
                    f"invalid JSON in {path} at line {line_number}: {exc}"
                ) from exc
            if not isinstance(value, dict):
                raise GateMemOfficialError(
                    f"expected JSON object in {path} at line {line_number}"
                )
            rows.append(value)
    return tuple(rows)


def _write_json(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ).encode("utf-8") + b"\n"
    path.write_bytes(data)
    return _sha256_bytes(data)


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = sha256()
    with path.open("wb") as handle:
        for row in rows:
            line = json.dumps(
                dict(row),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8") + b"\n"
            handle.write(line)
            digest.update(line)
    return digest.hexdigest()


def _run_capture(
    command: Sequence[str], *, cwd: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git_revision(path: Path) -> str:
    process = _run_capture(("git", "rev-parse", "HEAD"), cwd=path)
    if process.returncode != 0:
        raise GateMemOfficialError(
            f"failed to read Git revision for {path}: {process.stderr.strip()}"
        )
    revision = process.stdout.strip()
    if len(revision) != 40:
        raise GateMemOfficialError(f"unexpected Git revision: {revision!r}")
    return revision


def git_dirty(path: Path) -> bool:
    process = _run_capture(
        ("git", "status", "--porcelain", "--untracked-files=no"), cwd=path
    )
    if process.returncode != 0:
        raise GateMemOfficialError(
            f"failed to inspect Git status for {path}: {process.stderr.strip()}"
        )
    return bool(process.stdout.strip())


def verify_gatemem_checkout(
    checkout: Path,
    *,
    domain: str,
    expected_commit: str = PINNED_GATEMEM_COMMIT,
    require_clean: bool = True,
) -> GateMemCheckoutAudit:
    checkout = checkout.resolve()
    if domain not in SUPPORTED_GATEMEM_DOMAINS:
        raise GateMemOfficialError(f"unsupported GateMem domain: {domain}")

    scorer = checkout / "bench" / "scripts" / "score_predictions.py"
    data_dir = checkout / "bench" / "data" / domain
    episodes = data_dir / "episodes.jsonl"
    checkpoints = data_dir / "checkpoints.jsonl"
    for path in (scorer, episodes, checkpoints):
        if not path.is_file():
            raise GateMemOfficialError(f"required GateMem file is missing: {path}")

    observed = git_revision(checkout)
    if observed != expected_commit:
        raise GateMemOfficialError(
            "GateMem checkout revision mismatch: "
            f"expected={expected_commit}, observed={observed}"
        )
    dirty = git_dirty(checkout)
    if require_clean and dirty:
        raise GateMemOfficialError("GateMem checkout has tracked modifications")

    return GateMemCheckoutAudit(
        checkout_path=str(checkout),
        expected_commit=expected_commit,
        observed_commit=observed,
        dirty=dirty,
        scorer_sha256=sha256_file(scorer),
        episodes_sha256=sha256_file(episodes),
        checkpoints_sha256=sha256_file(checkpoints),
    )


def _audit_rows(
    result: ProtectedBenchmarkResult,
) -> tuple[
    tuple[dict[str, Any], ...],
    tuple[dict[str, Any], ...],
    tuple[dict[str, Any], ...],
]:
    return (
        tuple(asdict(value) for value in result.episode_audits),
        tuple(asdict(value) for value in result.turn_audits),
        tuple(asdict(value) for value in result.checkpoint_audits),
    )


def run_official_scorer(
    *,
    checkout: Path,
    domain: str,
    predictions_path: Path,
    score_output_dir: Path,
    python_executable: str = sys.executable,
    gate_by_action: bool = False,
) -> GateMemOfficialScore:
    scorer = checkout / "bench" / "scripts" / "score_predictions.py"
    data_dir = checkout / "bench" / "data" / domain
    score_output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        python_executable,
        str(scorer),
        "--data_dir",
        str(data_dir),
        "--predictions",
        str(predictions_path),
        "--out_dir",
        str(score_output_dir),
    ]
    if gate_by_action:
        command.append("--gate_by_action")

    process = _run_capture(command, cwd=checkout)
    summary_path = score_output_dir / "summary.json"
    summary: dict[str, Any] | None = None
    summary_hash: str | None = None
    if summary_path.is_file():
        value = json.loads(summary_path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise GateMemOfficialError(
                "official GateMem summary is not a JSON object"
            )
        summary = value
        summary_hash = sha256_file(summary_path)

    score = GateMemOfficialScore(
        command=tuple(command),
        return_code=process.returncode,
        stdout_sha256=_sha256_bytes(process.stdout.encode("utf-8")),
        stderr_sha256=_sha256_bytes(process.stderr.encode("utf-8")),
        summary_sha256=summary_hash,
        summary=summary,
    )
    if process.returncode != 0:
        raise GateMemOfficialError(
            "official GateMem scorer failed\n"
            f"stdout:\n{process.stdout}\n"
            f"stderr:\n{process.stderr}"
        )
    if summary is None:
        raise GateMemOfficialError(
            "official GateMem scorer produced no summary.json"
        )
    return score


def run_external_gatemem(
    *,
    checkout: Path,
    domain: str,
    output_dir: Path,
    agent_factory: AgentFactory,
    method_name: str,
    method_config: Mapping[str, Any],
    expected_commit: str = PINNED_GATEMEM_COMMIT,
    require_clean_checkout: bool = True,
    invoke_official_scorer: bool = True,
    scorer_python: str = sys.executable,
    gate_by_action: bool = False,
    repository_revision: str | None = None,
    opaque_id_secret: bytes | None = None,
) -> GateMemExternalRunResult:
    """Execute a pinned GateMem run behind the opaque method firewall.

    The evaluator reads source data and restores source checkpoint IDs only in
    scorer-facing rows. Source↔method mappings and the opaque key are never
    written to the result directory or passed to the method process.
    """

    checkout = checkout.resolve()
    output_dir = output_dir.resolve()
    if not method_name.strip():
        raise ValueError("method_name must not be empty")

    checkout_audit = verify_gatemem_checkout(
        checkout,
        domain=domain,
        expected_commit=expected_commit,
        require_clean=require_clean_checkout,
    )
    data_dir = checkout / "bench" / "data" / domain
    episodes = load_jsonl(data_dir / "episodes.jsonl")
    checkpoints = load_jsonl(data_dir / "checkpoints.jsonl")
    if not episodes or not checkpoints:
        raise GateMemOfficialError(
            "GateMem domain contains no episodes or checkpoints"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    protected = run_protected_benchmark(
        agent_factory=agent_factory,
        episodes=episodes,
        checkpoints=checkpoints,
        opaque_id_secret=opaque_id_secret,
    )
    predictions_path = output_dir / "predictions.jsonl"
    predictions_hash = _write_jsonl(predictions_path, protected.predictions)

    episode_rows, turn_rows, checkpoint_rows = _audit_rows(protected)
    episode_audit_hash = _write_jsonl(
        output_dir / "episode_audit.jsonl", episode_rows
    )
    turn_audit_hash = _write_jsonl(
        output_dir / "turn_audit.jsonl", turn_rows
    )
    checkpoint_audit_hash = _write_jsonl(
        output_dir / "checkpoint_audit.jsonl", checkpoint_rows
    )

    official_score: GateMemOfficialScore | None = None
    if invoke_official_scorer:
        official_score = run_official_scorer(
            checkout=checkout,
            domain=domain,
            predictions_path=predictions_path,
            score_output_dir=output_dir / "official_score",
            python_executable=scorer_python,
            gate_by_action=gate_by_action,
        )

    metadata = {
        "schema_version": "track-x-gatemem-external-run-v0.2",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "domain": domain,
        "method": {
            "name": method_name,
            "config": dict(method_config),
        },
        "repository_revision": repository_revision
        or os.environ.get("GITHUB_SHA")
        or "unrecorded",
        "checkout": asdict(checkout_audit),
        "counts": {
            "episodes": len(episodes),
            "checkpoints": len(checkpoints),
            "predictions": len(protected.predictions),
            "episode_audits": len(protected.episode_audits),
            "turn_audits": len(protected.turn_audits),
            "checkpoint_audits": len(protected.checkpoint_audits),
        },
        "opaque_identity_firewall": {
            "enabled": True,
            "key_commitment_sha256": protected.opaque_key_commitment_sha256,
            "mapping_commitment_sha256": (
                protected.opaque_mapping_commitment_sha256
            ),
            "mapping_count": protected.opaque_mapping_count,
            "mapping_serialized": False,
        },
        "artifact_sha256": {
            "predictions.jsonl": predictions_hash,
            "episode_audit.jsonl": episode_audit_hash,
            "turn_audit.jsonl": turn_audit_hash,
            "checkpoint_audit.jsonl": checkpoint_audit_hash,
        },
        "official_score": (
            asdict(official_score) if official_score is not None else None
        ),
        "boundary": {
            "raw_benchmark_text_copied_to_result": False,
            "source_identifiers_passed_to_method": False,
            "source_as_of_turn_id_passed_to_method": False,
            "relationships_passed_to_method": False,
            "hidden_checkpoint_fields_passed_to_method": False,
            "record_refs_passed_to_method": False,
            "memory_ops_passed_to_method": False,
            "official_scorer_modified": False,
        },
    }
    metadata_hash = _write_json(output_dir / "run_metadata.json", metadata)

    written_metadata = json.loads(
        (output_dir / "run_metadata.json").read_text(encoding="utf-8")
    )
    if canonical_json_sha256(written_metadata) == "":  # pragma: no cover
        raise AssertionError("unreachable empty digest")

    return GateMemExternalRunResult(
        output_dir=str(output_dir),
        prediction_count=len(protected.predictions),
        checkout=checkout_audit,
        official_score=official_score,
        run_metadata_sha256=metadata_hash,
    )
