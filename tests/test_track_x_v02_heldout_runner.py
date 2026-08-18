import json
from pathlib import Path

from mindmap.track_x.v02_evaluate import evaluate_heldout


_BUNDLES = (
    ("F08", "restore_manifest_gap", "F08.l", "F08.q1", "snapshot_cutoff", 1),
    (
        "F09",
        "cross_world_reference_context",
        "F09.xb",
        "F09.q4",
        "destination_mind_instance_id",
        "wrong-mind",
    ),
    (
        "F10",
        "protected_only_revocation",
        "F10.r",
        "F10.q4",
        "policy_operation",
        "grant",
    ),
    (
        "F11",
        "independent_public_survives",
        "F11.rs",
        "F11.q4",
        "object_id",
        "wrong-object",
    ),
    (
        "F12",
        "same_origin_dedup",
        "F12.del",
        "F12.q4",
        "object_id",
        "wrong-object",
    ),
    (
        "F13",
        "authorized_replication",
        "F13.rep",
        "F13.q2",
        "authorization_id",
        "AUTH.WRONG",
    ),
    (
        "F14",
        "temporal_negative_controls",
        "F14.w2",
        "F14.q2",
        "attributes.value",
        "wrong-value",
    ),
)


def _write_unseen_bundles(root: Path) -> None:
    rows = []
    for fixture, topology, event, query, field, replacement in _BUNDLES:
        rows.append(
            {
                "bundle_id": f"SMOKE-{fixture}",
                "fixture_id": fixture,
                "topology_family": topology,
                "event_id": event,
                "query_id": query,
                "author_session": "A",
                "complete_text": (
                    f"A Session A operator wrote an unfamiliar prose note for {event}. "
                    "The smoke test intentionally does not make this sentence parseable."
                ),
                "ambiguous_text": (
                    f"Someone mentioned {event}, but the material scope was omitted."
                ),
                "distractor_passages": [
                    "A nearby unrelated note repeats a plausible but non-authoritative value."
                ],
                "candidate_mutation": {
                    "field_name": field,
                    "replacement": replacement,
                },
                "notes": "Evaluator plumbing smoke test only; not a held-out result.",
            }
        )
    path = root / "data" / "track_x_v02" / "heldout" / "session_a.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")


def test_frozen_heldout_evaluator_completes_on_unseen_unparseable_wording(
    tmp_path: Path,
):
    _write_unseen_bundles(tmp_path)
    verification_rows, downstream_rows, summary = evaluate_heldout(tmp_path)
    assert len(verification_rows) == 42
    assert len(downstream_rows) == 42 * 5 * 2
    assert summary["n_topologies"] == 7
    assert summary["generic_typed_disagreements"] == {}
    # This is deliberately unparseable wording; safe abstention is expected,
    # and no accuracy claim is made from the smoke fixture.
    assert summary["verification"]["primary_verifier"]["coverage"] == 0.0
