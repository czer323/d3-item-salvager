"""UI Service for aggregating salvage data for the frontend."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ComputedField, ConfigDict

from d3_item_salvager.data import queries

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from sqlmodel import Session


class SalvageLabel(str, Enum):
    """Enumeration of supported salvage disposition labels."""

    KEEP = "keep"
    FOLLOWER = "follower"
    KANAI = "kanai"
    SALVAGE = "salvage"

    @property
    def display_name(self) -> str:
        """Return a human-friendly label."""
        return {
            SalvageLabel.KEEP: "Keep",
            SalvageLabel.FOLLOWER: "Follower",
            SalvageLabel.KANAI: "Kanai",
            SalvageLabel.SALVAGE: "Salvage",
        }[self]


def classify_usage_contexts(contexts: set[str]) -> SalvageLabel:
    """Derive a salvage label from usage contexts."""
    normalized = {context.lower() for context in contexts}
    # Logic ported from salvage_classifier.py
    # Note: Logic ordering matters.
    # If it is EVER "kanai" -> Kanai (unless it is also others?)
    # Original logic:
    # if "unused" -> SALVAGE
    # if "kanai" -> KANAI
    # if "follower" -> FOLLOWER
    # default -> KEEP
    if "unused" in normalized:
        return SalvageLabel.SALVAGE
    if "kanai" in normalized:
        return SalvageLabel.KANAI
    if "follower" in normalized:
        return SalvageLabel.FOLLOWER
    return SalvageLabel.KEEP


class ItemTableEntry(BaseModel):
    """Row model for the frontend item table."""

    model_config = ConfigDict(from_attributes=True)

    item_id: str
    name: str
    slot: str
    usage_contexts: list[str]
    classification: SalvageLabel
    variant_ids: list[int]

    @ComputedField  # type: ignore[misc]
    @property
    def badge_class(self) -> str:
        """Return details for frontend styling."""
        return {
            SalvageLabel.KEEP: "badge-success",
            SalvageLabel.FOLLOWER: "badge-info",
            SalvageLabel.KANAI: "badge-warning",
            SalvageLabel.SALVAGE: "badge-error",
        }.get(self.classification, "badge-ghost")

    @ComputedField  # type: ignore[misc]
    @property
    def usage_label(self) -> str:
        """Return formatted usage string."""
        return ", ".join(ctx.title() for ctx in self.usage_contexts)


class UIService:
    """Service to handle UI data aggregation."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_salvage_table(self, variant_ids: Sequence[int]) -> list[ItemTableEntry]:
        """
        Aggregate item usages for multiple variants into a flat list of items.
        Items are deduplicated and classified based on their combined usage.
        """
        # Dictionary to accumulate usage data: item_id -> data
        accumulator: dict[str, dict] = {}

        for vid in variant_ids:
            # Check if variant exists? Queries might raise or return empty.
            # We trust the IDs generally.
            rows = queries.list_item_usage_with_items(self.session, vid)

            for usage, item in rows:
                if item.id is None:
                    continue

                item_id = item.id
                context = (usage.usage_context or "unknown").lower()

                if item_id not in accumulator:
                    accumulator[item_id] = {
                        "name": item.name,
                        "slot": item.type or usage.slot or "Unknown",
                        "contexts": set(),
                        "variant_ids": set(),
                    }

                accumulator[item_id]["contexts"].add(context)
                accumulator[item_id]["variant_ids"].add(vid)

        # Convert accumulator to output list
        results: list[ItemTableEntry] = []

        for item_id, data in accumulator.items():
            classification = classify_usage_contexts(data["contexts"])

            # Per original logic, we might exclude 'salvage' explicitly?
            # User wants "what items a player needs to focus on keeping... which to give to follower..."
            # Usually "Salvage" means "You don't need this".
            # The original code did: "Exclude 'salvage' classification from the visible lists"
            if classification == SalvageLabel.SALVAGE:
                continue

            entry = ItemTableEntry(
                item_id=item_id,
                name=data["name"],
                slot=data["slot"],
                usage_contexts=sorted(list(data["contexts"])),
                classification=classification,
                variant_ids=sorted(list(data["variant_ids"])),
            )
            results.append(entry)

        return sorted(results, key=lambda x: x.name)
