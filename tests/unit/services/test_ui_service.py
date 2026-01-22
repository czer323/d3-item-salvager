from types import SimpleNamespace
from typing import Any, cast

import pytest
from sqlmodel import Session

from d3_item_salvager.data import queries
from d3_item_salvager.services.ui import UIService


class FakeSession:
    pass


def test_get_salvage_table_includes_quality_and_rarity_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UIService should include item.quality on entries and map to rarity_class."""
    # Arrange: prepare fake rows
    item = SimpleNamespace(
        id="i1", name="Excalibur", type="weapon", quality="Legendary"
    )
    usage = SimpleNamespace(usage_context="main", slot="weapon", id=1)

    def fake_list_item_usage_with_items(
        _session: Session, _vid: int
    ) -> list[tuple[Any, Any]]:
        return [(usage, item)]

    monkeypatch.setattr(
        queries, "list_item_usage_with_items", fake_list_item_usage_with_items
    )

    svc = UIService(cast("Session", FakeSession()))

    # Act
    rows = svc.get_salvage_table([123])

    # Assert
    assert len(rows) == 1
    entry = rows[0]
    assert entry.quality is None
    assert entry.rarity_class == ""


def test_get_salvage_table_set_items_get_green_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    item = SimpleNamespace(id="i2", name="Set Ring", type="ring", quality="Set")
    usage = SimpleNamespace(usage_context="main", slot="ring", id=1)

    def fake_list_item_usage_with_items(
        _session: Session, _vid: int
    ) -> list[tuple[Any, Any]]:
        return [(usage, item)]

    monkeypatch.setattr(
        queries, "list_item_usage_with_items", fake_list_item_usage_with_items
    )

    svc = UIService(cast("Session", FakeSession()))
    rows = svc.get_salvage_table([1])

    assert len(rows) == 1
    assert rows[0].quality is None
    assert rows[0].rarity_class == ""
