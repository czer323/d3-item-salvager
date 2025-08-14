"""Unit tests for DataParser covering positive and negative cases."""

import json
from pathlib import Path

import pytest

from d3_item_salvager.maxroll_parser.item_data_parser import DataParser
from d3_item_salvager.maxroll_parser.maxroll_exceptions import ItemDataError


def make_data_json(tmp_path: Path, items: list[dict[str, object]]) -> Path:
    """Create a data.json file with the given items for testing.

    Args:
        tmp_path: Temporary directory path for test files.
        items: List of item dictionaries to write.

    Returns:
        Path to the created data.json file.
    """
    path = tmp_path / "data.json"
    data = {"items": items}
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


def test_data_parser_positive(tmp_path: Path) -> None:
    """Test DataParser with valid items data.

    Verifies that items are parsed correctly and accessible by ID and attributes.
    """
    items: list[dict[str, object]] = [
        {"id": "item1", "name": "Sword", "type": "weapon", "quality": "legendary"},
        {"id": "item2", "name": "Shield", "type": "armor", "quality": "rare"},
    ]
    path = make_data_json(tmp_path, items)
    parser = DataParser(path)
    assert parser["item1"].name == "Sword"
    assert parser["item2"].type == "armor"
    item1 = parser.get_item("item1")
    assert item1 is not None
    assert item1.quality == "legendary"
    all_items = parser.get_all_items()
    assert "item1" in all_items
    assert "item2" in all_items


def test_data_parser_missing_items_key(tmp_path: Path) -> None:
    """Test DataParser with missing 'items' key in data.

    Verifies that get_all_items returns empty when 'items' key is absent.
    """
    path = tmp_path / "bad_data.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump({}, f)
    parser = DataParser(path)
    assert not parser.get_all_items()


def test_data_parser_items_not_list(tmp_path: Path) -> None:
    """Test DataParser with 'items' key not being a list.

    Verifies that ItemDataError is raised when 'items' is not a list.
    """
    data = {"items": "notalist"}
    path = tmp_path / "bad_type.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f)
    with pytest.raises(ItemDataError, match="'items' must be a list"):
        DataParser(path)


def test_data_parser_item_missing_id(tmp_path: Path) -> None:
    """Test DataParser with item missing 'id' field.

    Verifies that items without 'id' are ignored and get_all_items returns empty.
    """
    items: list[dict[str, object]] = [
        {"name": "Sword", "type": "weapon", "quality": "legendary"}
    ]
    path = make_data_json(tmp_path, items)
    parser = DataParser(path)
    assert not parser.get_all_items()
