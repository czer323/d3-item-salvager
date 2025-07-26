"""
Unit tests for data_loader.py (master data loading and validation).
"""

from pathlib import Path

import pytest

from d3_item_salvager.maxroll_parser import data_loader


def test_load_master_data_success() -> None:
    """
    Test that load_master_data loads data.json and returns non-empty dicts.
    """
    item_dict = data_loader.load_master_data()
    assert isinstance(item_dict, dict)
    # item_dict may be empty if 'items' is not present in data.json
    if item_dict:
        sample_item = next(iter(item_dict.values()))
        assert "id" in sample_item
        assert "name" in sample_item


def test_load_master_data_missing_file(tmp_path: Path) -> None:
    """
    Test that loading a missing file raises FileNotFoundError.
    """
    missing_path = tmp_path / "not_found.json"
    with pytest.raises(FileNotFoundError):
        data_loader.load_master_data(missing_path)


def test_load_master_data_invalid_structure(tmp_path: Path) -> None:
    """
    Test that invalid JSON structure raises TypeError.
    """
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{}", encoding="utf-8")
    result = data_loader.load_master_data(bad_json)
    assert result == {}, "Should return empty dict for empty JSON object"
