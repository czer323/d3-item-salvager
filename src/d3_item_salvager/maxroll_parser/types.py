"""Typed data structures and enumerations for Maxroll parsing domain.

Defines public, type-safe contracts for guide metadata, build profiles, item usages,
and item metadata. Implementation details are intentionally avoided for stable, documented shapes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

__all__: Final = [
    "BuildProfileData",
    "BuildProfileItems",
    "GuideInfo",
    "ItemMeta",
    "ItemSlot",
    "ItemUsageContext",
]


class ItemUsageContext(StrEnum):
    """
    Enumerates the contexts in which an item can appear in a build.

    Using StrEnum (Python 3.11+) preserves the string value for easy serialization/comparison.
    """

    MAIN = "main"  # Equipped on the hero
    KANAI = "kanai"  # Imprinted in Kanai's Cube
    FOLLOWER = "follower"  # Equipped on follower


class ItemSlot(StrEnum):
    """
    Enumerates recognized gear slots.

    Additional/unknown slots fall back to OTHER for forward compatibility.
    """

    HEAD = "head"
    SHOULDERS = "shoulders"
    NECK = "neck"
    TORSO = "torso"
    WAIST = "waist"
    HANDS = "hands"
    WRISTS = "wrists"
    LEGS = "legs"
    FEET = "feet"
    LEFT_FINGER = "leftfinger"
    RIGHT_FINGER = "rightfinger"
    MAIN_HAND = "mainhand"
    OFF_HAND = "offhand"
    WEAPON = "weapon"  # Generic weapon slot (some upstream data uses this)
    ARMOR = "armor"  # Generic armor slot placeholder
    JEWELRY = "jewelry"  # Generic jewelry placeholder
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class GuideInfo:
    """
    Represents a Diablo 3 build guide with its display name and URL.

    Attributes:
        name: Display name of the guide.
        url: URL of the guide.
    """

    name: str
    url: str


@dataclass(frozen=True, slots=True)
class BuildProfileData:
    """
    Normalized build profile metadata.

    Only fields reliably derivable from the profile JSON are included.
    Optional attributes default to None when absent.
    raw_profile_index preserves ordering information for deterministic processing
    or cross-referencing.

    Attributes:
        name: Name of the build profile.
        class_name: Class name for the build profile.
        seasonal: Whether the build is seasonal.
        gender: Gender for the build profile.
        paragon_level: Paragon level for the build profile.
        raw_profile_index: Index in the original profile array.
    """

    name: str
    class_name: str
    seasonal: bool | None = None
    gender: str | None = None
    paragon_level: int | None = None
    raw_profile_index: int | None = None


@dataclass(frozen=True, slots=True)
class BuildProfileItems:
    """
    Represents an individual item usage within a build profile.

    Attributes:
        profile_name: Name of the build profile.
        item_id: ID of the item.
        slot: Gear slot for the item.
        usage_context: Context in which the item is used.
    """

    profile_name: str
    item_id: str
    slot: ItemSlot
    usage_context: ItemUsageContext


@dataclass(frozen=True, slots=True)
class ItemMeta:
    """
    Minimal metadata for an item referenced by profiles.

    Additional attributes can be introduced later without breaking consumers.

    Attributes:
        id: Item ID.
        name: Name of the item.
        type: Type of the item.
        quality: Quality of the item.
    """

    id: str
    name: str | None = None
    type: str | None = None
    quality: str | None = None
