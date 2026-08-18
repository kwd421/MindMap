from __future__ import annotations

import re

from .v02_pipeline import DevelopmentIndependentVerifier


class NormalizedDevelopmentVerifier(DevelopmentIndependentVerifier):
    """Normalize orthographic variation without sharing primary parser logic."""

    implementation_name = "development_independent_verifier_v0.2-normalized"

    def _reconstruct(self, text: str):
        normalized = re.sub(r"\bReplica\b", "replica", text)
        return super()._reconstruct(normalized)
