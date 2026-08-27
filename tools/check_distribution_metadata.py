#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from mindmap.distribution_contract import verify_distributions, write_sha256_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify MindMap wheel/sdist metadata and license content.")
    parser.add_argument("--dist-dir", type=Path, default=Path("dist"))
    parser.add_argument("--sha256-manifest", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = verify_distributions(args.dist_dir)
    print(report.render())
    if args.sha256_manifest is not None:
        write_sha256_manifest(report, args.sha256_manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
