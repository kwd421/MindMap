from __future__ import annotations

import json
import subprocess
import sys


_SCRIPT = r'''
import json
import sys

order = sys.argv[1]

if order == "direct-first":
    from mindmap.track_x.gatemem_governance import PublicTurnPolicyParser
    from mindmap.track_x.gatemem_public import PublicEpisode, PublicPrincipal, PublicTurn
else:
    import mindmap.track_x
    from mindmap.track_x.gatemem_governance import PublicTurnPolicyParser
    from mindmap.track_x.gatemem_public import PublicEpisode, PublicPrincipal, PublicTurn


def episode():
    return PublicEpisode(
        episode_id="opaque-episode",
        domain="medical",
        principals=(
            PublicPrincipal("opaque-patient", "patient", "Alice"),
            PublicPrincipal("opaque-doctor", "doctor", "Dr. Bob"),
        ),
    )


def turn(index, text):
    return PublicTurn(
        turn_id=f"t{index}",
        timestamp=f"2026-01-0{index + 1}T00:00:00Z",
        speaker_principal_id="opaque-patient",
        speaker_role="patient",
        turn_kind="dialogue",
        text=text,
    )


def snapshot():
    parser = PublicTurnPolicyParser(episode())
    texts = (
        "Please remove the stitches tomorrow.",
        "Only share the migraine diagnosis with doctors.",
        "Please delete the migraine diagnosis record.",
    )
    output = []
    for index, text in enumerate(texts, start=1):
        signals = parser.parse(turn(index, text), observed_index=index)
        output.append(
            [
                {
                    "operation": signal.operation.value,
                    "scope": signal.restriction_scope.value,
                    "targets": list(signal.target_roles),
                    "anchors": list(signal.anchor_tokens),
                }
                for signal in signals
            ]
        )
    return output


before = snapshot()
import mindmap.track_x
from mindmap.track_x.gatemem_governance import PublicTurnPolicyParser as ParserAfter
assert ParserAfter is PublicTurnPolicyParser
after = snapshot()
print(json.dumps({"before": before, "after": after}, sort_keys=True))
'''


def _run(order: str) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "-c", _SCRIPT, order],
        check=True,
        capture_output=True,
        text=True,
    )
    value = json.loads(completed.stdout)
    assert isinstance(value, dict)
    return value


def test_base_parser_is_unchanged_by_package_import_order():
    direct_first = _run("direct-first")
    package_first = _run("package-first")

    assert direct_first["before"] == direct_first["after"]
    assert package_first["before"] == package_first["after"]
    assert direct_first == package_first
