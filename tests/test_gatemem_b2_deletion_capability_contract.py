from __future__ import annotations

import json
from pathlib import Path

from mindmap.track_x.gatemem_governance_safe import (
    deletion_capability_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT
    / "configs"
    / "track_x_gatemem_b2_deletion_capability_v0_1.json"
)


def test_deletion_capability_contract_matches_frozen_implementation():
    committed = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert committed == deletion_capability_manifest()
    assert committed["route"] == "capability-boundary"
    assert "referent-less forget <fact> requests" in committed[
        "outside_capability"
    ]
    assert "incomplete" in committed["expected_consequence"]
