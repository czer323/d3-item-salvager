"""Small collection utilities used by the frontend backend to canonicalize item lists."""

from collections.abc import Iterable
from typing import Any


def dedupe_and_sort(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate a sequence of item dicts by `id` (first-seen wins) and return
    them sorted alphabetically by `name`.

    Args:
        items: Iterable of dictionaries with at least `id` and `name` keys.

    Returns:
        A list of de-duplicated items sorted by their `name` value.
    """
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for it in items:
        item_id = it.get("id")
        if item_id is None:
            # Fallback: use name as key if id missing
            item_id = it.get("name")
        # Normalize to string to ensure stable membership checks
        key = str(item_id)
        if key in seen:
            continue
        seen.add(key)
        unique.append(it)

    def _name_key(entry: dict[str, Any]) -> str:
        return str(entry.get("name", ""))

    unique.sort(key=_name_key)
    return unique
