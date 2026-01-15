"""Failing unit tests for de-duplication and ordering logic (T012a).

These tests assert the presence of a small utility `dedupe_and_sort` which accepts
an iterable of item dicts and returns a de-duplicated, alphabetically-sorted list
by item 'name'. This is intended to be used by both server-side and client-side
sanity checks.
"""

from __future__ import annotations

from d3_item_salvager.utility.collections import dedupe_and_sort


def test_dedupe_and_sort_removes_duplicates_and_sorts() -> None:
    items = [
        {"id": "i1", "name": "B Item"},
        {"id": "i2", "name": "A Item"},
        {"id": "i1", "name": "B Item"},
    ]

    result = dedupe_and_sort(items)
    assert isinstance(result, list)
    names = [it["name"] for it in result]
    assert names == ["A Item", "B Item"]


def test_dedupe_and_sort_preserves_quality_and_slot() -> None:
    items = [
        {"id": "i1", "name": "A Item", "quality": "legendary", "slot": "helm"},
        {"id": "i2", "name": "A Item", "quality": "set", "slot": "helm"},
    ]

    result = dedupe_and_sort(items)
    # When duplicate names exist, prefer the first-seen (stable behavior) and preserve slot/quality
    assert result[0]["quality"] == "legendary"
    assert result[0]["slot"] == "helm"
