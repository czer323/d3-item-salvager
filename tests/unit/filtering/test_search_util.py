"""Test-first unit tests for backend fuzzy util (mirrors frontend tests)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from d3_item_salvager.utility.search import FilterCriteria, apply_filters, fuzzy_score


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
