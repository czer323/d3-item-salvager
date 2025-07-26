"""Defines data structures for Diablo 3 build profiles and guides."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GuideInfo:
    """Represents a Diablo 3 build guide with its name and URL."""

    name: str
    url: str


@dataclass
class BuildProfileData:
    """
    Represents a Diablo 3 build profile with basic information.

    Attributes:
        name: Name of the build profile.
        class_name: Class name associated with the profile (e.g., Barbarian, Wizard).
    """

    name: str
    class_name: str


@dataclass
class BuildProfileItems:
    """
    Represents an item usage in a build profile.

    Attributes:
        profile_name: Name of the build profile.
        item_id: Item ID used in the profile.
        slot: Slot where the item is used (e.g., main hand, off hand).
        usage_context: Context of usage (e.g., main, kanai, follower).
    """

    profile_name: str
    item_id: str
    slot: str
    usage_context: str
