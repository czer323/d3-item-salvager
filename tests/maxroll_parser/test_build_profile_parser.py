"""Unit tests for BuildProfileParser covering positive and negative cases."""

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.maxroll_parser.build_profile_parser import BuildProfileParser
from d3_item_salvager.maxroll_parser.guide_profile_resolver import GuideProfileResolver
from d3_item_salvager.maxroll_parser.maxroll_exceptions import BuildProfileError

if TYPE_CHECKING:  # pragma: no cover - typing only
    from pytest_mock import MockerFixture


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


class _FakeResolver(GuideProfileResolver):
    def __init__(self, payload: dict[str, Any]) -> None:
        # Override parent initialisation to avoid external configuration.
        self._payload = payload

    def resolve(self, guide_url: str) -> dict[str, Any]:  # pragma: no cover - trivial
        _ = guide_url
        return self._payload


def test_parser_uses_resolver_for_guide_urls() -> None:
    """Guide URLs should be resolved via the injected resolver."""
    payload = {"data": {"profiles": [{"name": "Resolved", "class": "Wizard"}]}}
    parser = BuildProfileParser(
        "https://maxroll.gg/d3/guides/test-guide",
        resolver=_FakeResolver(payload),
    )
    assert parser.profiles[0].name == "Resolved"


def test_parser_builds_resolver_when_config_supplied(mocker: "MockerFixture") -> None:
    """Parser should construct a resolver from config when one is not provided."""
    config = AppConfig()
    fake_resolver = mocker.create_autospec(GuideProfileResolver, instance=True)
    fake_resolver.resolve.return_value = {"data": {"profiles": []}}

    resolver_ctor = mocker.patch(
        "d3_item_salvager.maxroll_parser.build_profile_parser.GuideProfileResolver",
        return_value=fake_resolver,
    )

    parser = BuildProfileParser(
        "https://maxroll.gg/d3/guides/test-guide",
        config=config,
    )

    resolver_ctor.assert_called_once_with(config)
    fake_resolver.resolve.assert_called_once_with(
        "https://maxroll.gg/d3/guides/test-guide"
    )
    assert parser.profiles == []
