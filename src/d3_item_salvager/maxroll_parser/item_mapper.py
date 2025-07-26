"""
Utility for mapping build profile item IDs to full item data using the master item_dict.
"""


def map_item_ids_to_data(
    item_ids: list[str], item_dict: dict[str, dict[str, str]]
) -> list[dict[str, str] | None]:
    """
    Given a list of item IDs from a build profile,
    return the corresponding filtered item data dicts from item_dict.

    If an item ID is not found, None is returned in its place.

    Args:
        item_ids: List of item IDs (strings) from a build profile.
        item_dict: Filtered dictionary mapping item IDs to item data (from filter_item_fields).

    Returns:
        List of item data dicts (or None if not found), in the same order as item_ids.
    """
    return [item_dict.get(item_id) for item_id in item_ids]
