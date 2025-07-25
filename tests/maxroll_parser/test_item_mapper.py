"""
Unit tests for item_mapper.py (mapping build profile item IDs to item data).
"""

from d3_item_salvager.maxroll_parser import data_loader, item_mapper


def test_map_item_ids_to_data_basic() -> None:
    """
    Test mapping a list of item IDs to their corresponding item data.
    """
    item_dict, _ = data_loader.load_master_data()
    # Use a few known item IDs from the master data (if available)
    # For robustness, just grab the first 2 IDs from the dict
    item_ids = list(item_dict.keys())[:2]
    mapped = item_mapper.map_item_ids_to_data(item_ids, item_dict)
    assert len(mapped) == len(item_ids)
    for i, item in enumerate(mapped):
        assert item is not None, f"Item ID {item_ids[i]} should be found in item_dict"
        assert "id" in item
        assert "name" in item


def test_map_item_ids_to_data_missing() -> None:
    """
    Test that missing item IDs return None in the result.
    """
    item_dict, _ = data_loader.load_master_data()
    item_ids = ["not_a_real_id", "another_fake_id"]
    mapped = item_mapper.map_item_ids_to_data(item_ids, item_dict)
    assert mapped == [None, None]
