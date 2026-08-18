#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from mindmap.track_x.v02_authorship import validate_authorship_note
from mindmap.track_x.v02_bundles import load_bundle_json


_ALLOWED_PATHS = {
    "data/track_x_v02/heldout/session_a.json",
    "data/track_x_v02/heldout/AUTHORSHIP.md",
}


def _git(repository_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repository_root,
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout.strip()


def validate_contribution(
    repository_root: Path,
    *,
    base_ref: str,
) -> dict[str, object]:
    base_sha = _git(repository_root, "rev-parse", base_ref)
    head_sha = _git(repository_root, "rev-parse", "HEAD")
    changed = {
        line.strip()
        for line in _git(
            repository_root,
            "diff",
            "--name-only",
            f"{base_sha}...{head_sha}",
        ).splitlines()
        if line.strip()
    }
    if changed != _ALLOWED_PATHS:
        unexpected = sorted(changed - _ALLOWED_PATHS)
        missing = sorted(_ALLOWED_PATHS - changed)
        raise ValueError(
            "held-out contribution path isolation failed; "
            f"unexpected={unexpected}, missing={missing}"
        )

    heldout_root = repository_root / "data" / "track_x_v02" / "heldout"
    declaration = validate_authorship_note(
        heldout_root / "AUTHORSHIP.md",
        expected_base_commit=base_sha,
    )
    bundles = load_bundle_json(
        heldout_root / "session_a.json",
        split="heldout",
    )
    return {
        "base_sha": base_sha,
        "head_sha": head_sha,
        "changed_paths": sorted(changed),
        "heldout_branch": declaration.heldout_branch,
        "n_bundles": len(bundles),
        "topology_families": sorted(
            bundle.topology_family for bundle in bundles
        ),
        "status": "valid isolated Session A held-out contribution",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the Track X v0.2 Session A held-out-only commit."
    )
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--base-ref", required=True)
    args = parser.parse_args()
    result = validate_contribution(
        args.repository_root.resolve(),
        base_ref=args.base_ref,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
