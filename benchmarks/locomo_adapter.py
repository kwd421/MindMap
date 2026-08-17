#!/usr/bin/env python3
"""Schema-inspecting LoCoMo adapter.

The official dataset is not vendored. Place `locomo10.json` under
`benchmarks/data/` or pass an explicit path. No silent download is performed so
provenance and checksum remain auditable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_dialogue_turns(record: dict[str, Any]) -> Iterable[dict[str, Any]]:
    # Official LoCoMo releases have appeared in more than one layout.
    if "dialog_index" in record:
        yield from record["dialog_index"].values()
        return
    conversation = record.get("conversation", record)
    for key, value in conversation.items():
        if str(key).startswith("session_") and isinstance(value, list):
            yield from value


def inspect_dataset(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Expected a top-level JSON list")
    turns = 0
    questions = 0
    for record in data:
        turns += sum(1 for _ in iter_dialogue_turns(record))
        questions += len(record.get("qa", record.get("questions", [])))
    return {
        "path": str(path),
        "sha256": sha256(path),
        "conversations": len(data),
        "turns": turns,
        "questions": questions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=Path("benchmarks/data/locomo10.json"),
    )
    args = parser.parse_args()
    if not args.path.exists():
        raise SystemExit(
            f"Dataset not found: {args.path}\n"
            "Place the official LoCoMo file there and verify redistribution terms."
        )
    print(json.dumps(inspect_dataset(args.path), indent=2))


if __name__ == "__main__":
    main()
