"""
Loads and parses the game data.json file into lookup structures.

Produces immutable ItemMeta instances keyed by item id.
"""

import json
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any

import requests

from .maxroll_exceptions import ItemDataError
from .types import ItemMeta

__all__ = ["DataParser", "ItemMeta"]

DATA_PATH = Path(__file__).parent.parent.parent.parent / "reference" / "data.json"


class DataParser(Mapping[str, ItemMeta]):
    """
    Loads and validates data.json master item data.

    Implements Mapping so it can be passed where a read-only mapping of id->meta is expected.

    Args:
        data_path: Optional path to the data.json file. If not provided, uses default DATA_PATH.
    """

    def __init__(self, data_path: str | Path | None = None) -> None:
        self.data_path: str | Path = data_path or DATA_PATH
        self.raw_data: dict[str, Any] = self._load_json()
        self._items: dict[str, ItemMeta] = self._extract_and_filter_items()

    # -- Mapping protocol -------------------------------------------------
    def __getitem__(self, k: str) -> ItemMeta:
        return self._items[k]

    def __iter__(self) -> Iterator[str]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    # ---------------------------------------------------------------------
    def _load_json(self) -> dict[str, Any]:
        try:
            path_str = str(self.data_path)
            # Convert backslashes to forward slashes for URL detection
            path_str_url = path_str.replace("\\", "/")
            if path_str_url.startswith("http://") or path_str_url.startswith(
                "https://"
            ):
                response = requests.get(path_str_url, timeout=10)
                response.raise_for_status()
                raw = response.json()
            else:
                with open(self.data_path, encoding="utf-8") as f:
                    raw = json.load(f)
        except Exception as e:  # pragma: no cover - unexpected environment issues
            msg = f"Failed to load data.json: {e}"
            raise ItemDataError(msg, data_path=str(self.data_path)) from e
        return self._validate_json_dict(raw)

    @staticmethod
    def _validate_json_dict(data: object) -> dict[str, Any]:
        if not isinstance(data, dict):
            msg = "data.json must be a JSON object at the top level."
            raise ItemDataError(msg)
        return data

    def _extract_and_filter_items(self) -> dict[str, ItemMeta]:
        item_dict = self._extract_items(self.raw_data)
        return {
            str(iid): self._to_meta(raw)
            for iid, raw in item_dict.items()
            if isinstance(iid, str) and iid
        }

    @staticmethod
    def _extract_items(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
        items = data.get("items")
        if items is None:
            return {}
        if not isinstance(items, list):
            msg = "If present, 'items' must be a list."
            raise ItemDataError(msg, key="items")
        return {
            str(item.get("id")): item
            for item in items
            if isinstance(item, dict) and item.get("id")
        }

    @staticmethod
    def _coerce_str(val: object) -> str | None:
        if val is None:
            return None
        if isinstance(val, (str, int, float)):
            return str(val)
        if isinstance(val, list):
            return ", ".join(str(v) for v in val)
        return None

    def _to_meta(self, item: dict[str, Any]) -> ItemMeta:
        return ItemMeta(
            id=str(item.get("id")),
            name=self._coerce_str(item.get("name")),
            type=self._coerce_str(item.get("type")),
            quality=self._coerce_str(item.get("quality")),
        )

    # Convenience accessors ------------------------------------------------
    def get_item(self, item_id: str) -> ItemMeta | None:
        """
        Returns the ItemMeta for the given item_id, or None if not found.

        Args:
            item_id: The item id to look up.

        Returns:
            ItemMeta if found, else None.
        """
        return self._items.get(item_id)

    def get_all_items(self) -> dict[str, ItemMeta]:
        """
        Returns a copy of the internal item dictionary.

        Returns:
            Dictionary mapping item ids to ItemMeta objects.
        """
        return dict(self._items)

    def ids(self) -> Iterable[str]:
        """
        Returns an iterable of all item ids.

        Returns:
            Iterable of item ids as strings.
        """
        return self._items.keys()
