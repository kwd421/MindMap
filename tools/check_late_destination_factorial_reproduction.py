from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_REVISION = "c8a3f151b395211643f1b14548bc4fb51e93efc0"
MAIN_REVISION = "069c5f4b16b2f594aec48924161ae8944f39652e"
PR55_REVISION = "2bda2ff38ea79dd0901f6329490d2f9940690261"
ARTIFACT_NAMES = ("cells.csv", "summary.json", "artifact_manifest.json")


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def clone_exact(destination: Path, revision: str) -> None:
    run("git", "clone", "--quiet", "--no-checkout", str(ROOT), str(destination))
    run("git", "fetch", "--quiet", "origin", revision, cwd=destination)
    run("git", "checkout", "--quiet", "--detach", revision, cwd=destination)
    actual = run("git", "rev-parse", "HEAD", cwd=destination).stdout.strip()
    if actual != revision:
        raise RuntimeError(
            f"checkout revision mismatch: expected {revision}, found {actual}"
        )
    status = run(
        "git",
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        cwd=destination,
    ).stdout
    if status:
        raise RuntimeError(f"checkout is dirty: {destination}")


def main() -> int:
    expected_dir = ROOT / "results" / "research" / "EXP-20260828-010"
    with tempfile.TemporaryDirectory(prefix="mindmap-exp010-ci-") as temporary:
        temp_root = Path(temporary)
        runner_checkout = temp_root / "runner"
        main_checkout = temp_root / "main"
        pr55_checkout = temp_root / "pr55"
        output_dir = temp_root / "output"
        clone_exact(runner_checkout, RUNNER_REVISION)
        clone_exact(main_checkout, MAIN_REVISION)
        clone_exact(pr55_checkout, PR55_REVISION)

        completed = run(
            sys.executable,
            str(runner_checkout / "tools" / "run_late_destination_factorial.py"),
            "--main-checkout",
            str(main_checkout),
            "--pr55-checkout",
            str(pr55_checkout),
            "--output-dir",
            str(output_dir),
        )
        summary = json.loads(completed.stdout)
        if summary["boolean_outputs"] != {"numerator": 18, "denominator": 18}:
            raise RuntimeError("unexpected raw Boolean-output denominator")
        if summary["paired_revision_differences"] != {
            "numerator": 0,
            "denominator": 9,
        }:
            raise RuntimeError("unexpected paired revision comparison result")

        for artifact_name in ARTIFACT_NAMES:
            regenerated = (output_dir / artifact_name).read_bytes()
            expected = (expected_dir / artifact_name).read_bytes()
            if regenerated != expected:
                raise RuntimeError(f"EXP-010 artifact drift: {artifact_name}")

        for checkout, revision in (
            (runner_checkout, RUNNER_REVISION),
            (main_checkout, MAIN_REVISION),
            (pr55_checkout, PR55_REVISION),
        ):
            actual = run("git", "rev-parse", "HEAD", cwd=checkout).stdout.strip()
            status = run(
                "git",
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
                cwd=checkout,
            ).stdout
            if actual != revision or status:
                raise RuntimeError(f"checkout changed during reproduction: {checkout}")

    print(
        json.dumps(
            {
                "artifact_byte_matches": {"numerator": 3, "denominator": 3},
                "boolean_outputs": {"numerator": 18, "denominator": 18},
                "paired_revision_differences": {"numerator": 0, "denominator": 9},
                "revisions": {
                    "runner": RUNNER_REVISION,
                    "main": MAIN_REVISION,
                    "pr55": PR55_REVISION,
                },
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
