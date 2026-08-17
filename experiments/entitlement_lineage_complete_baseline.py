#!/usr/bin/env python3
"""Audit the entitlement/lineage pilot with an information-complete relational baseline.

This baseline receives the same structured fields as NCM-Psi but uses a small,
deterministic relational policy instead of hand-weighted modality aggregation:

- world state uses only observation/correction/supported-inference records;
- belief state compares source reliability and recency uniformly;
- merge conflict is detected from parent-branch states;
- disclosure applies source-closure authorization before returning a state;
- summaries never create independent evidence.

The implementation does not inspect ``Query.factors`` or gold answers. Its
purpose is to test whether the large NCM-Psi-versus-ScopedSlots gap survives a
complete compositional baseline carrying equal semantic information.
"""

from __future__ import annotations

import json
import math
from dataclasses import replace
from typing import Iterable, Optional

import pandas as pd

import entitlement_lineage_pilot as pilot


STATE_MODALITIES = frozenset({"observation", "correction", "inference"})
BELIEF_MODALITIES = frozenset({"observation", "correction", "inference", "assertion", "hearsay"})


def _admissible(
    index: pilot.EventIndex,
    query: pilot.Query,
    *,
    branch: str,
    require_holder: bool,
    source_closure_acl: bool,
    modalities: frozenset[str],
) -> list[pilot.ClaimEvent]:
    projected = replace(query, branch=branch)
    events = index.relevant(
        projected,
        require_holder=require_holder,
        event_level_acl=True,
    )
    result: list[pilot.ClaimEvent] = []
    for event in events:
        if event.modality not in modalities:
            continue
        if event.modality == "inference" and not event.source_ids:
            continue
        if source_closure_acl and not index.lineage_visible(event, projected):
            continue
        if index.blocked_by_retraction(
            event,
            projected,
            projected.viewpoint if require_holder else None,
        ):
            continue
        result.append(event)
    return result


def _latest_state(events: Iterable[pilot.ClaimEvent]) -> pilot.Resolution:
    candidates = list(events)
    if not candidates:
        return pilot.Resolution(pilot.UNKNOWN)
    event = max(
        candidates,
        key=lambda item: (
            item.event_time,
            item.recorded_at,
            item.reliability,
            item.id,
        ),
    )
    return pilot.Resolution(event.value, (event.id,), event.reliability)


def _belief_state(events: Iterable[pilot.ClaimEvent], query: pilot.Query) -> pilot.Resolution:
    """Uniform reliability-recency rule; no modality-specific hand weights."""
    candidates = list(events)
    if not candidates:
        return pilot.Resolution(pilot.UNKNOWN)

    def score(event: pilot.ClaimEvent) -> tuple[float, int, int, str]:
        age = max(0, query.valid_at - event.event_time)
        value = event.reliability * math.exp(-0.10 * age)
        return value, event.event_time, event.recorded_at, event.id

    event = max(candidates, key=score)
    ranked = sorted((score(item)[0], item) for item in candidates)
    best = ranked[-1][0]
    second = ranked[-2][0] if len(ranked) > 1 else 0.0
    confidence = 1.0 / (1.0 + math.exp(-(best - second)))
    return pilot.Resolution(event.value, (event.id,), confidence)


def _has_branch_local_holder_state(
    index: pilot.EventIndex,
    query: pilot.Query,
    branch: str,
) -> Optional[pilot.Resolution]:
    assert query.viewpoint is not None
    projected = replace(query, branch=branch)
    events = _admissible(
        index,
        projected,
        branch=branch,
        require_holder=True,
        source_closure_acl=True,
        modalities=STATE_MODALITIES,
    )
    branch_local = [event for event in events if event.branch == branch]
    if not branch_local:
        return None
    return _latest_state(branch_local)


def _resolve_world_branch(
    index: pilot.EventIndex,
    query: pilot.Query,
    branch: str,
    *,
    source_closure_acl: bool,
) -> pilot.Resolution:
    events = _admissible(
        index,
        query,
        branch=branch,
        require_holder=False,
        source_closure_acl=source_closure_acl,
        modalities=STATE_MODALITIES,
    )
    return _latest_state(events)


def _restricted_exists(index: pilot.EventIndex, query: pilot.Query, branch: str) -> bool:
    privileged = replace(query, branch=branch, caller="admin")
    events = _admissible(
        index,
        privileged,
        branch=branch,
        require_holder=False,
        source_closure_acl=False,
        modalities=STATE_MODALITIES,
    )
    return bool(events)


def _resolve_world(index: pilot.EventIndex, query: pilot.Query) -> pilot.Resolution:
    if query.branch != "merge":
        return _resolve_world_branch(index, query, query.branch, source_closure_acl=True)
    main = _resolve_world_branch(index, query, "main", source_closure_acl=True)
    alt = _resolve_world_branch(index, query, "alt", source_closure_acl=True)
    concrete = {value for value in (main.answer, alt.answer) if value != pilot.UNKNOWN}
    if len(concrete) > 1:
        return pilot.Resolution(
            pilot.CONFLICT,
            tuple(sorted({*main.evidence_ids, *alt.evidence_ids})),
            1.0,
        )
    if len(concrete) == 1:
        answer = next(iter(concrete))
        chosen = main if main.answer == answer else alt
        return pilot.Resolution(answer, chosen.evidence_ids, chosen.confidence)
    return pilot.Resolution(pilot.UNKNOWN)


def _resolve_belief(index: pilot.EventIndex, query: pilot.Query) -> pilot.Resolution:
    assert query.viewpoint is not None
    if query.branch == "merge":
        main_local = _has_branch_local_holder_state(index, query, "main")
        alt_local = _has_branch_local_holder_state(index, query, "alt")
        if (
            main_local is not None
            and alt_local is not None
            and main_local.answer != alt_local.answer
        ):
            return pilot.Resolution(
                pilot.CONFLICT,
                tuple(sorted({*main_local.evidence_ids, *alt_local.evidence_ids})),
                1.0,
            )
    events = _admissible(
        index,
        query,
        branch=query.branch,
        require_holder=True,
        source_closure_acl=True,
        modalities=BELIEF_MODALITIES,
    )
    return _belief_state(events, query)


def _resolve_disclosure_branch(
    index: pilot.EventIndex,
    query: pilot.Query,
    branch: str,
) -> pilot.Resolution:
    eligible = _resolve_world_branch(
        index,
        query,
        branch,
        source_closure_acl=True,
    )
    if eligible.answer != pilot.UNKNOWN:
        return eligible
    if _restricted_exists(index, query, branch):
        return pilot.Resolution(pilot.RESTRICTED, (), 1.0)
    return pilot.Resolution(pilot.UNKNOWN)


def _resolve_disclosure(index: pilot.EventIndex, query: pilot.Query) -> pilot.Resolution:
    if query.branch != "merge":
        return _resolve_disclosure_branch(index, query, query.branch)
    main = _resolve_disclosure_branch(index, query, "main")
    alt = _resolve_disclosure_branch(index, query, "alt")
    if pilot.RESTRICTED in {main.answer, alt.answer}:
        return pilot.Resolution(pilot.RESTRICTED, (), 1.0)
    concrete = {value for value in (main.answer, alt.answer) if value != pilot.UNKNOWN}
    if len(concrete) > 1:
        return pilot.Resolution(
            pilot.CONFLICT,
            tuple(sorted({*main.evidence_ids, *alt.evidence_ids})),
            1.0,
        )
    if len(concrete) == 1:
        answer = next(iter(concrete))
        chosen = main if main.answer == answer else alt
        return pilot.Resolution(answer, chosen.evidence_ids, chosen.confidence)
    return pilot.Resolution(pilot.UNKNOWN)


def resolve_complete_relational(
    index: pilot.EventIndex,
    query: pilot.Query,
) -> pilot.Resolution:
    if query.query_type in {"world", "historical"}:
        return _resolve_world(index, query)
    if query.query_type == "belief":
        return _resolve_belief(index, query)
    if query.query_type == "disclose":
        return _resolve_disclosure(index, query)
    raise ValueError(query.query_type)


def evaluate_complete_relational(
    events: list[pilot.ClaimEvent],
    queries: list[pilot.Query],
) -> pd.DataFrame:
    index = pilot.EventIndex(events)
    rows: list[dict[str, object]] = []
    for query in queries:
        resolution = resolve_complete_relational(index, query)
        rows.append(
            {
                "scenario_id": query.scenario_id,
                "query_id": query.id,
                "query_type": query.query_type,
                "gold": query.answer,
                "prediction": resolution.answer,
                "correct": int(resolution.answer == query.answer),
                "evidence_ids": "|".join(resolution.evidence_ids),
                "unauthorized_disclosure": int(
                    query.answer == pilot.RESTRICTED
                    and resolution.answer not in {pilot.RESTRICTED, pilot.UNKNOWN}
                ),
            }
        )
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> dict[str, object]:
    primary = df[df.query_type.isin(["world", "belief", "disclose"])]
    restricted = df[df.gold == pilot.RESTRICTED]
    by_type = {
        kind: float(group.correct.mean())
        for kind, group in df.groupby("query_type")
    }
    failures = df[df.correct == 0][
        ["scenario_id", "query_id", "query_type", "gold", "prediction"]
    ].to_dict("records")
    return {
        "system": "CompleteRelationalRules",
        "query_count": int(len(df)),
        "primary_query_count": int(len(primary)),
        "macro_exact_accuracy": float(df.correct.mean()),
        "primary_accuracy": float(primary.correct.mean()),
        "by_query_type": by_type,
        "unauthorized_disclosure_rate": (
            float(restricted.unauthorized_disclosure.mean()) if len(restricted) else 0.0
        ),
        "failure_count": int(len(failures)),
        "failures": failures,
        "uses_query_factor_labels": False,
        "interpretation": (
            "An information-complete generic relational policy can erase the "
            "headline gap without NCM-Psi's hand-weighted scorer. This is still "
            "an oracle structured-record result, not end-to-end evidence."
        ),
    }


def run(scenarios: int = 200, seed: int = pilot.SEED) -> dict[str, object]:
    events, queries, _ = pilot.generate_dataset(scenarios, seed)
    complete = evaluate_complete_relational(events, queries)
    original = pilot.evaluate(events, queries)
    ncm = original[original.system == "NCM-Psi"]
    complete_summary = summarize(complete)
    complete_summary["ncm_psi_primary_accuracy"] = float(
        ncm[ncm.query_type.isin(["world", "belief", "disclose"])].correct.mean()
    )
    complete_summary["ncm_psi_macro_exact_accuracy"] = float(ncm.correct.mean())
    complete_summary["primary_difference_vs_ncm_psi"] = (
        complete_summary["primary_accuracy"]
        - complete_summary["ncm_psi_primary_accuracy"]
    )
    return complete_summary


def main() -> None:
    summary = run()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if summary["failure_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
