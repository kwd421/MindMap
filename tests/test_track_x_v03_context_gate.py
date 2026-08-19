from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from mindmap.track_x.v03_context_gate import (
    ContextGateTreatment,
    evaluate_development_context_gate,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _summary(
    summary: dict[str, object],
    treatment: ContextGateTreatment,
    architecture: str,
) -> dict[str, object]:
    summaries = summary["summaries"]
    assert isinstance(summaries, dict)
    value = summaries[f"{treatment.value}:{architecture}"]
    assert isinstance(value, dict)
    return value


def test_context_gate_p0_has_frozen_development_surface_and_no_g_t_disagreement():
    rows, summary = evaluate_development_context_gate(REPOSITORY_ROOT)

    assert summary["classification"] == (
        "fixed deterministic development-only mechanism audit; no held-out "
        "or public-benchmark claim"
    )
    assert summary["n_passages"] == 42
    assert summary["n_topologies"] == 7
    assert summary["n_rows"] == 420
    assert len(rows) == 420
    assert summary["generic_typed_disagreements"] == []

    assert {row.architecture for row in rows} == {"G_generic", "T_typed"}
    assert {row.treatment for row in rows} == {
        treatment.value for treatment in ContextGateTreatment
    }
    assert {row.condition for row in rows} == {
        "clean",
        "field_corruption",
        "candidate_omitted",
        "raw_unavailable",
        "ambiguous_raw",
        "misleading_context",
    }


def test_controlled_context_gate_removes_unsupported_and_ineligible_prompt_exposure():
    rows, summary = evaluate_development_context_gate(REPOSITORY_ROOT)

    for architecture in ("G_generic", "T_typed"):
        passthrough = _summary(
            summary,
            ContextGateTreatment.CONTROLLED_PASSTHROUGH,
            architecture,
        )
        gated = _summary(
            summary,
            ContextGateTreatment.CONTROLLED_VERIFIED_GATE,
            architecture,
        )

        assert passthrough["n"] == 42
        assert passthrough["candidate_presence_rate"] == pytest.approx(5 / 6)
        assert passthrough["candidate_exact_rate"] == pytest.approx(1 / 6)
        assert passthrough["prompt_coverage"] == pytest.approx(5 / 6)
        assert passthrough["prompt_exact_rate"] == pytest.approx(1 / 6)
        assert passthrough["prompt_conditional_risk"] == pytest.approx(4 / 5)
        assert passthrough["unsupported_prompt_exposure_rate"] == pytest.approx(2 / 3)
        assert passthrough["ineligible_prompt_exposure_rate"] == pytest.approx(1 / 3)
        assert passthrough["ineligible_prompt_exposure_conditional"] == 1.0
        assert passthrough["permitted_prompt_recall"] == pytest.approx(1 / 4)
        assert passthrough["abstention_rate"] == 0.0

        assert gated["n"] == 42
        assert gated["candidate_presence_rate"] == pytest.approx(5 / 6)
        assert gated["candidate_exact_rate"] == pytest.approx(1 / 6)
        assert gated["prompt_coverage"] == pytest.approx(2 / 3)
        assert gated["prompt_exact_rate"] == pytest.approx(2 / 3)
        assert gated["prompt_conditional_risk"] == 0.0
        assert gated["unsupported_prompt_exposure_rate"] == 0.0
        assert gated["ineligible_prompt_exposure_rate"] == 0.0
        assert gated["ineligible_prompt_exposure_conditional"] == 0.0
        assert gated["permitted_prompt_recall"] == 1.0
        assert gated["gate_recovery_rate_on_candidate_errors"] == pytest.approx(3 / 5)
        assert gated["gate_block_rate_on_candidate_errors"] == pytest.approx(2 / 5)
        assert gated["abstention_rate"] == pytest.approx(1 / 3)
        assert gated["clean_false_intervention_rate"] == 0.0

    controlled_rows = [
        row
        for row in rows
        if row.architecture == "G_generic"
        and row.treatment
        == ContextGateTreatment.CONTROLLED_VERIFIED_GATE.value
    ]
    assert sum(row.gate_recovered_candidate_error for row in controlled_rows) == 21
    assert sum(row.gate_blocked_candidate_error for row in controlled_rows) == 14
    assert sum(row.unsupported_prompt_exposure for row in controlled_rows) == 0
    assert sum(row.ineligible_prompt_exposure for row in controlled_rows) == 0


def test_primary_path_is_a_development_null_and_oracle_uses_ineligible_evidence():
    _rows, summary = evaluate_development_context_gate(REPOSITORY_ROOT)

    for architecture in ("G_generic", "T_typed"):
        primary = _summary(
            summary,
            ContextGateTreatment.PRIMARY_PASSTHROUGH,
            architecture,
        )
        primary_gate = _summary(
            summary,
            ContextGateTreatment.PRIMARY_VERIFIED_GATE,
            architecture,
        )
        oracle = _summary(
            summary,
            ContextGateTreatment.ORACLE_CONTEXT_CEILING,
            architecture,
        )

        for value in (primary, primary_gate):
            assert value["candidate_presence_rate"] == pytest.approx(2 / 3)
            assert value["candidate_exact_rate"] == pytest.approx(2 / 3)
            assert value["prompt_coverage"] == pytest.approx(2 / 3)
            assert value["prompt_exact_rate"] == pytest.approx(2 / 3)
            assert value["prompt_conditional_risk"] == 0.0
            assert value["unsupported_prompt_exposure_rate"] == 0.0
            assert value["ineligible_prompt_exposure_rate"] == 0.0
            assert value["permitted_prompt_recall"] == 1.0
            assert value["abstention_rate"] == pytest.approx(1 / 3)

        assert primary["answer_accuracy"] == primary_gate["answer_accuracy"]
        assert primary["silent_wrong_use_rate"] == primary_gate["silent_wrong_use_rate"]
        assert primary["unsafe_disclosure_rate"] == primary_gate["unsafe_disclosure_rate"]

        assert oracle["candidate_presence_rate"] == 1.0
        assert oracle["candidate_exact_rate"] == 1.0
        assert oracle["prompt_coverage"] == 1.0
        assert oracle["prompt_exact_rate"] == 1.0
        assert oracle["unsupported_prompt_exposure_rate"] == 0.0
        assert oracle["ineligible_prompt_exposure_rate"] == pytest.approx(1 / 3)
        assert oracle["ineligible_prompt_exposure_conditional"] == 1.0
        assert oracle["permitted_prompt_recall"] == 1.0
        assert oracle["abstention_rate"] == 0.0


def test_condition_level_prompt_counts_match_the_declared_mechanism():
    rows, _summary_value = evaluate_development_context_gate(REPOSITORY_ROOT)
    rows = [row for row in rows if row.architecture == "G_generic"]

    controlled_passthrough = [
        row
        for row in rows
        if row.treatment
        == ContextGateTreatment.CONTROLLED_PASSTHROUGH.value
    ]
    controlled_gate = [
        row
        for row in rows
        if row.treatment
        == ContextGateTreatment.CONTROLLED_VERIFIED_GATE.value
    ]

    assert sum(row.unsupported_prompt_exposure for row in controlled_passthrough) == 28
    assert sum(row.raw_unavailable_prompt_exposure for row in controlled_passthrough) == 7
    assert sum(row.ambiguous_prompt_exposure for row in controlled_passthrough) == 7
    assert sum(
        row.misleading_context_prompt_exposure for row in controlled_passthrough
    ) == 7

    assert sum(row.prompt_event_exact for row in controlled_gate) == 28
    assert sum(row.method_abstained for row in controlled_gate) == 14
    assert sum(row.clean_false_intervention for row in controlled_gate) == 0


def _run_cli(output_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(REPOSITORY_ROOT / "experiments" / "track_x_v03_context_gate_p0.py"),
            "--repository-root",
            str(REPOSITORY_ROOT),
            "--output-dir",
            str(output_dir),
        ],
        cwd=REPOSITORY_ROOT,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_runner_writes_deterministic_artifacts_without_reading_heldout(tmp_path: Path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_run = _run_cli(first)
    second_run = _run_cli(second)

    assert first_run.returncode == 0, first_run.stderr
    assert second_run.returncode == 0, second_run.stderr
    assert json.loads(first_run.stdout) == json.loads(second_run.stdout)
    assert (first / "rows.csv").read_bytes() == (second / "rows.csv").read_bytes()
    assert (first / "summary.json").read_bytes() == (second / "summary.json").read_bytes()
    assert (first / "run_metadata.json").read_bytes() == (
        second / "run_metadata.json"
    ).read_bytes()

    metadata = json.loads((first / "run_metadata.json").read_text(encoding="utf-8"))
    assert metadata["heldout_read"] is False
    assert metadata["base_freeze_commit"] == (
        "b7faf750df7f9db018b97ec224b0c83142c4efe4"
    )
    assert metadata["row_count"] == 420
    assert set(metadata["artifact_sha256"]) == {"rows.csv", "summary.json"}
