import json
from pathlib import Path

import pytest

from mindmap.track_x.v02_authorship import validate_authorship_note


ROOT = Path(__file__).resolve().parents[1]


def _note(base: str, branch: str) -> str:
    return f"""# Track X v0.2 Held-Out Passage Authorship

[Session A] ACCEPT WITH PASSAGE CONTRIBUTION
Base/freeze commit: {base}
I did not edit or use the Track X v0.2 primary extractor, verifier,
thresholds, development passages, evaluator, or answer outputs while writing
these passages.

Held-out branch: {branch}
Changed paths:
- data/track_x_v02/heldout/session_a.json
- data/track_x_v02/heldout/AUTHORSHIP.md
"""


def test_valid_authorship_note_binds_base_branch_and_two_paths(tmp_path: Path):
    base = "1" * 40
    path = tmp_path / "AUTHORSHIP.md"
    path.write_text(
        _note(base, "research/track-x-v0.2-heldout-session-a"),
        encoding="utf-8",
    )
    declaration = validate_authorship_note(
        path,
        expected_base_commit=base,
    )
    assert declaration.base_freeze_commit == base
    assert declaration.heldout_branch == "research/track-x-v0.2-heldout-session-a"
    assert declaration.changed_paths == (
        "data/track_x_v02/heldout/AUTHORSHIP.md",
        "data/track_x_v02/heldout/session_a.json",
    )


def test_authorship_note_rejects_wrong_base_or_unreserved_branch(tmp_path: Path):
    path = tmp_path / "AUTHORSHIP.md"
    path.write_text(
        _note("1" * 40, "research/unreserved"),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        validate_authorship_note(path, expected_base_commit="3" * 40)
    with pytest.raises(ValueError):
        validate_authorship_note(path)


def test_authorship_note_does_not_require_its_own_commit_hash(tmp_path: Path):
    path = tmp_path / "AUTHORSHIP.md"
    text = _note("1" * 40, "research/track-x-v0.2-heldout-session-a")
    assert "Held-out commit:" not in text
    path.write_text(text, encoding="utf-8")
    validate_authorship_note(path)


def test_freeze_contract_reserves_only_session_a_data_and_authorship():
    freeze = json.loads(
        (ROOT / "data" / "track_x_v02" / "FREEZE_V02.json").read_text(
            encoding="utf-8"
        )
    )
    assert set(freeze["allowed_session_a_paths"]) == {
        "data/track_x_v02/heldout/session_a.json",
        "data/track_x_v02/heldout/AUTHORSHIP.md",
    }
    assert set(freeze["allowed_session_a_paths"]).isdisjoint(
        freeze["frozen_paths"]
    )
