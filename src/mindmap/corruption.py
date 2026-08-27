from __future__ import annotations

import random
from dataclasses import replace

from .core import Scenario


CORRUPTION_MODES = (
    "identity_collapse",
    "fork_cutoff_shift",
    "world_mind_branch_swap",
    "exposure_source_swap",
    "attitude_laundering",
    "policy_declassification",
    "restore_parent_error",
    "temporal_scope_shift",
    "speaker_or_holder_swap",
)


def clone_scenario(scenario: Scenario, **changes: object) -> Scenario:
    data = {
        "scenario_id": scenario.scenario_id,
        "template": scenario.template,
        "seed": scenario.seed,
        "evidence": list(scenario.evidence),
        "claims": list(scenario.claims),
        "exposures": list(scenario.exposures),
        "minds": list(scenario.minds),
        "branches": list(scenario.branches),
        "queries": list(scenario.queries),
        "metadata": dict(scenario.metadata),
    }
    data.update(changes)
    return Scenario(**data)


def _sibling_pairs(scenario: Scenario) -> list[tuple[str, str]]:
    groups: dict[tuple[str, str | None], list[str]] = {}
    for mind in scenario.minds:
        groups.setdefault((mind.character_identity_id, mind.parent_mind_instance_id), []).append(mind.mind_instance_id)
    pairs: list[tuple[str, str]] = []
    for ids in groups.values():
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                pairs.append((ids[i], ids[j]))
    return pairs


def corrupt_scenario(scenario: Scenario, mode: str, rr: random.Random) -> Scenario:
    """Apply one joint corruption mode to a structured event hypothesis.

    Modes intentionally mutate dependent fields together. This is not an
    independent field-dropout model.
    """
    if mode not in CORRUPTION_MODES:
        raise ValueError(f"unknown corruption mode: {mode}")

    evidence = list(scenario.evidence)
    claims = list(scenario.claims)
    exposures = list(scenario.exposures)
    minds = list(scenario.minds)
    metadata = dict(scenario.metadata)
    metadata["corruption_mode"] = mode
    pairs = _sibling_pairs(scenario)

    if mode == "identity_collapse":
        if pairs:
            source, victim = rr.choice(pairs)
            changed = False
            new_exposures = []
            for exposure in exposures:
                if exposure.mind_instance_id == source and exposure.recorded_at > 10 and rr.random() < 0.8:
                    new_exposures.append(replace(exposure, mind_instance_id=victim))
                    changed = True
                else:
                    new_exposures.append(exposure)
            exposures = new_exposures
            new_claims = []
            for claim in claims:
                if claim.holder_mind_instance_id == source and claim.recorded_at > 10 and rr.random() < 0.8:
                    new_claims.append(replace(claim, holder_mind_instance_id=victim))
                    changed = True
                else:
                    new_claims.append(claim)
            claims = new_claims
            metadata["corruption_effective"] = str(changed)

    elif mode == "fork_cutoff_shift":
        candidates = [m for m in minds if m.parent_mind_instance_id is not None and m.inherited_through_tx is not None]
        if candidates:
            target = rr.choice(candidates)
            shift = rr.choice([8, 12, 20])
            minds = [
                replace(m, inherited_through_tx=(m.inherited_through_tx or 0) + shift)
                if m.mind_instance_id == target.mind_instance_id else m
                for m in minds
            ]
            metadata["corruption_target"] = target.mind_instance_id

    elif mode == "world_mind_branch_swap":
        branch_ids = {b.world_branch_id for b in scenario.branches}
        if len(branch_ids) > 1:
            mapping = {"main": "alt", "alt": "main"}
            candidate_claims = [
                c for c in claims
                if c.recorded_at > 10 and (c.asserted_in_world_branch_id or c.world_branch_id) in mapping
            ]
            if candidate_claims:
                target = rr.choice(candidate_claims)
                old_context = target.asserted_in_world_branch_id or target.world_branch_id
                new_context = mapping[old_context]
                claims = [
                    replace(c, world_branch_id=new_context, asserted_in_world_branch_id=new_context)
                    if c.revision_id == target.revision_id else c
                    for c in claims
                ]
                exposures = [
                    replace(
                        x,
                        world_branch_id=mapping[x.destination_world_branch_id or x.world_branch_id],
                        destination_world_branch_id=mapping[x.destination_world_branch_id or x.world_branch_id],
                    )
                    if x.object_id in target.source_event_ids and (x.destination_world_branch_id or x.world_branch_id) in mapping
                    else x
                    for x in exposures
                ]
            else:
                metadata["corruption_effective"] = "False"
        else:
            metadata["corruption_effective"] = "False"

    elif mode == "exposure_source_swap":
        candidates = [x for x in exposures if x.operation in {"receive", "copy", "restore"}]
        if candidates and pairs:
            target = rr.choice(candidates)
            a, b = rr.choice(pairs)
            replacement = b if target.mind_instance_id == a else a
            exposures = [
                replace(x, mind_instance_id=replacement, source_mind_instance_id=target.mind_instance_id)
                if x.exposure_id == target.exposure_id else x
                for x in exposures
            ]
        else:
            metadata["corruption_effective"] = "False"

    elif mode == "attitude_laundering":
        candidates = [
            c for c in claims
            if c.holder_mind_instance_id is not None
            and c.attitude_or_modality in {"suspect", "disbelieve", "suspend", "hearsay"}
        ]
        if candidates:
            target = rr.choice(candidates)
            claims = [
                replace(c, attitude_or_modality="believe") if c.revision_id == target.revision_id else c
                for c in claims
            ]
        else:
            metadata["corruption_effective"] = "False"

    elif mode == "policy_declassification":
        candidates = [c for c in claims if c.derives_from_claim_ids or c.policy_label != "public"]
        if candidates:
            target = rr.choice(candidates)
            claims = [
                replace(c, policy_label="public", derives_from_claim_ids=())
                if c.revision_id == target.revision_id else c
                for c in claims
            ]
            target_event_ids = set(target.source_event_ids)
            evidence = [
                replace(e, policy_label="public") if e.event_id in target_event_ids else e
                for e in evidence
            ]
        else:
            metadata["corruption_effective"] = "False"

    elif mode == "restore_parent_error":
        candidates = [m for m in minds if m.originating_snapshot_id is not None or m.parent_mind_instance_id is not None]
        if candidates:
            target = rr.choice(candidates)
            alternatives = [m.mind_instance_id for m in minds if m.mind_instance_id != target.mind_instance_id]
            wrong_parent = rr.choice(alternatives) if alternatives and rr.random() < 0.5 else None
            minds = [
                replace(m, parent_mind_instance_id=wrong_parent)
                if m.mind_instance_id == target.mind_instance_id else m
                for m in minds
            ]
        else:
            metadata["corruption_effective"] = "False"

    elif mode == "temporal_scope_shift":
        candidates = [c for c in claims if c.recorded_at > 5]
        if candidates:
            target = rr.choice(candidates)
            shift = rr.choice([-8, -4, 4, 8])
            claims = [
                replace(
                    c,
                    valid_from=max(0, c.valid_from + shift),
                    recorded_at=max(0, c.recorded_at + (shift if rr.random() < 0.5 else 0)),
                )
                if c.revision_id == target.revision_id else c
                for c in claims
            ]
        else:
            metadata["corruption_effective"] = "False"

    elif mode == "speaker_or_holder_swap":
        candidates = [c for c in claims if c.holder_mind_instance_id is not None]
        if candidates and pairs:
            target = rr.choice(candidates)
            a, b = rr.choice(pairs)
            new_holder = b if target.holder_mind_instance_id == a else a
            claims = [
                replace(c, holder_mind_instance_id=new_holder)
                if c.revision_id == target.revision_id else c
                for c in claims
            ]
        else:
            metadata["corruption_effective"] = "False"

    return clone_scenario(
        scenario,
        evidence=evidence,
        claims=claims,
        exposures=exposures,
        minds=minds,
        metadata=metadata,
    )


def corrupt_dataset(scenarios: list[Scenario], prevalence: float, seed: int, cascade_probability: float = 0.25) -> list[Scenario]:
    rr = random.Random(seed)
    output: list[Scenario] = []
    for scenario in scenarios:
        mutated = scenario
        applied: list[str] = []
        if rr.random() < prevalence:
            first = rr.choice(CORRUPTION_MODES)
            mutated = corrupt_scenario(mutated, first, rr)
            applied.append(first)
            if rr.random() < cascade_probability:
                second = rr.choice([m for m in CORRUPTION_MODES if m != first])
                mutated = corrupt_scenario(mutated, second, rr)
                applied.append(second)
        if applied:
            meta = dict(mutated.metadata)
            meta["corruption_modes"] = ",".join(applied)
            mutated = clone_scenario(mutated, metadata=meta)
        output.append(mutated)
    return output
