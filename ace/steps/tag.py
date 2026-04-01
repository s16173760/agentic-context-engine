"""TagStep — placeholder for future skill tagging from reflector output."""

from __future__ import annotations

from ..core.context import ACEStepContext


class TagStep:
    """Pass-through step — skill tag counters were removed from the Skillbook.

    Kept as a pipeline placeholder so existing pipeline compositions and
    ``learning_tail()`` continue to work without modification.
    """

    requires: frozenset[str] = frozenset({"reflections"})
    provides: frozenset[str] = frozenset()

    max_workers = 1

    def __init__(self, skillbook: object = None) -> None:
        # Accept skillbook arg for backward compat with learning_tail() wiring
        pass

    def __call__(self, ctx: ACEStepContext) -> ACEStepContext:
        return ctx
