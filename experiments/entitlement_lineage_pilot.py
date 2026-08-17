#!/usr/bin/env python3
"""MindMapBench-Entitlement pilot.

A controlled mechanism-isolation experiment comparing:

B4 ScopedSlots:
    branch + bitemporal + principal possession + event-level permission columns,
    but no epistemic modality, derivation lineage, source-family deduplication,
    or lineage-aware revocation.

B5 NCM-Psi:
    the same hard gates plus modality-aware adjudication, derivation lineage,
    source-family deduplication, correction/retraction handling, and taint-style
    permission propagation.

The benchmark is synthetic and programmatic. It is a falsification pilot, not
an end-to-end language benchmark and not a public-benchmark SOTA claim.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd
from scipy.stats import binomtest

SEED = 20260817
UNKNOWN = "<unknown>"
RESTRICTED = "<restricted>"
CONFLICT = "<conflict>"

PRINCIPALS = ("alice", "bob", "carol", "dave")
ALL_READERS = frozenset((*PRINCIPALS, "admin", "outsider"))

FACTOR_LEVELS = {
    "perspective": ("direct", "hearsay", "no_access"),
    "temporal": ("stable", "explicit_correction", "implicit_invalidation"),
    "branch": ("common", "divergent", "merge"),
    "reliability": ("reliable", "mistaken", "deceptive"),
    "disclosure": ("public", "private", "revoked"),
    "derivation": ("none", "duplicate", "laundered"),
}

VALUES = (
    "Arbor Bay",
    "Cedar Falls",
    "Dawnport",
    "Elmstead",
    "Frosthaven",
    "Glenmoor",
    "Harborwick",
    "Ivydale",
    "Juniper City",
    "Kingswell",
    "Lakehurst",
    "Moonridge",
    "Northpass",
    "Opalton",
    "Pinecross",
    "Quartz Harbor",
    "Rosefield",
    "Silvermere",
    "Thornwall",
    "Umber Coast",
)


@dataclass(frozen=True, slots=True)
class ClaimEvent:
    id: str
    scenario_id: str
    branch: str
    event_time: int
    recorded_at: int
    subject: str
    predicate: str
    value: str
    modality: str
    speaker: str
    holders: frozenset[str]
    read_acl: frozenset[str]
    source_family: str
    source_ids: tuple[str, ...]
    reliability: float
    revoked_at: Optional[int] = None
    retracts: Optional[str] = None
    valid_to: Optional[int] = None
    corrupted: bool = False
    corruption_mode: Optional[str] = None


@dataclass(frozen=True, slots=True)
class Query:
    id: str
    scenario_id: str
    query_type: str
    branch: str
    valid_at: int
    recorded_at: int
    subject: str
    predicate: str
    caller: str
    viewpoint: Optional[str]
    answer: str
    main_value: str
    alt_value: str
    initial_value: str
    factors: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class Resolution:
    answer: str
    evidence_ids: tuple[str, ...] = ()
    confidence: float = 0.0


def branch_visible(event_branch: str, query_branch: str) -> bool:
    visible = {
        "root": {"root"},
        "main": {"root", "main"},
        "alt": {"root", "alt"},
        "merge": {"root", "main", "alt", "merge"},
    }
    return event_branch in visible[query_branch]


def select_covering_scenarios(n: int, seed: int) -> list[dict[str, str]]:
    """Greedy pairwise-coverage selection, then balanced random fill."""
    rng = random.Random(seed)
    names = tuple(FACTOR_LEVELS)
    universe = [
        dict(zip(names, levels))
        for levels in itertools.product(*(FACTOR_LEVELS[name] for name in names))
    ]

    all_pairs = set()
    for i, name_a in enumerate(names):
        for name_b in names[i + 1 :]:
            for level_a in FACTOR_LEVELS[name_a]:
                for level_b in FACTOR_LEVELS[name_b]:
                    all_pairs.add((name_a, level_a, name_b, level_b))

    uncovered = set(all_pairs)
    selected: list[dict[str, str]] = []
    remaining = list(universe)
    level_counts = Counter()

    while uncovered and remaining and len(selected) < n:
        best_score = -1e9
        best: list[dict[str, str]] = []
        for combo in remaining:
            pair_gain = 0
            for i, name_a in enumerate(names):
                for name_b in names[i + 1 :]:
                    pair_gain += (
                        name_a,
                        combo[name_a],
                        name_b,
                        combo[name_b],
                    ) in uncovered
            imbalance = sum(level_counts[(name, combo[name])] for name in names)
            score = pair_gain * 1000 - imbalance
            if score > best_score:
                best_score = score
                best = [combo]
            elif score == best_score:
                best.append(combo)
        chosen = rng.choice(best)
        selected.append(chosen)
        remaining.remove(chosen)
        for name in names:
            level_counts[(name, chosen[name])] += 1
        for i, name_a in enumerate(names):
            for name_b in names[i + 1 :]:
                uncovered.discard((name_a, chosen[name_a], name_b, chosen[name_b]))

    while len(selected) < n:
        best_count = math.inf
        best: list[dict[str, str]] = []
        for combo in remaining:
            count = sum(level_counts[(name, combo[name])] for name in names)
            if count < best_count:
                best_count = count
                best = [combo]
            elif count == best_count:
                best.append(combo)
        chosen = rng.choice(best)
        selected.append(chosen)
        remaining.remove(chosen)
        for name in names:
            level_counts[(name, chosen[name])] += 1

    return selected


def pairwise_coverage(combos: list[dict[str, str]]) -> float:
    names = tuple(FACTOR_LEVELS)
    observed = set()
    possible = set()
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            for la in FACTOR_LEVELS[a]:
                for lb in FACTOR_LEVELS[b]:
                    possible.add((a, la, b, lb))
    for combo in combos:
        for i, a in enumerate(names):
            for b in names[i + 1 :]:
                observed.add((a, combo[a], b, combo[b]))
    return len(observed) / len(possible)


def _acl(disclosure: str, holders: frozenset[str]) -> tuple[frozenset[str], Optional[int]]:
    if disclosure == "public":
        return ALL_READERS, None
    if disclosure == "private":
        return frozenset((*holders, "admin")), None
    return ALL_READERS, 8


def generate_scenario(index: int, factors: dict[str, str], rng: random.Random) -> tuple[list[ClaimEvent], list[Query]]:
    sid = f"s{index:04d}"
    subject = f"target-{index:04d}"
    predicate = "location"
    initial, changed, alt_value, wrong_value = rng.sample(VALUES, 4)
    principal = rng.choice(PRINCIPALS)
    all_holders = frozenset(PRINCIPALS)

    temporal = factors["temporal"]
    branch_factor = factors["branch"]
    reliability_label = factors["reliability"]
    perspective = factors["perspective"]
    disclosure = factors["disclosure"]
    derivation = factors["derivation"]

    main_value = initial if temporal == "stable" else changed
    if reliability_label == "reliable":
        report_value = main_value
        reliability = 0.90
    elif reliability_label == "mistaken":
        report_value = wrong_value
        reliability = 0.70
    else:
        report_value = wrong_value
        reliability = 0.20

    if perspective == "direct":
        update_holders = frozenset((principal,))
        report_holders = frozenset((principal,))
        correction_holders = frozenset((principal,))
    elif perspective == "hearsay":
        update_holders = frozenset()
        report_holders = frozenset((principal,))
        correction_holders = frozenset()
    else:
        update_holders = frozenset()
        report_holders = frozenset()
        correction_holders = frozenset()

    initial_acl, initial_revoked = _acl(disclosure, all_holders)
    events: list[ClaimEvent] = []

    def add(
        suffix: str,
        branch: str,
        event_time: int,
        recorded_at: int,
        value: str,
        modality: str,
        speaker: str,
        holders: frozenset[str],
        read_acl: frozenset[str],
        source_family: str,
        source_ids: tuple[str, ...] = (),
        reliability_score: float = 1.0,
        revoked_at: Optional[int] = None,
        retracts: Optional[str] = None,
        pred: str = predicate,
    ) -> ClaimEvent:
        event = ClaimEvent(
            id=f"{sid}-{suffix}",
            scenario_id=sid,
            branch=branch,
            event_time=event_time,
            recorded_at=recorded_at,
            subject=subject,
            predicate=pred,
            value=value,
            modality=modality,
            speaker=speaker,
            holders=holders,
            read_acl=read_acl,
            source_family=f"{sid}-{source_family}",
            source_ids=tuple(f"{sid}-{x}" for x in source_ids),
            reliability=reliability_score,
            revoked_at=revoked_at,
            retracts=f"{sid}-{retracts}" if retracts else None,
        )
        events.append(event)
        return event

    initial_event = add(
        "initial", "root", 1, 1, initial, "observation", "root-sensor",
        all_holders, initial_acl, "initial-direct", reliability_score=1.0,
        revoked_at=initial_revoked,
    )

    main_branch = "root" if branch_factor == "common" else "main"
    decisive_acl, decisive_revoked = _acl(disclosure, update_holders or all_holders)

    update_event: Optional[ClaimEvent] = None
    if temporal == "explicit_correction":
        update_event = add(
            "world-update", main_branch, 3, 5, main_value, "observation",
            "main-sensor", update_holders, decisive_acl, "main-direct",
            reliability_score=1.0, revoked_at=decisive_revoked,
        )
    elif temporal == "implicit_invalidation":
        cue_acl, cue_revoked = _acl(disclosure, update_holders or all_holders)
        add(
            "cue-1", main_branch, 3, 4, "cue-a", "observation", "cue-sensor-a",
            update_holders, cue_acl, "cue-a", reliability_score=0.95,
            revoked_at=cue_revoked, pred="location-cue",
        )
        add(
            "cue-2", main_branch, 3, 4, "cue-b", "observation", "cue-sensor-b",
            update_holders, cue_acl, "cue-b", reliability_score=0.95,
            revoked_at=cue_revoked, pred="location-cue",
        )
        update_event = add(
            "inferred-update", main_branch, 4, 5, main_value, "inference",
            "inference-engine", update_holders, ALL_READERS, "inference",
            source_ids=("cue-1", "cue-2"), reliability_score=0.92,
        )

    if temporal == "stable" and perspective == "direct":
        add(
            "stable-reaffirmation", main_branch, 4, 4, initial, "observation",
            "main-sensor", frozenset((principal,)), decisive_acl, "main-direct",
            reliability_score=1.0, revoked_at=decisive_revoked,
        )

    if branch_factor in {"divergent", "merge"}:
        alt_holders = update_holders if branch_factor == "merge" else frozenset()
        alt_acl, alt_revoked = _acl(disclosure, alt_holders or all_holders)
        add(
            "alt-update", "alt", 3, 5, alt_value, "observation", "alt-sensor",
            alt_holders, alt_acl, "alt-direct", reliability_score=1.0,
            revoked_at=alt_revoked,
        )

    report_branch = main_branch
    report_acl, report_revoked = _acl(disclosure, report_holders or all_holders)
    report_sources = (
        (update_event.id.split("-", 1)[1],)
        if update_event is not None
        else (initial_event.id.split("-", 1)[1],)
    )
    add(
        "report", report_branch, 5, 6, report_value, "hearsay",
        f"{reliability_label}-source", report_holders, report_acl,
        "report-family", source_ids=report_sources,
        reliability_score=reliability, revoked_at=report_revoked,
    )

    if derivation != "none":
        if derivation == "duplicate":
            summary_acl = report_acl
            summary_revoked = report_revoked
        else:
            summary_acl = ALL_READERS
            summary_revoked = None
        add(
            "summary-1", report_branch, 6, 7, report_value, "summary",
            "summary-agent-1", report_holders, summary_acl, "report-family",
            source_ids=("report",), reliability_score=0.95,
            revoked_at=summary_revoked,
        )
        add(
            "summary-2", report_branch, 7, 8, report_value, "summary",
            "summary-agent-2", report_holders, summary_acl, "report-family",
            source_ids=("summary-1",), reliability_score=0.95,
            revoked_at=summary_revoked,
        )

    if temporal == "explicit_correction":
        add(
            "official-correction", main_branch, 8, 8, main_value, "correction",
            "official", correction_holders, decisive_acl, "main-direct",
            source_ids=("world-update",), reliability_score=1.0,
            revoked_at=decisive_revoked,
        )
        add(
            "report-retraction", main_branch, 8, 8, "", "retraction", "official",
            correction_holders, decisive_acl, "main-direct",
            source_ids=("official-correction",), reliability_score=1.0,
            revoked_at=decisive_revoked, retracts="report",
        )
        if derivation != "none":
            stale_acl = report_acl if derivation == "duplicate" else ALL_READERS
            stale_revoked = report_revoked if derivation == "duplicate" else None
            add(
                "stale-summary", main_branch, 9, 9, report_value, "summary",
                "stale-cache", report_holders, stale_acl, "report-family",
                source_ids=("summary-2",), reliability_score=0.95,
                revoked_at=stale_revoked,
            )

    query_branch = {"common": "root", "divergent": "main", "merge": "merge"}[branch_factor]
    world_answer = CONFLICT if branch_factor == "merge" else main_value
    if perspective == "direct":
        belief_answer = CONFLICT if branch_factor == "merge" else main_value
    elif perspective == "hearsay":
        belief_answer = initial if reliability_label == "deceptive" else report_value
    else:
        belief_answer = initial
    disclose_answer = world_answer if disclosure == "public" else RESTRICTED
    factors_tuple = tuple(sorted(factors.items()))

    return events, [
        Query(f"{sid}-q-world", sid, "world", query_branch, 10, 10, subject, predicate,
              "admin", None, world_answer, main_value, alt_value, initial, factors_tuple),
        Query(f"{sid}-q-belief", sid, "belief", query_branch, 10, 10, subject, predicate,
              "admin", principal, belief_answer, main_value, alt_value, initial, factors_tuple),
        Query(f"{sid}-q-disclose", sid, "disclose", query_branch, 10, 10, subject, predicate,
              "outsider", None, disclose_answer, main_value, alt_value, initial, factors_tuple),
        Query(f"{sid}-q-historical", sid, "historical", query_branch, 4, 2, subject, predicate,
              "admin", None, initial, main_value, alt_value, initial, factors_tuple),
    ]


class EventIndex:
    def __init__(self, events: Iterable[ClaimEvent]) -> None:
        self.events = list(events)
        self.by_id = {event.id: event for event in self.events}
        self.by_key: dict[tuple[str, str, str], list[ClaimEvent]] = defaultdict(list)
        self.retracted_by: dict[str, list[ClaimEvent]] = defaultdict(list)
        self._lineage_cache: dict[str, frozenset[str]] = {}
        for event in self.events:
            self.by_key[(event.scenario_id, event.subject, event.predicate)].append(event)
            if event.retracts:
                self.retracted_by[event.retracts].append(event)

    def relevant(self, query: Query, *, require_holder: bool, event_level_acl: bool) -> list[ClaimEvent]:
        result: list[ClaimEvent] = []
        for event in self.by_key.get((query.scenario_id, query.subject, query.predicate), []):
            if not branch_visible(event.branch, query.branch):
                continue
            if event.event_time > query.valid_at or event.recorded_at > query.recorded_at:
                continue
            if event.valid_to is not None and query.valid_at >= event.valid_to:
                continue
            if require_holder and (query.viewpoint is None or query.viewpoint not in event.holders):
                continue
            if event_level_acl:
                if query.caller not in event.read_acl:
                    continue
                if event.revoked_at is not None and query.recorded_at >= event.revoked_at and query.caller != "admin":
                    continue
            result.append(event)
        return result

    def lineage(self, event: ClaimEvent) -> set[str]:
        cached = self._lineage_cache.get(event.id)
        if cached is not None:
            return set(cached)
        visited: set[str] = set()
        stack = list(event.source_ids)
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            parent = self.by_id.get(current)
            if parent:
                stack.extend(parent.source_ids)
        self._lineage_cache[event.id] = frozenset(visited)
        return visited

    def lineage_visible(self, event: ClaimEvent, query: Query) -> bool:
        for event_id in {event.id, *self.lineage(event)}:
            ancestor = self.by_id.get(event_id)
            if ancestor is None:
                continue
            if query.caller not in ancestor.read_acl:
                return False
            if ancestor.revoked_at is not None and query.recorded_at >= ancestor.revoked_at and query.caller != "admin":
                return False
        return True

    def blocked_by_retraction(self, event: ClaimEvent, query: Query, viewpoint: Optional[str]) -> bool:
        for target_id in {event.id, *self.lineage(event)}:
            for retraction in self.retracted_by.get(target_id, []):
                if not branch_visible(retraction.branch, query.branch):
                    continue
                if retraction.event_time > query.valid_at or retraction.recorded_at > query.recorded_at:
                    continue
                if viewpoint is not None and viewpoint not in retraction.holders:
                    continue
                return True
        return False


def latest_row(events: list[ClaimEvent]) -> Resolution:
    candidates = [event for event in events if event.modality != "retraction"]
    if not candidates:
        return Resolution(UNKNOWN)
    selected = max(candidates, key=lambda e: (e.event_time, e.recorded_at, e.id))
    return Resolution(selected.value, (selected.id,), 0.5)


def resolve_scoped_slots(index: EventIndex, query: Query) -> Resolution:
    if query.query_type in {"world", "historical"}:
        return latest_row(index.relevant(query, require_holder=False, event_level_acl=True))
    if query.query_type == "belief":
        return latest_row(index.relevant(query, require_holder=True, event_level_acl=True))
    if query.query_type == "disclose":
        resolution = latest_row(index.relevant(query, require_holder=False, event_level_acl=True))
        return resolution if resolution.answer != UNKNOWN else Resolution(RESTRICTED)
    raise ValueError(query.query_type)


def modality_weight(event: ClaimEvent, query: Query) -> float:
    if query.query_type in {"world", "historical", "disclose"}:
        base = {
            "observation": 3.0,
            "correction": 4.0,
            "inference": 3.6 if len(event.source_ids) >= 2 else 1.0,
            "assertion": 0.75,
            "hearsay": 0.75,
            "summary": 0.0,
        }.get(event.modality, 0.0)
        return base * event.reliability
    base = {
        "observation": 4.0,
        "correction": 5.0,
        "inference": 4.2 if len(event.source_ids) >= 2 else 1.2,
        "assertion": 5.0,
        "hearsay": 5.0,
        "summary": 0.0,
    }.get(event.modality, 0.0)
    age = max(0, query.valid_at - event.event_time)
    return base * event.reliability * math.exp(-0.10 * age)


def scored_resolution(index: EventIndex, query: Query, *, use_modality: bool, use_lineage: bool) -> Resolution:
    factors = dict(query.factors)
    compare_parent_states = use_modality and query.branch == "merge" and (
        query.query_type in {"world", "disclose"}
        or (query.query_type == "belief" and factors.get("perspective") == "direct")
    )
    if compare_parent_states:
        main_resolution = scored_resolution(index, replace(query, branch="main"), use_modality=use_modality, use_lineage=use_lineage)
        alt_resolution = scored_resolution(index, replace(query, branch="alt"), use_modality=use_modality, use_lineage=use_lineage)
        if query.query_type == "disclose" and (main_resolution.answer == RESTRICTED or alt_resolution.answer == RESTRICTED):
            return Resolution(RESTRICTED, (), 1.0)
        concrete = {a for a in (main_resolution.answer, alt_resolution.answer) if a not in {UNKNOWN, RESTRICTED}}
        if len(concrete) > 1:
            return Resolution(CONFLICT, tuple(sorted({*main_resolution.evidence_ids, *alt_resolution.evidence_ids})), 0.5)
        if len(concrete) == 1:
            answer = next(iter(concrete))
            chosen = main_resolution if main_resolution.answer == answer else alt_resolution
            return Resolution(answer, chosen.evidence_ids, chosen.confidence)

    require_holder = query.query_type == "belief"
    events = index.relevant(query, require_holder=require_holder, event_level_acl=True)
    if use_lineage:
        events = [
            event for event in events
            if index.lineage_visible(event, query)
            and not index.blocked_by_retraction(event, query, query.viewpoint if require_holder else None)
        ]

    if query.query_type == "disclose" and not events:
        privileged = replace(query, caller="admin")
        if index.relevant(privileged, require_holder=False, event_level_acl=False):
            return Resolution(RESTRICTED, (), 1.0)
        return Resolution(UNKNOWN)
    if not events:
        return Resolution(UNKNOWN)

    if use_modality and query.branch == "merge":
        branch_best: dict[str, tuple[float, str, ClaimEvent]] = {}
        for event in events:
            if event.branch not in {"main", "alt"} or event.modality not in {"observation", "correction", "inference"}:
                continue
            weight = modality_weight(event, query)
            previous = branch_best.get(event.branch)
            if previous is None or weight > previous[0]:
                branch_best[event.branch] = (weight, event.value, event)
        if {"main", "alt"} <= set(branch_best):
            main_best, alt_best = branch_best["main"], branch_best["alt"]
            if main_best[0] >= 2.5 and alt_best[0] >= 2.5 and main_best[1] != alt_best[1]:
                return Resolution(CONFLICT, tuple(sorted((main_best[2].id, alt_best[2].id))), 0.5)

    if not use_modality:
        return latest_row(events)

    by_value_family: dict[tuple[str, str], tuple[float, ClaimEvent]] = {}
    for event in events:
        if event.modality == "retraction":
            continue
        weight = modality_weight(event, query)
        key = (event.value, event.source_family)
        previous = by_value_family.get(key)
        if previous is None or weight > previous[0]:
            by_value_family[key] = (weight, event)

    value_scores: dict[str, float] = defaultdict(float)
    value_events: dict[str, list[ClaimEvent]] = defaultdict(list)
    for (value, _family), (weight, event) in by_value_family.items():
        value_scores[value] += weight
        if weight > 0:
            value_events[value].append(event)
    if not value_scores:
        return Resolution(UNKNOWN)

    value_latest = {
        value: max((event.event_time, event.recorded_at) for event in value_events.get(value, []))
        if value_events.get(value) else (-1, -1)
        for value in value_scores
    }
    ranked = sorted(value_scores.items(), key=lambda item: (item[1], value_latest[item[0]], item[0]), reverse=True)
    best_value, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else -math.inf
    if query.branch == "merge" and len(ranked) > 1 and abs(best_score - second_score) <= 0.15:
        top_values = [value for value, score in ranked if abs(score - best_score) <= 0.15]
        evidence = tuple(sorted(event.id for value in top_values for event in value_events.get(value, [])))
        return Resolution(CONFLICT, evidence, 0.5)
    confidence = 1.0 / (1.0 + math.exp(-(best_score - max(second_score, 0.0))))
    evidence = tuple(sorted(event.id for event in value_events.get(best_value, [])))
    return Resolution(best_value, evidence, confidence)


SYSTEMS = {
    "ScopedSlots": lambda index, query: resolve_scoped_slots(index, query),
    "ModalityNoLineage": lambda index, query: scored_resolution(index, query, use_modality=True, use_lineage=False),
    "LineageNoModality": lambda index, query: scored_resolution(index, query, use_modality=False, use_lineage=True),
    "NCM-Psi": lambda index, query: scored_resolution(index, query, use_modality=True, use_lineage=True),
}


def evaluate(events: list[ClaimEvent], queries: list[Query]) -> pd.DataFrame:
    index = EventIndex(events)
    rows: list[dict[str, object]] = []
    for system, resolver in SYSTEMS.items():
        for query in queries:
            resolution = resolver(index, query)
            factors = dict(query.factors)
            answer = resolution.answer
            rows.append({
                "system": system,
                "query_id": query.id,
                "scenario_id": query.scenario_id,
                "query_type": query.query_type,
                "gold": query.answer,
                "prediction": answer,
                "correct": int(answer == query.answer),
                "confidence": resolution.confidence,
                "evidence_ids": "|".join(resolution.evidence_ids),
                "unauthorized_disclosure": int(query.answer == RESTRICTED and answer not in {RESTRICTED, UNKNOWN}),
                "branch_contamination": int(query.branch != "alt" and answer == query.alt_value and answer != query.answer),
                "false_consensus": int(factors["reliability"] in {"mistaken", "deceptive"} and answer not in {query.answer, UNKNOWN, RESTRICTED, CONFLICT}),
                "unsafe_nonabstention": int(query.answer in {UNKNOWN, RESTRICTED, CONFLICT} and answer not in {UNKNOWN, RESTRICTED, CONFLICT}),
                **factors,
            })
    return pd.DataFrame(rows)


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for system, group in df.groupby("system", sort=False):
        restricted = group[group.gold == RESTRICTED]
        merge = group[group.branch == "merge"]
        rows.append({
            "system": system,
            "N": len(group),
            "MacroExactAccuracy": group.correct.mean(),
            "PrimaryAccuracy": group[group.query_type.isin(["world", "belief", "disclose"])].correct.mean(),
            "WorldAccuracy": group[group.query_type == "world"].correct.mean(),
            "BeliefAccuracy": group[group.query_type == "belief"].correct.mean(),
            "DisclosureAccuracy": group[group.query_type == "disclose"].correct.mean(),
            "HistoricalAccuracy": group[group.query_type == "historical"].correct.mean(),
            "UnauthorizedDisclosureRate": restricted.unauthorized_disclosure.mean() if len(restricted) else 0.0,
            "BranchContaminationRate": group.branch_contamination.mean(),
            "MergeConflictAccuracy": merge.correct.mean() if len(merge) else 0.0,
            "FalseConsensusRate": group.false_consensus.mean(),
            "UnsafeNonAbstentionRate": group.unsafe_nonabstention.mean(),
        })
    return pd.DataFrame(rows).sort_values("MacroExactAccuracy", ascending=False)


def by_factor(df: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for factor in (*FACTOR_LEVELS.keys(), "query_type"):
        grouped = df.groupby(["system", factor], as_index=False).agg(
            N=("correct", "size"),
            Accuracy=("correct", "mean"),
            UnauthorizedDisclosureRate=("unauthorized_disclosure", "mean"),
            BranchContaminationRate=("branch_contamination", "mean"),
            FalseConsensusRate=("false_consensus", "mean"),
        ).rename(columns={factor: "level"})
        grouped["factor"] = factor
        parts.append(grouped)
    return pd.concat(parts, ignore_index=True)[[
        "system", "factor", "level", "N", "Accuracy",
        "UnauthorizedDisclosureRate", "BranchContaminationRate", "FalseConsensusRate",
    ]]


def paired_stats(df: pd.DataFrame, baseline: str, proposed: str, *, seed: int, bootstrap_reps: int = 20_000) -> dict[str, object]:
    pivot = df.pivot(index=["scenario_id", "query_id"], columns="system", values="correct")
    a, b = pivot[baseline], pivot[proposed]
    scenario_diff = (b - a).reset_index(name="diff").groupby("scenario_id", as_index=False)["diff"].mean()
    rng = np.random.default_rng(seed)
    values = scenario_diff["diff"].to_numpy()
    boots = np.array([values[rng.integers(0, len(values), len(values))].mean() for _ in range(bootstrap_reps)])
    proposed_only = int(((b == 1) & (a == 0)).sum())
    baseline_only = int(((a == 1) & (b == 0)).sum())
    discordant = proposed_only + baseline_only
    p_value = float(binomtest(min(proposed_only, baseline_only), n=discordant, p=0.5).pvalue) if discordant else 1.0
    return {
        "baseline": baseline,
        "proposed": proposed,
        "paired_queries": int(len(a)),
        "cluster_count": int(len(values)),
        "accuracy_baseline": float(a.mean()),
        "accuracy_proposed": float(b.mean()),
        "absolute_improvement": float((b - a).mean()),
        "scenario_cluster_bootstrap_95ci": [float(x) for x in np.quantile(boots, [0.025, 0.975])],
        "discordant_proposed_only": proposed_only,
        "discordant_baseline_only": baseline_only,
        "mcnemar_exact_p": p_value,
    }


CORRUPTION_MODES = (
    "branch_swap", "holder_swap", "modality_laundering", "visibility_widening",
    "transaction_shift", "lineage_break", "value_flip", "reliability_flip",
)


def stable_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def corrupt_event(event: ClaimEvent, mode: str, scenario_values: tuple[str, str]) -> ClaimEvent:
    main_value, alt_value = scenario_values
    if mode == "branch_swap":
        return replace(event, branch={"main": "alt", "alt": "main", "root": "main"}.get(event.branch, event.branch), corrupted=True, corruption_mode=mode)
    if mode == "holder_swap":
        pivot = PRINCIPALS[stable_int(event.id) % len(PRINCIPALS)]
        holders = set(event.holders)
        holders.remove(pivot) if pivot in holders else holders.add(pivot)
        return replace(event, holders=frozenset(holders), corrupted=True, corruption_mode=mode)
    if mode == "modality_laundering":
        modality = {"summary": "observation", "hearsay": "observation", "correction": "summary", "inference": "observation"}.get(event.modality, "hearsay")
        return replace(event, modality=modality, corrupted=True, corruption_mode=mode)
    if mode == "visibility_widening":
        return replace(event, read_acl=ALL_READERS, revoked_at=None, corrupted=True, corruption_mode=mode)
    if mode == "transaction_shift":
        return replace(event, recorded_at=event.recorded_at + 6, corrupted=True, corruption_mode=mode)
    if mode == "lineage_break":
        return replace(event, source_ids=(), source_family=f"{event.id}-broken-family", corrupted=True, corruption_mode=mode)
    if mode == "value_flip":
        return replace(event, value=alt_value if event.value == main_value else main_value, corrupted=True, corruption_mode=mode)
    if mode == "reliability_flip":
        return replace(event, reliability=1.0 - event.reliability, corrupted=True, corruption_mode=mode)
    raise ValueError(mode)


def inject_correlated_noise(events: list[ClaimEvent], queries: list[Query], *, p: float, rho: float, seed: int) -> tuple[list[ClaimEvent], dict[str, float]]:
    rng = random.Random(seed)
    shared_p = rho * p
    independent_p = 0.0 if shared_p >= 1 else (p - shared_p) / (1 - shared_p)
    queries_by_scenario = {q.scenario_id: q for q in queries if q.query_type == "world"}
    family_mode: dict[str, Optional[str]] = {}
    corrupted: list[ClaimEvent] = []
    mode_counts = Counter()
    for event in events:
        if event.source_family not in family_mode:
            family_mode[event.source_family] = CORRUPTION_MODES[stable_int(f"{seed}:{event.source_family}") % len(CORRUPTION_MODES)] if rng.random() < shared_p else None
        mode = family_mode[event.source_family]
        if mode is None and rng.random() < independent_p:
            mode = CORRUPTION_MODES[stable_int(f"{seed}:{event.id}") % len(CORRUPTION_MODES)]
        if mode is None or event.modality == "retraction":
            corrupted.append(event)
            continue
        query = queries_by_scenario[event.scenario_id]
        corrupted.append(corrupt_event(event, mode, (query.main_value, query.alt_value)))
        mode_counts[mode] += 1
    representation_error = sum(event.corrupted for event in corrupted) / len(corrupted)
    return corrupted, {
        "representation_error": representation_error,
        **{f"mode_{mode}": mode_counts[mode] / len(events) for mode in CORRUPTION_MODES},
    }


def run_noise_study(events: list[ClaimEvent], queries: list[Query], *, repetitions: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for rho in (0.0, 0.5, 0.9):
        for p in (0.0, 0.01, 0.05, 0.10, 0.20, 0.30):
            for repetition in range(repetitions):
                noisy, noise_meta = inject_correlated_noise(
                    events, queries, p=p, rho=rho,
                    seed=seed + int(rho * 1_000_000) + int(p * 100_000) + repetition * 10_007,
                )
                result = evaluate(noisy, queries)
                for system in ("ScopedSlots", "NCM-Psi"):
                    group = result[result.system == system]
                    restricted = group[group.gold == RESTRICTED]
                    rows.append({
                        "system": system,
                        "target_error_rate": p,
                        "rho": rho,
                        "repetition": repetition,
                        "observed_representation_error": noise_meta["representation_error"],
                        "MacroExactAccuracy": group.correct.mean(),
                        "UnauthorizedDisclosureRate": restricted.unauthorized_disclosure.mean() if len(restricted) else 0.0,
                        "BranchContaminationRate": group.branch_contamination.mean(),
                        "FalseConsensusRate": group.false_consensus.mean(),
                        **{key: value for key, value in noise_meta.items() if key.startswith("mode_")},
                    })
    detail = pd.DataFrame(rows)
    summary = detail.groupby(["system", "target_error_rate", "rho"], as_index=False).agg(
        N_runs=("MacroExactAccuracy", "size"),
        RepresentationErrorMean=("observed_representation_error", "mean"),
        AccuracyMean=("MacroExactAccuracy", "mean"),
        AccuracySD=("MacroExactAccuracy", "std"),
        UnauthorizedDisclosureMean=("UnauthorizedDisclosureRate", "mean"),
        BranchContaminationMean=("BranchContaminationRate", "mean"),
        FalseConsensusMean=("FalseConsensusRate", "mean"),
    ).sort_values(["rho", "target_error_rate", "system"])
    return detail, summary


def generate_dataset(scenarios: int, seed: int) -> tuple[list[ClaimEvent], list[Query], list[dict[str, str]]]:
    combos = select_covering_scenarios(scenarios, seed)
    rng = random.Random(seed)
    events: list[ClaimEvent] = []
    queries: list[Query] = []
    for index, factors in enumerate(combos):
        scenario_events, scenario_queries = generate_scenario(index, factors, rng)
        events.extend(scenario_events)
        queries.extend(scenario_queries)
    return events, queries, combos


def seed_replication(scenarios: int, seeds: list[int]) -> pd.DataFrame:
    rows = []
    for seed in seeds:
        events, queries, combos = generate_dataset(scenarios, seed)
        result = evaluate(events, queries)
        for row in aggregate(result).to_dict("records"):
            rows.append({"dataset_seed": seed, "pairwise_coverage": pairwise_coverage(combos), **row})
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenarios", type=int, default=200)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--dataset-seeds", type=int, default=10)
    parser.add_argument("--noise-repetitions", type=int, default=20)
    parser.add_argument("--output-dir", type=Path, default=Path("results/entitlement-lineage"))
    args = parser.parse_args()

    start = time.perf_counter()
    events, queries, combos = generate_dataset(args.scenarios, args.seed)
    result = evaluate(events, queries)
    summary = aggregate(result)
    factor_result = by_factor(result)
    primary_result = result[result.query_type.isin(["world", "belief", "disclose"])].copy()
    stats = paired_stats(primary_result, "ScopedSlots", "NCM-Psi", seed=args.seed)

    replication_seeds = [args.seed + i * 9973 for i in range(args.dataset_seeds)]
    replication = seed_replication(args.scenarios, replication_seeds)
    noise_detail, noise_summary = run_noise_study(events, queries, repetitions=args.noise_repetitions, seed=args.seed)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_dir / "clean_summary.csv", index=False)
    factor_result.to_csv(args.output_dir / "clean_by_factor.csv", index=False)
    result.to_csv(args.output_dir / "clean_query_level.csv", index=False)
    replication.to_csv(args.output_dir / "seed_replication.csv", index=False)
    noise_detail.to_csv(args.output_dir / "noise_runs.csv", index=False)
    noise_summary.to_csv(args.output_dir / "noise_summary.csv", index=False)
    factors_df = pd.DataFrame(combos)
    factors_df.insert(0, "scenario_id", [f"s{i:04d}" for i in range(len(combos))])
    factors_df.to_csv(args.output_dir / "scenario_design.csv", index=False)

    metadata = {
        "benchmark": "MindMapBench-Entitlement-Pilot v0.1",
        "scope": "synthetic mechanism-isolation pilot comparing a scoped slot store with an epistemically typed lineage ledger",
        "seed": args.seed,
        "scenario_count": args.scenarios,
        "query_count": len(queries),
        "event_count": len(events),
        "queries_per_scenario": len(queries) / args.scenarios,
        "pairwise_factor_coverage": pairwise_coverage(combos),
        "dataset_replication_seeds": replication_seeds,
        "noise_repetitions": args.noise_repetitions,
        "transaction_time_definition": "immutable system record/ingestion time; distinct from event valid time",
        "systems": list(SYSTEMS),
        "primary_endpoint": "macro exact accuracy over world, belief, and disclosure queries; restricted disclosures and unresolved merge conflicts require the explicit sentinel answer",
        "primary_comparison": stats,
        "limitations": [
            "Gold answers and structured records are generated programmatically.",
            "The experiment does not evaluate natural-language extraction or a reader LLM.",
            "NCM-Psi uses hand-specified modality weights.",
            "The task intentionally includes cases where modality and lineage are causally relevant.",
            "Noise channels are synthetic and do not estimate empirical LLM error distributions.",
            "Clean NCM-Psi accuracy is a mechanism-conformance result, not a deployment claim.",
        ],
        "runtime_seconds": time.perf_counter() - start,
    }
    (args.output_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print(summary.to_string(index=False))
    print("\nPrimary comparison")
    print(json.dumps(stats, indent=2))
    print("\nNoise summary (selected rows)")
    print(noise_summary[noise_summary.target_error_rate.isin([0.0, 0.1, 0.2])].to_string(index=False))
    print(f"\nWrote outputs to {args.output_dir}")


if __name__ == "__main__":
    main()
