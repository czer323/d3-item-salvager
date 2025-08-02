# pylint: disable=W0621  # Redefining name from outer scope (pytest fixtures)
"""Tests for Maxroll guide cache utilities."""

import json
from pathlib import Path

import pytest

from d3_item_salvager.config.base import (
    DatabaseConfig,
    LoggingConfig,
    MaxrollParserConfig,
)
from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.maxroll_parser.get_guide_cache_utils import (
    load_guides_from_cache,
    save_guides_to_cache,
)
from d3_item_salvager.maxroll_parser.types import GuideInfo


@pytest.fixture
def test_cache_path(tmp_path: Path) -> Path:
    """Fixture to provide a temporary cache path for testing in a temp subdir."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / "test_guides_cache.json"


@pytest.fixture
def test_sample_guides() -> list[GuideInfo]:
    """Sample guides for testing."""
    return [
        GuideInfo(name="Test Guide 1", url="https://maxroll.gg/d3/guides/test-guide-1"),
        GuideInfo(name="Test Guide 2", url="https://maxroll.gg/d3/guides/test-guide-2"),
    ]


def make_test_config(cache_path: Path, cache_ttl: int = 9999) -> AppConfig:
    """Create a temporary AppConfig for testing."""
    return AppConfig(
        database=DatabaseConfig(),
        maxroll_parser=MaxrollParserConfig(
            bearer_token="test-token",
            cache_file=cache_path,
            cache_ttl=cache_ttl,
        ),
        logging=LoggingConfig(),
    )


def test_save_and_load_guides_cache(
    test_cache_path: Path,
    test_sample_guides: list[GuideInfo],
) -> None:
    """Test saving and loading guides from cache."""
    config = make_test_config(test_cache_path, cache_ttl=9999)
    save_guides_to_cache(test_sample_guides, config)
    loaded = load_guides_from_cache(config)
    assert loaded is not None
    assert len(loaded) == 2
    assert loaded[0].name == "Test Guide 1"
    assert loaded[1].url == "https://maxroll.gg/d3/guides/test-guide-2"


def test_cache_expiry(
    test_cache_path: Path,
    test_sample_guides: list[GuideInfo],
) -> None:
    """Test that cache expires after TTL."""
    config = make_test_config(test_cache_path, cache_ttl=-1)
    save_guides_to_cache(test_sample_guides, config)
    loaded = load_guides_from_cache(config)
    assert loaded is None


def test_load_guides_cache_missing_file() -> None:
    """Test loading from a non-existent cache file."""
    missing_path = Path("not_a_real_cache_file.json")
    config = make_test_config(missing_path, cache_ttl=9999)
    assert load_guides_from_cache(config) is None


def test_load_guides_cache_invalid_json(
    test_cache_path: Path,
) -> None:
    """Test loading from a cache file with invalid JSON."""
    test_cache_path.write_text("not valid json", encoding="utf-8")
    config = make_test_config(test_cache_path, cache_ttl=9999)
    assert load_guides_from_cache(config) is None


def test_load_guides_cache_missing_keys(
    test_cache_path: Path,
) -> None:
    """Test loading from a cache file with missing keys."""
    bad_data = {"guides": [{"foo": "bar"}, {"name": "OnlyName"}]}
    test_cache_path.write_text(json.dumps(bad_data), encoding="utf-8")
    config = make_test_config(test_cache_path, cache_ttl=9999)
    loaded = load_guides_from_cache(config)
    assert loaded == []
