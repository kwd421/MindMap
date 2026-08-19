from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from mindmap.track_x.gatemem_baselines import AlwaysNoMemoryGateMemAgent
from mindmap.track_x.gatemem_official import (
    GateMemOfficialError,
    git_revision,
    load_jsonl,
    run_external_gatemem,
    verify_gatemem_checkout,
)


_SECRET = b"official-harness-test-secret-000001"


def _run(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _fake_checkout(tmp_path: Path) -> tuple[Path, str]:
    checkout = tmp_path / "GateMem"
    data_dir = checkout / "bench" / "data" / "medical"
    scripts_dir = checkout / "bench" / "scripts"
    scripts_dir.mkdir(parents=True)

    episodes = [
        {
            "episode_id": "medical_episode_source_001",
            "domain": "medical",
            "entities": {
                "principals": [
                    {
                        "principal_id": "patient_source_001",
                        "role": "patient",
                    },
                ],
                "relationships": [
                    {
                        "patient_id": "patient_source_001",
                        "access_level": "HIDDEN_RELATIONSHIP_POLICY",
                    }
                ],
            },
            "turns": [
                {
                    "turn_id": "medical_turn_source_001",
                    "speaker": {
                        "principal_id": "patient_source_001",
                        "role": "patient",
                    },
                    "text": "DO_NOT_COPY_SOURCE_TEXT",
                    "record_refs": ["gold-record"],
                }
            ],
            "records": [
                {"record_id": "gold-record", "canonical_values": ["secret"]}
            ],
        }
    ]
    checkpoints = [
        {
            "checkpoint_id": "medical_checkpoint_source_001",
            "episode_id": "medical_episode_source_001",
            "as_of_turn_id": "medical_turn_source_001",
            "asker": {
                "principal_id": "patient_source_001",
                "role": "patient",
            },
            "query_text": "What do you remember?",
            "query_type": "utility",
            "expected_action": "answer",
            "judge_spec": {"include": ["secret"]},
            "leak_targets": [],
        }
    ]
    _write_jsonl(data_dir / "episodes.jsonl", episodes)
    _write_jsonl(data_dir / "checkpoints.jsonl", checkpoints)

    scorer = r'''
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--data_dir", required=True)
parser.add_argument("--predictions", required=True)
parser.add_argument("--out_dir", required=True)
parser.add_argument("--gate_by_action", action="store_true")
args = parser.parse_args()

rows = [json.loads(line) for line in Path(args.predictions).read_text(encoding="utf-8").splitlines() if line.strip()]
assert all(set(row) == {"checkpoint_id", "output"} for row in rows)
out = Path(args.out_dir)
out.mkdir(parents=True, exist_ok=True)
(out / "summary.json").write_text(
    json.dumps({"n_predictions": len(rows), "gate_by_action": args.gate_by_action}),
    encoding="utf-8",
)
'''
    (scripts_dir / "score_predictions.py").write_text(scorer, encoding="utf-8")

    _run(["git", "init", "-q"], checkout)
    _run(["git", "config", "user.name", "Track X Test"], checkout)
    _run(["git", "config", "user.email", "track-x@example.invalid"], checkout)
    _run(["git", "add", "."], checkout)
    _run(["git", "commit", "-q", "-m", "fixture"], checkout)
    return checkout, git_revision(checkout)


def test_jsonl_loader_rejects_non_object_rows(tmp_path: Path):
    path = tmp_path / "bad.jsonl"
    path.write_text("[1,2,3]\n", encoding="utf-8")
    with pytest.raises(GateMemOfficialError, match="expected JSON object"):
        load_jsonl(path)


def test_checkout_verification_pins_revision_and_detects_tracked_dirt(
    tmp_path: Path,
):
    checkout, revision = _fake_checkout(tmp_path)
    audit = verify_gatemem_checkout(
        checkout,
        domain="medical",
        expected_commit=revision,
    )
    assert audit.observed_commit == revision
    assert audit.dirty is False
    assert len(audit.scorer_sha256) == 64

    with pytest.raises(GateMemOfficialError, match="revision mismatch"):
        verify_gatemem_checkout(
            checkout,
            domain="medical",
            expected_commit="0" * 40,
        )

    scorer = checkout / "bench" / "scripts" / "score_predictions.py"
    scorer.write_text(
        scorer.read_text(encoding="utf-8") + "\n# dirty\n",
        encoding="utf-8",
    )
    with pytest.raises(GateMemOfficialError, match="tracked modifications"):
        verify_gatemem_checkout(
            checkout,
            domain="medical",
            expected_commit=revision,
        )


def test_external_harness_runs_opaque_method_and_unmodified_official_scorer(
    tmp_path: Path,
):
    checkout, revision = _fake_checkout(tmp_path)
    output = tmp_path / "result"
    result = run_external_gatemem(
        checkout=checkout,
        domain="medical",
        output_dir=output,
        agent_factory=AlwaysNoMemoryGateMemAgent,
        method_name="always_no_memory",
        method_config={},
        expected_commit=revision,
        invoke_official_scorer=True,
        scorer_python=sys.executable,
        repository_revision="mindmap-test-sha",
        opaque_id_secret=_SECRET,
    )

    assert result.prediction_count == 1
    assert result.official_score is not None
    assert result.official_score.summary == {
        "n_predictions": 1,
        "gate_by_action": False,
    }
    prediction = json.loads(
        (output / "predictions.jsonl").read_text(encoding="utf-8")
    )
    assert prediction["checkpoint_id"] == "medical_checkpoint_source_001"
    assert prediction["output"]["action"] == "no_memory"
    assert "checkpoint_id" not in prediction["output"].get("memory_audit", {})

    metadata = json.loads(
        (output / "run_metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["schema_version"] == "track-x-gatemem-external-run-v0.2"
    assert metadata["repository_revision"] == "mindmap-test-sha"
    assert metadata["checkout"]["observed_commit"] == revision
    assert metadata["counts"]["checkpoints"] == 1
    assert metadata["artifact_sha256"]["predictions.jsonl"]
    firewall = metadata["opaque_identity_firewall"]
    assert firewall["enabled"] is True
    assert firewall["mapping_serialized"] is False
    assert len(firewall["key_commitment_sha256"]) == 64
    assert len(firewall["mapping_commitment_sha256"]) == 64
    assert firewall["mapping_count"] >= 4
    assert metadata["boundary"]["source_identifiers_passed_to_method"] is False
    assert metadata["boundary"]["source_as_of_turn_id_passed_to_method"] is False
    assert metadata["boundary"]["relationships_passed_to_method"] is False

    # Source text, gold records, relationship-policy labels, and the mapping are
    # not copied into the all-no-memory method/scorer bundle. Evaluator-owned
    # audit files may retain source IDs needed to identify benchmark rows.
    result_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in output.rglob("*")
        if path.is_file()
    )
    assert "DO_NOT_COPY_SOURCE_TEXT" not in result_text
    assert "gold-record" not in result_text
    assert "canonical_values" not in result_text
    assert "HIDDEN_RELATIONSHIP_POLICY" not in result_text
    assert "source_to_method" not in result_text
    assert "patient_source_001" not in prediction["output"].get("answer", "")
