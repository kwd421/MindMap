from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "run_gatemem_deletion_surface_audit",
    ROOT / "tools" / "run_gatemem_deletion_surface_audit.py",
)
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(AUDIT)


def test_strict_directive_includes_sentence_initial_imperatives() -> None:
    assert AUDIT.strict_directive("Delete the retired code from memory.")
    assert AUDIT.strict_directive("Please remove the old note from memory.")
    assert AUDIT.strict_directive(
        "Rotation is complete. Forget the previous credential from memory."
    )
    assert AUDIT.strict_directive(
        "Deletion request on history: erase the old amount from shared memory."
    )


def test_strict_directive_excludes_descriptions_and_indirect_language() -> None:
    assert not AUDIT.strict_directive("The retired code is deleted from memory.")
    assert not AUDIT.strict_directive("The contract removes auto-renewal.")
    assert not AUDIT.strict_directive("I want the old wording removed from memory.")
    assert not AUDIT.strict_directive("Do not restore the deleted note.")
