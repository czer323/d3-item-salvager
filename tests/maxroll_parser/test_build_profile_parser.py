"""Unit tests for BuildProfileParser covering positive and negative cases."""

import json
from pathlib import Path

import pytest

from d3_item_salvager.maxroll_parser.build_profile_parser import BuildProfileParser
from d3_item_salvager.maxroll_parser.maxroll_exceptions import BuildProfileError


def make_profile_json(tmp_path: Path, profiles: list[dict[str, object]]) -> Path:
    """Helper to create a profile.json file for tests."""
    path = tmp_path / "profile.json"
    data = {"data": {"profiles": profiles}}
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


def test_extract_profiles_positive(tmp_path: Path) -> None:
    """Test extracting valid profiles from a well-formed file."""
    profiles: list[dict[str, object]] = [
        {
            "name": "Test",
            "class": "Barbarian",
            "seasonal": True,
            "gender": "male",
            "paragonLevel": 100,
        },
        {
            "name": "Test2",
            "class": "Wizard",
            "seasonal": False,
            "gender": "female",
            "paragonLevel": 200,
        },
    ]
    path = make_profile_json(tmp_path, profiles)
    parser = BuildProfileParser(path)
    assert len(parser.profiles) == 2
    assert parser.profiles[0].name == "Test"
    assert parser.profiles[1].class_name == "Wizard"


def test_extract_profiles_missing_data_key(tmp_path: Path) -> None:
    """Test error raised when 'data' key is missing in profile file."""
    path = tmp_path / "bad_profile.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump({}, f)
    with pytest.raises(BuildProfileError, match="missing top-level 'data' key"):
        BuildProfileParser(path)


def test_extract_profiles_invalid_profiles_type(tmp_path: Path) -> None:
    """Test error raised when 'profiles' is not a list."""
    data = {"data": {"profiles": "notalist"}}
    path = tmp_path / "bad_type.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f)
    with pytest.raises(BuildProfileError, match="'profiles' must be a list"):
        BuildProfileParser(path)


def test_extract_usages_positive(tmp_path: Path) -> None:
    """Test extracting item usages from valid profiles."""
    profiles: list[dict[str, object]] = [
        {
            "name": "Test",
            "items": {"mainhand": {"id": "item1"}},
            "kanai": {"weapon": "item2"},
            "followerItems": {"head": "item3"},
        },
    ]
    path = make_profile_json(tmp_path, profiles)
    parser = BuildProfileParser(path)
    usages = parser.extract_usages()
    ids = {u.item_id for u in usages}
    assert "item1" in ids
    assert "item2" in ids
    assert "item3" in ids


def test_extract_usages_empty_profiles(tmp_path: Path) -> None:
    """Test extracting usages from empty profiles returns empty list."""
    profiles: list[dict[str, object]] = []
    path = make_profile_json(tmp_path, profiles)
    parser = BuildProfileParser(path)
    usages = parser.extract_usages()
    assert not usages
