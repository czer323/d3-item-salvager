"""
Module for loading and parsing the master data.json file into lookup structures.
"""

import json
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).parent.parent.parent.parent / "reference" / "data.json"


def load_master_data(
    data_path: Path = DATA_PATH,
) -> dict[str, Any]:
    """
    Load and parse the master data.json file.

    Args:
        data_path: Path to the data.json file.

    Returns:
        item_dict: Dict mapping item IDs to item data.

    Raises:
        TypeError: If the data structure is invalid or required fields are missing.
    """
    with open(data_path, encoding="utf-8") as f:
        raw = json.load(f)
    data = validate_json_dict(raw)
    item_dict = extract_items(data)
    filtered_item_dict = filter_item_fields(item_dict)
    return filtered_item_dict


def validate_json_dict(data: object) -> dict:
    """Validate that the loaded JSON data is a dictionary."""
    if not isinstance(data, dict):
        msg = "data.json must be a JSON object at the top level."
        raise TypeError(msg)
    return data


def extract_items(data: dict) -> dict[str, dict]:
    """Extract items from the loaded data."""
    items = data.get("items")
    if items is None:
        return {}
    if not isinstance(items, list):
        msg = "If present, 'items' must be a list."
        raise TypeError(msg)
    return {item.get("id"): item for item in items if item.get("id")}


def filter_item_fields(item_dict: dict[str, Any]) -> dict[str, dict[str, str]]:
    """
    Helper to filter and clean item data to only keep id, name, type, quality as strings.
    """

    def to_str(val: str | int | float | list | dict | None) -> str:
        if isinstance(val, list):
            return ", ".join(str(x) for x in val)
        if isinstance(val, dict):
            return str(val)
        return str(val) if val is not None else ""

    filtered = {}
    for item_id, item in item_dict.items():
        filtered[item_id] = {
            "id": to_str(item.get("id")),
            "name": to_str(item.get("name")),
            "type": to_str(item.get("type")),
            "quality": to_str(item.get("quality")),
        }
    return filtered
