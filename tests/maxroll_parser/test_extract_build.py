"""
Unit tests for build_loader.py (loading and parsing build profile JSON).
"""

from pathlib import Path

import pytest

from d3_item_salvager.maxroll_parser import extract_build
from d3_item_salvager.maxroll_parser.types import BuildProfileItems


def test_load_build_profile_success() -> None:
    """
    Test loading a valid build profile JSON and extracting the 'data' key.
    """
    ref_path = (
        Path(__file__).parent.parent.parent
        / "reference"
        / "profile_object_298017784.json"
    )
    parser = extract_build.BuildProfileParser(ref_path)
    data = parser.build_data
    assert isinstance(data, (dict, list))
    # Check for at least one profile or expected keys
    if isinstance(data, dict):
        assert data, "'data' dict should not be empty"
    elif isinstance(data, list):
        assert len(data) > 0


def test_load_build_profile_missing_file(tmp_path: Path) -> None:
    """
    Test that loading a missing file raises ValueError.
    """
    missing_path = tmp_path / "not_found.json"
    with pytest.raises(ValueError, match="Could not parse build profile JSON"):
        extract_build.BuildProfileParser(missing_path)


def test_load_build_profile_invalid_json(tmp_path: Path) -> None:
    """
    Test that invalid JSON raises ValueError.
    """
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("not really json", encoding="utf-8")
    with pytest.raises(ValueError, match="Could not parse build profile JSON"):
        extract_build.BuildProfileParser(bad_json)


def test_extract_profiles_and_items_usage_output() -> None:
    """
    Test that extract_profiles_and_items returns correct minimal item usage records.
    """
    ref_path = (
        Path(__file__).parent.parent.parent
        / "reference"
        / "profile_object_298017784.json"
    )
    parser = extract_build.BuildProfileParser(ref_path)
    usages = parser.extract_usages()
    assert isinstance(usages, list)
    assert usages, "Should return at least one item usage record"
    for usage in usages:
        assert isinstance(usage, BuildProfileItems)
        for field in ("profile_name", "item_id", "slot", "usage_context"):
            assert hasattr(usage, field)
