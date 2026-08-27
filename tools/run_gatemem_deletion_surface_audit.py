from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


EXTRACTION_RULE_VERSION = "strict-sentence-imperative-v1"
_SENTENCE_DIRECTIVE_RE = re.compile(
    r"(?:^|[.!?]\s+)(?:please\s+)?(?:delete|remove|erase|forget)\b",
    flags=re.IGNORECASE,
)
_LABELLED_DIRECTIVE_RE = re.compile(
    r"^deletion\s+request(?:\s+[^:]{0,80})?:\s*"
    r"(?:please\s+)?(?:delete|remove|erase|forget)\b",
    flags=re.IGNORECASE,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strict_directive(text: str) -> bool:
    """Select only explicit sentence-initial deletion imperatives.

    This deterministic high-precision rule deliberately excludes descriptive
    reminders ("the value is deleted"), morphological lookalikes ("removes
    auto-renewal"), and indirect requests. It is a development diagnostic, not
    a semantic gold label for every deletion speech act in GateMem.
    """

    normalized = text.strip()
    return bool(
        _SENTENCE_DIRECTIVE_RE.search(normalized)
        or _LABELLED_DIRECTIVE_RE.search(normalized)
    )


def git_revision(path: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git rev-parse failed")
    return completed.stdout.strip()


def require_revision(path: Path, expected: str, label: str) -> None:
    actual = git_revision(path)
    if actual != expected:
        raise RuntimeError(f"{label} revision mismatch: expected {expected}, got {actual}")


def load_mindmap_api(checkout: Path) -> dict[str, Any]:
    source_root = checkout / "src"
    if not source_root.is_dir():
        raise RuntimeError(f"MindMap source directory is absent: {source_root}")
    sys.path.insert(0, str(source_root))
    for name in tuple(sys.modules):
        if name == "mindmap" or name.startswith("mindmap."):
            del sys.modules[name]
    safe = importlib.import_module("mindmap.track_x.gatemem_governance_safe")
    public = importlib.import_module("mindmap.track_x.gatemem_public")
    governance = importlib.import_module("mindmap.track_x.gatemem_governance")
    return {
        "Parser": safe.FrozenPublicTurnPolicyParser,
        "manifest": safe.deletion_capability_manifest(),
        "PublicEpisode": public.PublicEpisode,
        "PublicPrincipal": public.PublicPrincipal,
        "PublicTurn": public.PublicTurn,
        "SignalOperation": governance.SignalOperation,
    }


def information_referent_regex(referents: list[str]) -> re.Pattern[str]:
    alternatives = "|".join(re.escape(item) for item in referents)
    return re.compile(rf"\b(?:{alternatives})\b", flags=re.IGNORECASE)


def audit(
    *,
    gatemem_checkout: Path,
    mindmap_checkout: Path,
    expected_gatemem_revision: str,
    expected_mindmap_revision: str,
    output_dir: Path,
) -> dict[str, Any]:
    require_revision(gatemem_checkout, expected_gatemem_revision, "GateMem")
    require_revision(mindmap_checkout, expected_mindmap_revision, "MindMap")
    api = load_mindmap_api(mindmap_checkout)
    manifest = api["manifest"]
    referents = list(manifest["information_referents"])
    referent_re = information_referent_regex(referents)
    delete_operation = api["SignalOperation"].DELETE

    data_files = sorted((gatemem_checkout / "bench" / "data").glob("*/episodes.jsonl"))
    if len(data_files) != 4:
        raise RuntimeError(f"expected four GateMem episode files, found {len(data_files)}")

    all_turn_count = 0
    episode_count = 0
    rows: list[dict[str, Any]] = []
    for data_file in data_files:
        domain = data_file.parent.name
        with data_file.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                raw = json.loads(line)
                episode_count += 1
                episode_id = raw["episode_id"]
                principals = tuple(
                    api["PublicPrincipal"](
                        principal_id=item["principal_id"],
                        role=item["role"],
                        display_name=item.get("display_name"),
                    )
                    for item in raw["entities"]["principals"]
                )
                episode = api["PublicEpisode"](
                    episode_id=episode_id,
                    domain=domain,
                    principals=principals,
                )
                parser = api["Parser"](episode)
                for observed_index, item in enumerate(raw["turns"]):
                    all_turn_count += 1
                    text = item["text"]
                    if not strict_directive(text):
                        continue
                    speaker = item["speaker"]
                    turn = api["PublicTurn"](
                        turn_id=item["turn_id"],
                        timestamp=item.get("timestamp"),
                        speaker_principal_id=speaker["principal_id"],
                        speaker_role=speaker["role"],
                        turn_kind=item.get("turn_kind", "dialogue"),
                        text=text,
                    )
                    signals = parser.parse(turn, observed_index=observed_index)
                    delete_signals = [
                        signal for signal in signals if signal.operation is delete_operation
                    ]
                    rows.append(
                        {
                            "domain": domain,
                            "episode_id": episode_id,
                            "turn_id": item["turn_id"],
                            "source_line": line_number,
                            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                            "information_referent_present": bool(referent_re.search(text)),
                            "delete_signal_count": len(delete_signals),
                            "all_signal_operations": ";".join(
                                signal.operation.value for signal in signals
                            ),
                        }
                    )

    if not rows:
        raise RuntimeError("strict directive extraction returned no rows")

    output_dir.mkdir(parents=True, exist_ok=True)
    rows_path = output_dir / "turn_results.csv"
    fieldnames = list(rows[0])
    with rows_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    detected = sum(row["delete_signal_count"] > 0 for row in rows)
    with_referent = sum(row["information_referent_present"] for row in rows)
    without_referent = total - with_referent
    detected_without_referent = sum(
        row["delete_signal_count"] > 0
        and not row["information_referent_present"]
        for row in rows
    )
    per_domain: dict[str, dict[str, int]] = {}
    for domain in sorted({row["domain"] for row in rows}):
        domain_rows = [row for row in rows if row["domain"] == domain]
        per_domain[domain] = {
            "strict_directive_turns": len(domain_rows),
            "delete_signals": sum(
                row["delete_signal_count"] > 0 for row in domain_rows
            ),
            "information_referent_present": sum(
                row["information_referent_present"] for row in domain_rows
            ),
        }

    summary = {
        "schema_version": "gatemem-deletion-surface-audit-v1",
        "study_class": "development",
        "official_benchmark_score": False,
        "extraction_rule_version": EXTRACTION_RULE_VERSION,
        "gatemem_revision": expected_gatemem_revision,
        "mindmap_revision": expected_mindmap_revision,
        "capability_manifest": manifest,
        "dataset": {
            "episode_files": [
                {
                    "path": str(path.relative_to(gatemem_checkout)),
                    "sha256": sha256_file(path),
                }
                for path in data_files
            ],
            "episodes": episode_count,
            "turns": all_turn_count,
        },
        "results": {
            "strict_directive_delete_signal": {
                "numerator": detected,
                "denominator": total,
            },
            "information_referent_present": {
                "numerator": with_referent,
                "denominator": total,
            },
            "referent_absent_delete_signal": {
                "numerator": detected_without_referent,
                "denominator": without_referent,
            },
            "unique_text_sha256": len({row["text_sha256"] for row in rows}),
            "per_domain": per_domain,
        },
        "selection_boundary": (
            "Deterministic sentence-initial imperatives only; not a semantic gold "
            "label, full deletion-speech recall estimate, or GateMem score."
        ),
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest_path = output_dir / "artifact_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "summary.json": sha256_file(summary_path),
                "turn_results.csv": sha256_file(rows_path),
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
    parser.add_argument("--gatemem-checkout", type=Path, required=True)
    parser.add_argument("--mindmap-checkout", type=Path, required=True)
    parser.add_argument("--expected-gatemem-revision", required=True)
    parser.add_argument("--expected-mindmap-revision", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = audit(**vars(args))
    print(json.dumps(summary["results"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
