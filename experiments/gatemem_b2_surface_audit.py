#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from mindmap.track_x.gatemem_baselines import RawLexicalConfig
from mindmap.track_x.gatemem_governance import governance_surface_manifest
from mindmap.track_x.gatemem_governance_safe import FrozenB2GateMemAgent
from mindmap.track_x.gatemem_public import (
    PublicCheckpoint,
    PublicEpisode,
    PublicPrincipal,
    PublicTurn,
)
from mindmap.track_x.gatemem_reader import ExtractiveReaderResult


@dataclass(frozen=True, slots=True)
class AuditCase:
    case_id: str
    turns: tuple[PublicTurn, ...]
    asker_principal_id: str
    asker_role: str
    expected_fact_admitted: bool
    expected_policy_turns_blocked: int
    expected_reader_called: bool
    top_k: int = 5


class AuditReader:
    model_id = "deterministic/b2-surface-audit-reader"
    revision = "0" * 40

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def answer(self, *, question: str, context: str) -> ExtractiveReaderResult:
        self.calls.append((question, context))
        answer = context.split()[0] if context.split() else ""
        return ExtractiveReaderResult(
            answer=answer,
            answer_start=0 if answer else None,
            answer_end=len(answer) if answer else None,
            span_score=1.0 if answer else None,
            null_score=0.0 if answer else None,
            score_margin=1.0 if answer else None,
            diagnostic_probability=0.75 if answer else None,
            window_count=1 if answer else 0,
            input_token_count=len(context.split()),
            forward_calls=1 if answer else 0,
        )


def _episode() -> PublicEpisode:
    return PublicEpisode(
        episode_id="opaque-episode",
        domain="medical",
        principals=(
            PublicPrincipal("opaque-patient", "patient", "Alice"),
            PublicPrincipal("opaque-doctor", "doctor", "Dr. Bob"),
            PublicPrincipal("opaque-nurse", "nurse", "Nurse Eve"),
        ),
    )


def _turn(
    turn_id: str,
    *,
    text: str,
    speaker: str = "opaque-patient",
    role: str = "patient",
) -> PublicTurn:
    return PublicTurn(
        turn_id=turn_id,
        timestamp=f"2026-01-{int(turn_id[-1]) + 1:02d}T00:00:00Z",
        speaker_principal_id=speaker,
        speaker_role=role,
        turn_kind="dialogue",
        text=text,
    )


def _cases() -> tuple[AuditCase, ...]:
    fact = _turn("t1", text="The migraine diagnosis was entered yesterday.")
    unrelated = _turn("t3", text="The follow-up appointment is Friday.")
    return (
        AuditCase(
            "unknown_admit",
            (fact, unrelated),
            "opaque-doctor",
            "doctor",
            True,
            0,
            True,
        ),
        AuditCase(
            "same_speaker_delete",
            (
                fact,
                _turn("t2", text="Please delete the migraine diagnosis record."),
                unrelated,
            ),
            "opaque-doctor",
            "doctor",
            False,
            1,
            True,
        ),
        AuditCase(
            "other_speaker_delete",
            (
                fact,
                _turn(
                    "t2",
                    speaker="opaque-nurse",
                    role="nurse",
                    text="Please delete the migraine diagnosis record.",
                ),
            ),
            "opaque-doctor",
            "doctor",
            True,
            1,
            True,
        ),
        AuditCase(
            "allow_only_target",
            (
                fact,
                _turn("t2", text="Only share the migraine diagnosis with doctors."),
            ),
            "opaque-doctor",
            "doctor",
            True,
            1,
            True,
        ),
        AuditCase(
            "allow_only_other",
            (
                fact,
                _turn("t2", text="Only share the migraine diagnosis with doctors."),
            ),
            "opaque-nurse",
            "nurse",
            False,
            1,
            False,
        ),
        AuditCase(
            "deny_named_role",
            (
                fact,
                _turn("t2", text="Do not share the migraine diagnosis with nurses."),
            ),
            "opaque-nurse",
            "nurse",
            False,
            1,
            False,
        ),
        AuditCase(
            "actor_only_self",
            (
                fact,
                _turn("t2", text="Keep this migraine diagnosis private."),
            ),
            "opaque-patient",
            "patient",
            True,
            1,
            True,
        ),
        AuditCase(
            "actor_only_other",
            (
                fact,
                _turn("t2", text="Keep this migraine diagnosis private."),
            ),
            "opaque-doctor",
            "doctor",
            False,
            1,
            False,
        ),
        AuditCase(
            "no_backfill_after_block",
            (
                _turn("t1", text="Migraine migraine diagnosis: value one."),
                _turn("t2", text="Please delete the migraine diagnosis record."),
                _turn("t3", text="Migraine diagnosis backup: value three."),
            ),
            "opaque-doctor",
            "doctor",
            False,
            1,
            False,
            top_k=2,
        ),
    )


def _run_case(case: AuditCase) -> dict[str, Any]:
    reader = AuditReader()
    agent = FrozenB2GateMemAgent(
        RawLexicalConfig(top_k=case.top_k, max_answer_characters=6000),
        reader,
    )
    agent.reset(_episode())
    for turn in case.turns:
        agent.ingest(turn)
    checkpoint = PublicCheckpoint(
        checkpoint_id="opaque-query",
        episode_id="opaque-episode",
        asker_principal_id=case.asker_principal_id,
        asker_role=case.asker_role,
        query_text="What is the migraine diagnosis?",
    )
    prediction = agent.query(checkpoint)
    audit = prediction["memory_audit"]
    governance = prediction["answer_structured"]["governance"]
    retrieval_ids = tuple(item["turn_id"] for item in audit["retrieval_items"])
    prompt_ids = tuple(prediction["answer_structured"]["prompt_turn_ids"])
    decisions = {item["turn_id"]: item for item in audit["governance_items"]}
    fact_admitted = "t1" in prompt_ids
    policy_turns = {
        signal.source_public_turn_id for signal in agent.governance_signals
    }
    blocked_policy_turns = sum(
        decisions[turn_id]["disposition"] == "block"
        for turn_id in policy_turns
        if turn_id in decisions
    )
    sensitive_in_prompt = "migraine diagnosis was entered" in audit[
        "prompt_context"
    ]["text"].casefold()
    passed = (
        fact_admitted is case.expected_fact_admitted
        and blocked_policy_turns == case.expected_policy_turns_blocked
        and bool(reader.calls) is case.expected_reader_called
        and set(prompt_ids).issubset(set(retrieval_ids))
        and len(retrieval_ids) <= case.top_k
    )
    return {
        "case_id": case.case_id,
        "candidate_count": governance["candidate_count"],
        "admitted_count": governance["admitted_count"],
        "blocked_count": governance["blocked_count"],
        "fact_admitted": fact_admitted,
        "expected_fact_admitted": case.expected_fact_admitted,
        "policy_turn_count": len(policy_turns),
        "blocked_policy_turn_count": blocked_policy_turns,
        "expected_blocked_policy_turn_count": case.expected_policy_turns_blocked,
        "reader_called": bool(reader.calls),
        "expected_reader_called": case.expected_reader_called,
        "sensitive_fact_in_prompt": sensitive_in_prompt,
        "prompt_is_subset_of_candidates": set(prompt_ids).issubset(set(retrieval_ids)),
        "no_candidate_backfill": len(retrieval_ids) <= case.top_k,
        "passed": passed,
    }


def run(output_dir: Path) -> dict[str, Any]:
    rows = [_run_case(case) for case in _cases()]
    manifest = governance_surface_manifest()
    manifest_payload = json.dumps(
        manifest,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    summary = {
        "schema_version": "track-x-gatemem-b2-surface-audit-v0.1",
        "classification": (
            "fixed synthetic pre-outcome information-surface audit; no public "
            "GateMem performance or MindMap effectiveness result"
        ),
        "case_count": len(rows),
        "passed_count": sum(bool(row["passed"]) for row in rows),
        "failed_count": sum(not bool(row["passed"]) for row in rows),
        "surface_manifest_sha256": sha256(manifest_payload).hexdigest(),
        "external_policy_signals_enabled": False,
        "same_b1a_candidates": True,
        "candidate_backfill_after_block": False,
        "rows": rows,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/gatemem_b2_surface_audit_v0_1"),
    )
    args = parser.parse_args()
    summary = run(args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["failed_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
