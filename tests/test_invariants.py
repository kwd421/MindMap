from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))

from mindmap import EpistemicBranchStore, SYSTEM_CONFIGS, UNKNOWN  # noqa: E402
from epistemic_branch_pilot import generate_scenario  # noqa: E402


def scenario(seed: int = 7):
    return generate_scenario(0, random.Random(seed))


def test_reference_answers_are_self_consistent() -> None:
    events, queries = scenario()
    store = EpistemicBranchStore()
    store.extend(events)
    for query in queries:
        assert store.resolve(query, **SYSTEM_CONFIGS["NCM3E"]).answer == query.answer


def test_unauthorized_secret_is_non_revealing() -> None:
    events, queries = scenario()
    store = EpistemicBranchStore()
    store.extend(events)
    query = next(q for q in queries if q.category == "knowledge_not_access")
    assert query.answer == UNKNOWN
    assert store.resolve(query, **SYSTEM_CONFIGS["NCM3E"]).answer == UNKNOWN


def test_authorization_does_not_create_character_knowledge() -> None:
    events, queries = scenario()
    store = EpistemicBranchStore()
    store.extend(events)
    query = next(q for q in queries if q.id.endswith("admin-unwitnessed-secret"))
    assert query.caller == "admin"
    assert store.resolve(query, **SYSTEM_CONFIGS["NCM3E"]).answer == UNKNOWN


def test_worldline_isolation() -> None:
    events, queries = scenario()
    store = EpistemicBranchStore()
    store.extend(events)
    main = next(q for q in queries if q.id.endswith("world-main"))
    alt = next(q for q in queries if q.id.endswith("world-alt"))
    assert main.answer != alt.answer
    assert store.resolve(main, **SYSTEM_CONFIGS["NCM3E"]).answer == main.answer
    assert store.resolve(alt, **SYSTEM_CONFIGS["NCM3E"]).answer == alt.answer


def test_transaction_time_projection() -> None:
    events, queries = scenario()
    store = EpistemicBranchStore()
    store.extend(events)
    before = next(q for q in queries if "before-tx" in q.id)
    after = next(
        q
        for q in queries
        if "after-tx" in q.id and q.viewpoint == before.viewpoint
    )
    assert before.valid_at == after.valid_at
    assert before.tx_at < after.tx_at
    assert store.resolve(before, **SYSTEM_CONFIGS["NCM3E"]).answer == before.answer
    assert store.resolve(after, **SYSTEM_CONFIGS["NCM3E"]).answer == after.answer
