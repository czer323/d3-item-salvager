"""Unit tests for table sorting and filtering behaviors (T021).

These tests exercise the Python mirror of the client-side algorithms so we can
unit test logic without a JS runtime. They also serve as a specification for
what the JS helpers should implement.
"""

from __future__ import annotations

from frontend.src.services.backend_catalog import ItemRecord
from frontend.src.services.item_usage import (
    UsageAccumulator,
    merge_catalogue_with_usage,
)


def test_server_merges_and_sorts_by_name_deterministically() -> None:
    """Verify that _merge_catalogue_with_usage returns rows sorted by name (case-insensitive)
    and uses item id as a tie-breaker so ordering is deterministic.

    """
    # Catalogue contains two items with same name to exercise tie-breaker
    catalogue = [
        ItemRecord(id="id2", name="Chanon Bolter", slot="Crossbow"),
        ItemRecord(id="id1", name="Chanon Bolter", slot="Crossbow"),
        ItemRecord(id="a", name="Alpha", slot="Weapon"),
    ]

    usage = {
        "id2": UsageAccumulator(
            name="Chanon Bolter", slot="Crossbow", contexts=set(), variant_ids=set()
        ),
        "id1": UsageAccumulator(
            name="Chanon Bolter", slot="Crossbow", contexts=set(), variant_ids=set()
        ),
        "a": UsageAccumulator(
            name="Alpha", slot="Weapon", contexts=set(), variant_ids=set()
        ),
    }

    rows = merge_catalogue_with_usage(catalogue, usage)
    names_ids = [(r.name, r.item_id) for r in rows]

    # Expect alphabetical by name, and for identical names, id1 before id2 (id1 < id2)
    assert names_ids == [
        ("Alpha", "a"),
        ("Chanon Bolter", "id1"),
        ("Chanon Bolter", "id2"),
    ]
