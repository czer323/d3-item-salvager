"""
Module for loading and parsing the master data.json file into lookup structures.
"""

import json
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).parent.parent.parent.parent / "reference" / "data.json"


def load_master_data(
    data_path: Path = DATA_PATH,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Load and parse the master data.json file.
    Args:
        data_path: Path to the data.json file.
    Returns:
        Tuple of (item_dict, class_dict):
            item_dict: Dict mapping item IDs to item data.
            class_dict: Dict mapping class keys to class data.
    Raises:
        TypeError: If the data structure is invalid or required fields are missing.
    """
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)

    # Validate top-level structure
    if not isinstance(data, dict):
        msg = "data.json must be a JSON object at the top level."
        raise TypeError(msg)

    # 'items' is optional and may not exist
    items = data.get("items")
    if items is not None:
        if not isinstance(items, list):
            msg = "If present, 'items' must be a list."
            raise TypeError(msg)
        item_dict = {item.get("id"): item for item in items if item.get("id")}
    else:
        item_dict = {}

    # 'classes' is a dict in this data.json
    classes = data.get("classes")
    if not isinstance(classes, dict):
        msg = "'classes' must be a dict."
        raise TypeError(msg)
    class_dict = classes

    return item_dict, class_dict


# Example usage (for testing):
if __name__ == "__main__":
    loaded_items, loaded_classes = load_master_data()
    print(f"Loaded {len(loaded_items)} items and {len(loaded_classes)} classes.")
