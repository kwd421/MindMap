from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUIRED_DECLARATION = "[Session A] ACCEPT WITH PASSAGE CONTRIBUTION"
_REQUIRED_NONINTERFERENCE = (
    "I did not edit or use the Track X v0.2 primary extractor, verifier,"
)


@dataclass(frozen=True, slots=True)
class AuthorshipDeclaration:
    base_freeze_commit: str
    heldout_branch: str
    changed_paths: tuple[str, ...]


def _field(lines: tuple[str, ...], prefix: str) -> str:
    for line in lines:
        if line.startswith(prefix):
            return line[len(prefix) :].strip().strip("`")
    raise ValueError(f"authorship note lacks field: {prefix}")


def validate_authorship_note(
    path: Path,
    *,
    expected_base_commit: str | None = None,
) -> AuthorshipDeclaration:
    """Validate the pre-commit authorship declaration.

    The note deliberately does not contain its own final commit hash. That hash
    is computed by Git/CI and recorded in the GitHub handoff and result metadata;
    requiring it inside the committed file would be self-referential.
    """

    text = path.read_text(encoding="utf-8")
    if _REQUIRED_DECLARATION not in text:
        raise ValueError("authorship note lacks explicit Session A acceptance")
    if _REQUIRED_NONINTERFERENCE not in text:
        raise ValueError("authorship note lacks non-interference declaration")

    lines = tuple(line.strip() for line in text.splitlines())
    base = _field(lines, "Base/freeze commit:")
    branch = _field(lines, "Held-out branch:")
    if not _COMMIT_RE.fullmatch(base):
        raise ValueError("Base/freeze commit must be a full lowercase SHA-1")
    if expected_base_commit is not None and base != expected_base_commit:
        raise ValueError(
            f"authorship base {base} does not match frozen base "
            f"{expected_base_commit}"
        )
    if not branch.startswith("research/track-x-v0.2-heldout-"):
        raise ValueError("held-out branch must use the reserved branch prefix")

    allowed = {
        "data/track_x_v02/heldout/session_a.json",
        "data/track_x_v02/heldout/AUTHORSHIP.md",
    }
    declared_paths = tuple(
        line.removeprefix("- ").strip("`")
        for line in lines
        if line.startswith("- data/track_x_v02/heldout/")
    )
    if set(declared_paths) != allowed:
        raise ValueError(
            "authorship note must declare exactly the two allowed held-out paths"
        )
    return AuthorshipDeclaration(
        base_freeze_commit=base,
        heldout_branch=branch,
        changed_paths=tuple(sorted(declared_paths)),
    )
