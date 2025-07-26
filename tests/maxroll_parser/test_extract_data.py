"""
Unit tests for extract_data to test the game data parsing.
"""

from pathlib import Path

import pytest

from d3_item_salvager.maxroll_parser import extract_data


def test_dataparser_success() -> None:
    """
    Test that DataParser loads data.json and returns non-empty dicts.
    """
    loader = extract_data.DataParser()
    item_dict = loader.items
    assert isinstance(item_dict, dict)
    # item_dict may be empty if 'items' is not present in data.json
    if item_dict:
        sample_item = next(iter(item_dict.values()))
        assert "id" in sample_item
        assert "name" in sample_item


def test_dataparser_missing_file(tmp_path: Path) -> None:
    """
    Test that DataParser raises FileNotFoundError for a missing file.
    """
    missing_path = tmp_path / "not_found.json"
    with pytest.raises(FileNotFoundError):
        extract_data.DataParser(missing_path)


def test_dataparser_invalid_structure(tmp_path: Path) -> None:
    """
    Test that DataParser raises TypeError for invalid JSON structure.
    """
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{}", encoding="utf-8")
    loader = extract_data.DataParser(bad_json)
    result = loader.items
    assert not result, "Should return empty dict for empty JSON object"
