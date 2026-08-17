#!/usr/bin/env python3
"""Structured collision audit for NCM-Psi v0.2.

This is an oracle/component unit test, not an end-to-end LLM benchmark.
It generates 48 scenarios x 4 decisions and compares six semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import FrozenSet
import csv

CASES = (
    ("identity_fork", "report", "accepted"),
    ("identity_fork", "report", "rejected"),
    ("identity_fork", "report", "doubted"),
    ("identity_fork", "state_replication", "accepted"),
    ("operational_replica", "report", "accepted"),
    ("operational_replica", "state_replication", "accepted"),
)
POLICIES = ("public", "private_then_shared", "shared_then_revoked", "source_deleted")
SUPPORTS = ("protected_only", "independent_public")
SYSTEMS = (
    "BranchPrincipalACL",
    "AttributedTransfer",
    "TransferAdoption",
    "LineageNoAltSupport",
    "AltSupportNoLineage",
    "NCM-Psi-v0.2",
)


@dataclass(frozen=True)
class Scenario:
    sid: str
    lineage: str
    transfer: str
    stance: str
    policy: str
    support: str


def scenarios() -> list[Scenario]:
    out: list[Scenario] = []
    i = 0
    for lineage, transfer, stance in CASES:
        for policy in POLICIES:
            for support in SUPPORTS:
                i += 1
                out.append(Scenario(f"ca-{i:03d}", lineage, transfer, stance, policy, support))
    assert len(out) == 48
    return out


def allow(s: Scenario) -> bool:
    return s.policy in {"public", "private_then_shared"} or s.support == "independent_public"


def flat_allow(s: Scenario) -> bool:
    return s.policy in {"public", "private_then_shared"}


def gold(s: Scenario) -> dict[str, FrozenSet[str]]:
    belief = {"accepted": "believes_phi", "rejected": "rejects_phi", "doubted": "doubts_phi"}[s.stance]
    first = (
        "first_person"
        if s.lineage == "operational_replica" and s.transfer == "state_replication"
        else "attributed_to_source"
    )
    disclose = "allow" if allow(s) else "deny"
    if not allow(s):
        provenance = frozenset({"withhold"})
    elif s.policy in {"shared_then_revoked", "source_deleted"} and s.support == "independent_public":
        provenance = frozenset({"public_independent"})
    else:
        transfer_path = (
            "replicated_self_state"
            if s.lineage == "operational_replica" and s.transfer == "state_replication"
            else "source_transfer"
        )
        provenance = frozenset({transfer_path, "public_independent"}) if s.support == "independent_public" else frozenset({transfer_path})
    return {
        "destination_belief": frozenset({belief}),
        "first_person_attribution": frozenset({first}),
        "disclosure": frozenset({disclose}),
        "provenance": provenance,
    }


def stance(s: Scenario) -> str:
    return {"accepted": "believes_phi", "rejected": "rejects_phi", "doubted": "doubts_phi"}[s.stance]


def first_no_lineage(s: Scenario) -> str:
    return "first_person" if s.transfer == "state_replication" else "attributed_to_source"


def first_with_lineage(s: Scenario) -> str:
    return (
        "first_person"
        if s.lineage == "operational_replica" and s.transfer == "state_replication"
        else "attributed_to_source"
    )


def flat_provenance(s: Scenario, lineage_aware: bool) -> str:
    if not flat_allow(s):
        return "withhold"
    if lineage_aware:
        return "replicated_self_state" if first_with_lineage(s) == "first_person" else "source_transfer"
    return "replicated_self_state" if s.transfer == "state_replication" else "source_transfer"


def support_provenance(s: Scenario, lineage_aware: bool) -> str:
    if not allow(s):
        return "withhold"
    if s.policy in {"shared_then_revoked", "source_deleted"} and s.support == "independent_public":
        return "public_independent"
    if lineage_aware:
        return "replicated_self_state" if first_with_lineage(s) == "first_person" else "source_transfer"
    return "replicated_self_state" if s.transfer == "state_replication" else "source_transfer"


def predict(system: str, s: Scenario, category: str) -> str:
    if system == "BranchPrincipalACL":
        return {
            "destination_belief": "believes_phi",
            "first_person_attribution": "first_person",
            "disclosure": "allow",
            "provenance": "self_memory",
        }[category]
    if system == "AttributedTransfer":
        return {
            "destination_belief": "believes_phi",
            "first_person_attribution": first_no_lineage(s),
            "disclosure": "allow" if flat_allow(s) else "deny",
            "provenance": flat_provenance(s, False),
        }[category]
    if system == "TransferAdoption":
        return {
            "destination_belief": stance(s),
            "first_person_attribution": first_no_lineage(s),
            "disclosure": "allow" if flat_allow(s) else "deny",
            "provenance": flat_provenance(s, False),
        }[category]
    if system == "LineageNoAltSupport":
        return {
            "destination_belief": stance(s),
            "first_person_attribution": first_with_lineage(s),
            "disclosure": "allow" if flat_allow(s) else "deny",
            "provenance": flat_provenance(s, True),
        }[category]
    if system == "AltSupportNoLineage":
        return {
            "destination_belief": stance(s),
            "first_person_attribution": first_no_lineage(s),
            "disclosure": "allow" if allow(s) else "deny",
            "provenance": support_provenance(s, False),
        }[category]
    if system == "NCM-Psi-v0.2":
        return {
            "destination_belief": stance(s),
            "first_person_attribution": first_with_lineage(s),
            "disclosure": "allow" if allow(s) else "deny",
            "provenance": support_provenance(s, True),
        }[category]
    raise ValueError(system)


def main() -> None:
    rows: list[dict[str, object]] = []
    for s in scenarios():
        expected = gold(s)
        for category, acceptable in expected.items():
            for system in SYSTEMS:
                pred = predict(system, s, category)
                rows.append({
                    "scenario_id": s.sid,
                    "lineage": s.lineage,
                    "transfer": s.transfer,
                    "stance": s.stance,
                    "policy": s.policy,
                    "support": s.support,
                    "category": category,
                    "system": system,
                    "prediction": pred,
                    "acceptable": "|".join(sorted(acceptable)),
                    "correct": int(pred in acceptable),
                })

    out = Path("collision_audit_outputs")
    out.mkdir(exist_ok=True)
    with (out / "decision_level_results.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary: list[dict[str, object]] = []
    for system in SYSTEMS:
        sr = [r for r in rows if r["system"] == system]
        scenario_scores = []
        for sid in sorted({str(r["scenario_id"]) for r in sr}):
            values = [int(r["correct"]) for r in sr if r["scenario_id"] == sid]
            scenario_scores.append(int(all(values)))
        summary.append({
            "system": system,
            "decision_accuracy": sum(int(r["correct"]) for r in sr) / len(sr),
            "scenario_all_correct": sum(scenario_scores) / len(scenario_scores),
        })

    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    for row in sorted(summary, key=lambda x: float(x["decision_accuracy"]), reverse=True):
        print(f"{row['system']:24s} accuracy={row['decision_accuracy']:.6f} all_correct={row['scenario_all_correct']:.6f}")


if __name__ == "__main__":
    main()
