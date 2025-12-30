"""Utilities for classifying item salvage disposition."""

from __future__ import annotations

from enum import Enum


class SalvageLabel(str, Enum):
    """Enumeration of supported salvage disposition labels."""

    KEEP = "keep"
    FOLLOWER = "follower"
    KANAI = "kanai"
    SALVAGE = "salvage"

    @property
    def display_name(self) -> str:
        """Return a human-friendly label."""
        return _DISPLAY_NAMES[self]


_DISPLAY_NAMES: dict[SalvageLabel, str] = {
    SalvageLabel.KEEP: "Keep",
    SalvageLabel.FOLLOWER: "Follower",
    SalvageLabel.KANAI: "Kanai",
    SalvageLabel.SALVAGE: "Salvage",
}


def classify_usage_contexts(contexts: tuple[str, ...]) -> SalvageLabel:
    """Derive a salvage label from usage contexts."""
    normalized = {context.lower() for context in contexts}
    if "unused" in normalized:
        return SalvageLabel.SALVAGE
    if "kanai" in normalized:
        return SalvageLabel.KANAI
    if "follower" in normalized:
        return SalvageLabel.FOLLOWER
    return SalvageLabel.KEEP
