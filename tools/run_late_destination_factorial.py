from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


SCHEMA_VERSION = "late-destination-factorial-v1"
MAIN_REVISION = "069c5f4b16b2f594aec48924161ae8944f39652e"
PR55_REVISION = "2bda2ff38ea79dd0901f6329490d2f9940690261"
DESTINATION_CREATION_TIMES = (5, 6, 7)
REPLICATION_SYSTEM_TIME = 6
IMPLEMENTATIONS = ("gold", "generic", "typed")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(checkout: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(checkout), *args], text=True
    ).strip()


def require_exact_clean_checkout(checkout: Path, revision: str) -> None:
    actual = git_output(checkout, "rev-parse", "HEAD")
    if actual != revision:
        raise RuntimeError(
            f"checkout revision mismatch: expected {revision}, found {actual}"
        )
    status = git_output(
        checkout, "status", "--porcelain=v1", "--untracked-files=all"
    )
    if status:
        raise RuntimeError(f"checkout is dirty: {checkout}")


def worker_rows(
    checkout: Path, revision_role: str, revision: str
) -> list[dict[str, object]]:
    sys.path.insert(0, str(checkout / "src"))
    try:
        from mindmap.canonical.fixture_common import E
        from mindmap.canonical.generic import GenericLedger
        from mindmap.canonical.gold import GoldSemantics
        from mindmap.canonical.model import TargetQuery, TargetSpace
        from mindmap.canonical.typed import TypedLedger

        models = {
            "gold": GoldSemantics,
            "generic": GenericLedger,
            "typed": TypedLedger,
        }
        rows: list[dict[str, object]] = []
        for destination_time in DESTINATION_CREATION_TIMES:
            events = [
                E("p", "principal_create", 0, object_id="P"),
                E(
                    "src",
                    "mind_create",
                    0,
                    object_id="R1",
                    actor_principal_id="P",
                ),
                E(
                    "world",
                    "world_create",
                    0,
                    object_id="main",
                    attrs={"parent": "", "fork_valid_time": None},
                ),
                E(
                    "lineage",
                    "lineage",
                    1,
                    lineage_kind="operational_replica",
                    source_mind_instance_id="R1",
                    destination_mind_instance_id="R2",
                ),
                E(
                    "evidence",
                    "evidence",
                    2,
                    object_id="E.sync",
                    proposition_id="sync_p",
                    actor_principal_id="P",
                    actor_mind_instance_id="R1",
                    about_world_branch_id="main",
                    source_family_id="sync-source",
                ),
                E(
                    "observe",
                    "exposure",
                    2,
                    object_id="E.sync",
                    destination_mind_instance_id="R1",
                    transfer_kind="observe",
                ),
                E(
                    "auth",
                    "authorization",
                    3,
                    object_id="AUTH",
                    source_mind_instance_id="R1",
                    destination_mind_instance_id="R2",
                    policy_operation="grant",
                ),
                E(
                    "dest",
                    "mind_create",
                    destination_time,
                    object_id="R2",
                    actor_principal_id="P",
                ),
                E(
                    "rep",
                    "exposure",
                    REPLICATION_SYSTEM_TIME,
                    object_id="E.sync",
                    source_mind_instance_id="R1",
                    destination_mind_instance_id="R2",
                    transfer_kind="state_replication",
                    authorization_id="AUTH",
                ),
            ]
            query = TargetQuery(
                "q",
                TargetSpace.AVAILABLE,
                10,
                evidence_id="E.sync",
                mind_instance_id="R2",
            )
            stratum = {
                5: "before_replication",
                6: "equal_to_replication",
                7: "after_replication",
            }[destination_time]
            for implementation, model in models.items():
                answer = model(events).answer(query)
                if not isinstance(answer, bool):
                    raise RuntimeError(
                        f"non-Boolean AVAILABLE answer: {implementation}={answer!r}"
                    )
                rows.append(
                    {
                        "revision_role": revision_role,
                        "revision_sha": revision,
                        "destination_creation_system_time": destination_time,
                        "destination_stratum": stratum,
                        "replication_system_time": REPLICATION_SYSTEM_TIME,
                        "implementation": implementation,
                        "available": answer,
                    }
                )
        return rows
    finally:
        sys.path.pop(0)


def run_worker(
    checkout: Path, revision_role: str, revision: str
) -> list[dict[str, object]]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker",
            "--checkout",
            str(checkout),
            "--revision-role",
            revision_role,
            "--revision",
            revision,
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"worker failed for {revision_role}: {completed.stderr.strip()}"
        )
    return json.loads(completed.stdout)


def summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    if len(rows) != 18:
        raise RuntimeError(f"expected 18 Boolean output rows, found {len(rows)}")
    keyed: dict[tuple[str, int, str], bool] = {}
    for row in rows:
        key = (
            str(row["revision_role"]),
            int(row["destination_creation_system_time"]),
            str(row["implementation"]),
        )
        if key in keyed:
            raise RuntimeError(f"duplicate output cell: {key}")
        available = row["available"]
        if type(available) is not bool:
            raise RuntimeError(
                f"non-Boolean output cell: {key}={available!r}"
            )
        keyed[key] = available

    paired_differences = 0
    paired_rows = 0
    for destination_time in DESTINATION_CREATION_TIMES:
        for implementation in IMPLEMENTATIONS:
            paired_rows += 1
            paired_differences += (
                keyed[("main", destination_time, implementation)]
                != keyed[("pr55", destination_time, implementation)]
            )

    outputs_by_role = {
        role: {
            str(destination_time): {
                implementation: keyed[(role, destination_time, implementation)]
                for implementation in IMPLEMENTATIONS
            }
            for destination_time in DESTINATION_CREATION_TIMES
        }
        for role in ("main", "pr55")
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "study_class": "development",
        "prior_outcome_access": True,
        "official_benchmark_score": False,
        "source_revisions": {
            "main": MAIN_REVISION,
            "pr55": PR55_REVISION,
        },
        "destination_creation_system_times": list(DESTINATION_CREATION_TIMES),
        "replication_system_time": REPLICATION_SYSTEM_TIME,
        "boolean_outputs": {"numerator": 18, "denominator": 18},
        "paired_revision_differences": {
            "numerator": paired_differences,
            "denominator": paired_rows,
        },
        "outputs_by_role": outputs_by_role,
        "claim_boundary": (
            "Prior-access deterministic development reproduction of one "
            "synthetic event family; not independent confirmation, prevalence, "
            "an official benchmark score, or the PR 56 invalid-input contract."
        ),
    }


def execute(
    *, main_checkout: Path, pr55_checkout: Path, output_dir: Path
) -> dict[str, object]:
    require_exact_clean_checkout(main_checkout, MAIN_REVISION)
    require_exact_clean_checkout(pr55_checkout, PR55_REVISION)
    rows = run_worker(main_checkout, "main", MAIN_REVISION)
    rows += run_worker(pr55_checkout, "pr55", PR55_REVISION)
    require_exact_clean_checkout(main_checkout, MAIN_REVISION)
    require_exact_clean_checkout(pr55_checkout, PR55_REVISION)
    summary = summarize(rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    cells_path = output_dir / "cells.csv"
    with cells_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest_path = output_dir / "artifact_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "cells.csv": sha256_file(cells_path),
                "summary.json": sha256_file(summary_path),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-checkout", type=Path)
    parser.add_argument("--pr55-checkout", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--checkout", type=Path)
    parser.add_argument("--revision-role")
    parser.add_argument("--revision")
    args = parser.parse_args()
    if args.worker:
        if not args.checkout or not args.revision_role or not args.revision:
            parser.error("worker mode requires checkout, revision-role, and revision")
        print(
            json.dumps(
                worker_rows(args.checkout, args.revision_role, args.revision),
                sort_keys=True,
            )
        )
        return 0
    if not args.main_checkout or not args.pr55_checkout or not args.output_dir:
        parser.error("execution requires main-checkout, pr55-checkout, and output-dir")
    print(
        json.dumps(
            execute(
                main_checkout=args.main_checkout,
                pr55_checkout=args.pr55_checkout,
                output_dir=args.output_dir,
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
