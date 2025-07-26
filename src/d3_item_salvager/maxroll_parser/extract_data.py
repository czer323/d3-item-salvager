"""
Module for loading and parsing the game data data.json file into lookup structures.
"""

import json
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).parent.parent.parent.parent / "reference" / "data.json"


class DataParser:
    """
    DataParser loads and parses the master data.json file into lookup structures.

    Attributes:
        data_path (Path): Path to the data.json file.
        raw_data (dict): Raw loaded JSON data.
        items (dict[str, dict[str, str]]): Filtered item dictionary.
    """

    def __init__(self, data_path: Path | None = None) -> None:
        """
        Initialize the DataParser and load data from the specified path.

        Args:
            data_path: Optional path to the data.json file. Defaults to DATA_PATH.
        """
        self.data_path: Path = data_path or DATA_PATH
        self.raw_data: dict[str, Any] = self._load_json()
        self.items: dict[str, dict[str, str]] = self._extract_and_filter_items()

    def _load_json(self) -> dict[str, Any]:
        """
        Load and validate the master data.json file.

        Returns:
            dict: Loaded and validated JSON data.

        Raises:
            TypeError: If the data structure is invalid.
        """
        with open(self.data_path, encoding="utf-8") as f:
            raw = json.load(f)
        return self._validate_json_dict(raw)

    @staticmethod
    def _validate_json_dict(data: object) -> dict:
        """
        Validate that the loaded JSON data is a dictionary.

        Args:
            data: Loaded JSON object.

        Returns:
            dict: Validated dictionary.

        Raises:
            TypeError: If not a dictionary.
        """
        if not isinstance(data, dict):
            msg = "data.json must be a JSON object at the top level."
            raise TypeError(msg)
        return data

    def _extract_and_filter_items(self) -> dict[str, dict[str, str]]:
        """
        Extract and filter items from the loaded data.

        Returns:
            dict[str, dict[str, str]]: Filtered item dictionary.
        """
        item_dict = self._extract_items(self.raw_data)
        return self._filter_item_fields(item_dict)

    @staticmethod
    def _extract_items(data: dict) -> dict[str, dict]:
        """
        Extract items from the loaded data.

        Args:
            data: Loaded JSON dictionary.

        Returns:
            dict[str, dict]: Dictionary mapping item IDs to item data.

        Raises:
            TypeError: If 'items' is not a list.
        """
        items = data.get("items")
        if items is None:
            return {}
        if not isinstance(items, list):
            msg = "If present, 'items' must be a list."
            raise TypeError(msg)
        return {item.get("id"): item for item in items if item.get("id")}

    @staticmethod
    def _filter_item_fields(item_dict: dict[str, Any]) -> dict[str, dict[str, str]]:
        """
        Filter and clean item data to only keep id, name, type, quality as strings.

        Args:
            item_dict: Dictionary of item data.

        Returns:
            dict[str, dict[str, str]]: Filtered item dictionary.
        """

        def to_str(val: str | int | float | list | dict | None) -> str:
            if isinstance(val, list):
                return ", ".join(str(x) for x in val)
            if isinstance(val, dict):
                return str(val)
            return str(val) if val is not None else ""

        filtered: dict[str, dict[str, str]] = {}
        for item_id, item in item_dict.items():
            filtered[item_id] = {
                "id": to_str(item.get("id")),
                "name": to_str(item.get("name")),
                "type": to_str(item.get("type")),
                "quality": to_str(item.get("quality")),
            }
        return filtered

    def get_item(self, item_id: str) -> dict[str, str] | None:
        """
        Get filtered item data by item ID.

        Args:
            item_id: The item ID to look up.

        Returns:
            dict[str, str] or None: Item data if found, else None.
        """
        return self.items.get(item_id)

    def get_all_items(self) -> dict[str, dict[str, str]]:
        """
        Get all filtered item data.

        Returns:
            dict[str, dict[str, str]]: All item data.
        """
        return self.items
