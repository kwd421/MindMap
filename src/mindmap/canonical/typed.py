from __future__ import annotations

from .typed_projection import TypedProjectionMixin
from .typed_resolution import TypedResolutionMixin


class TypedLedger(TypedResolutionMixin, TypedProjectionMixin):
    """Normalized typed implementation (T) of the canonical finite semantics."""
