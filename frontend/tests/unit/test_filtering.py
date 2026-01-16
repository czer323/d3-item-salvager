"""Unit tests for filtering utilities used by the frontend."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from frontend.src.services.filtering import FilterCriteria, apply_filters, fuzzy_score


@dataclass(slots=True)
class _Item:
    name: str
    slot: str


@pytest.mark.parametrize(
    ("candidate", "query", "expected_minimum"),
    [
        ("The Furnace", "furn", 80),
        ("Frostburn Gauntlets", "furn", 30),
        ("Ring of Royal Grandeur", "ring", 90),
    ],
)
def test_fuzzy_score_prefers_prefix_and_substring_matches(
    candidate: str, query: str, expected_minimum: int
) -> None:
    """Prefix and substring matches should produce strong scores."""
    score = fuzzy_score(candidate, query)
    assert score >= expected_minimum


def test_apply_filters_combines_slot_and_search_terms() -> None:
    """Slot filtering and fuzzy search terms operate together."""
    items = [
        _Item(name="Ring of Royal Grandeur", slot="Ring"),
        _Item(name="Convention of Elements", slot="Ring"),
        _Item(name="Furnace", slot="Two-Handed Weapon"),
    ]
    criteria = FilterCriteria(search="furn", slot="Two-Handed Weapon")

    filtered = apply_filters(items, criteria)

    assert len(filtered) == 1
    assert filtered[0].name == "Furnace"


def test_apply_filters_returns_all_items_when_criteria_empty() -> None:
    """Empty criteria should return the original collection."""
    items = [
        _Item(name="Squirt's Necklace", slot="Amulet"),
        _Item(name="Stone of Jordan", slot="Ring"),
    ]

    filtered = apply_filters(items, FilterCriteria())

    assert filtered == items


def test_apply_filters_with_usage_and_classes() -> None:
    """Usage and class filters should be applied correctly."""

    @dataclass(slots=True)
    class _UsedItem:
        name: str
        slot: str
        usage_contexts: tuple[str, ...]
        usage_classes: tuple[str, ...]

    items = [
        _UsedItem(
            name="Mighty Weapon",
            slot="mainhand",
            usage_contexts=("main",),
            usage_classes=("Barbarian",),
        ),
        _UsedItem(
            name="Chantodo's Will",
            slot="mainhand",
            usage_contexts=("kanai",),
            usage_classes=("Wizard",),
        ),
        _UsedItem(
            name="Follower Talisman",
            slot="offhand",
            usage_contexts=("follower",),
            usage_classes=("Monk",),
        ),
    ]

    # Filter by usage type
    criteria = FilterCriteria(usage_types={"kanai"})
    filtered = apply_filters(items, criteria)
    assert len(filtered) == 1
    assert filtered[0].name == "Chantodo's Will"

    # Filter by class
    criteria = FilterCriteria(usage_classes={"barbarian"})
    filtered = apply_filters(items, criteria)
    assert len(filtered) == 1
    assert filtered[0].name == "Mighty Weapon"

    # Filter by usage and class (no match)
    criteria = FilterCriteria(usage_types={"main"}, usage_classes={"wizard"})
    filtered = apply_filters(items, criteria)
    assert len(filtered) == 0
