"""Small collection utilities used by the frontend backend to canonicalize item lists."""

from collections.abc import Iterable
from typing import Any


def dedupe_and_sort(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate a sequence of item dicts by `id` (first-seen wins) and return
    them sorted alphabetically by `name`.

    Args:
        items: Iterable of dictionaries, each typically containing `id` and `name` keys.
               If `id` is missing, `name` is used as the deduplication key.

    Returns:
        A list of de-duplicated items sorted by their `name` value.
    """
    # Use discriminated keys to avoid collisions between different id types
    # (e.g., 1 vs "1"). We represent types by their name to keep types concrete
    # for static analysis and fall back to string representations when needed.
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, Any]] = []
    for it in items:
        item_id = it.get("id")
        if item_id is None:
            # Fallback: use name as key if id missing
            item_id = it.get("name")

        if item_id is None:
            # Both id and name missing — use a stable placeholder
            key: tuple[str, str] = ("NoneType", "")
        else:
            # Represent the type by its name and the value by its string form to
            # ensure keys are hashable and statically-typed.
            try:
                hash(item_id)
                key = (type(item_id).__name__, str(item_id))
            except TypeError:
                key = (type(item_id).__name__, str(item_id))

        if key in seen:
            continue
        seen.add(key)
        unique.append(it)

    def _name_key(entry: dict[str, Any]) -> str:
        return str(entry.get("name", ""))

    unique.sort(key=_name_key)
    return unique
