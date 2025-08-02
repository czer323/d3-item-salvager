# ruff: noqa: SLF001
# pylint: disable=protected-access

"""
Unit tests for get_guide_urls module (fetch_all_guides_meilisearch).
"""

import json
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from d3_item_salvager.config.base import (
    DatabaseConfig,
    LoggingConfig,
    MaxrollParserConfig,
)
from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.maxroll_parser.get_guide_urls import MaxrollGuideFetcher


@pytest.fixture(name="guide_fetcher_config")
def guide_fetcher_config_fixture(tmp_path: Path) -> AppConfig:
    """Fixture to provide an AppConfig with a temp cache path for MaxrollGuideFetcher."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(exist_ok=True)
    cache_path = cache_dir / "maxroll_guides.json"
    return AppConfig(
        database=DatabaseConfig(),
        logging=LoggingConfig(),
        maxroll_parser=MaxrollParserConfig(
            api_url="https://dummy-url",
            bearer_token="dummy-token",
            cache_file=cache_path,
        ),
    )


def sample_meilisearch_response() -> dict:
    """Simulate a sample response from Meilisearch for testing."""
    return {
        "hits": [
            {"permalink": "https://maxroll.gg/d3/guides/sample-build-1"},
            {"permalink": "https://maxroll.gg/d3/guides/sample-build-2"},
            {"permalink": "https://maxroll.gg/d3/news/irrelevant-news"},
        ]
    }


def test_fetch_all_guides_meilisearch_filters_and_extracts(
    mocker: MockerFixture, guide_fetcher_config: AppConfig
) -> None:
    """Test filtering and extracting build guides from Meilisearch response."""
    mock_post = mocker.patch("requests.post")
    # Simulate two pages: first with 3 hits, second empty
    mock_post.side_effect = [
        type(
            "Resp",
            (),
            {
                "json": lambda _: sample_meilisearch_response(),
                "raise_for_status": lambda _: None,
            },
        )(),
        type(
            "Resp",
            (),
            {
                "json": lambda _: {"hits": []},
                "raise_for_status": lambda _: None,
            },
        )(),
    ]
    fetcher = MaxrollGuideFetcher(guide_fetcher_config)
    guides = fetcher.fetch_guides()
    assert len(guides) == 2
    assert guides[0].url == "https://maxroll.gg/d3/guides/sample-build-1"
    assert guides[1].url == "https://maxroll.gg/d3/guides/sample-build-2"
    assert all(hasattr(g, "name") and hasattr(g, "url") for g in guides)
    assert guides[0].name == "Sample Build 1"
    assert guides[1].name == "Sample Build 2"


def test__extract_guide_links_from_hits_basic(
    guide_fetcher_config: AppConfig,
) -> None:
    """Test extracting guide links from basic hits list."""
    hits = [
        {"permalink": "https://maxroll.gg/d3/guides/test-build-1"},
        {"permalink": "https://maxroll.gg/d3/guides/test-build-2"},
        {"permalink": "https://maxroll.gg/d3/news/ignore-this"},
    ]
    fetcher = MaxrollGuideFetcher(guide_fetcher_config)
    guides = fetcher._extract_guide_links_from_hits(hits)
    assert len(guides) == 2
    assert guides[0].url == "https://maxroll.gg/d3/guides/test-build-1"
    assert guides[1].url == "https://maxroll.gg/d3/guides/test-build-2"
    assert guides[0].name == "Test Build 1"
    assert guides[1].name == "Test Build 2"


def test__extract_guide_links_from_hits_empty(
    guide_fetcher_config: AppConfig,
) -> None:
    """Test extracting guide links from empty hits list."""
    fetcher = MaxrollGuideFetcher(guide_fetcher_config)
    guides = fetcher._extract_guide_links_from_hits([])
    assert not guides


def test__extract_guide_links_from_hits_missing_permalink(
    guide_fetcher_config: AppConfig,
) -> None:
    """Test extracting guide links when some hits are missing permalink."""
    hits = [{}, {"permalink": "https://maxroll.gg/d3/guides/valid-build"}]
    fetcher = MaxrollGuideFetcher(guide_fetcher_config)
    guides = fetcher._extract_guide_links_from_hits(hits)
    assert len(guides) == 1
    assert guides[0].url == "https://maxroll.gg/d3/guides/valid-build"


def test_fetch_guides_local_file(
    tmp_path: Path, guide_fetcher_config: AppConfig
) -> None:
    """Test fetching guides from a local file with valid hits."""
    local_json = {
        "hits": [
            {"permalink": "https://maxroll.gg/d3/guides/local-build-1"},
            {"permalink": "https://maxroll.gg/d3/guides/local-build-2"},
            {"permalink": "https://maxroll.gg/d3/news/ignore-this"},
        ]
    }
    local_path = tmp_path / "local_guides.json"
    with local_path.open("w", encoding="utf-8") as f:
        json.dump(local_json, f)
    config = AppConfig(
        database=DatabaseConfig(),
        logging=LoggingConfig(),
        maxroll_parser=MaxrollParserConfig(
            api_url=str(local_path),
            bearer_token=guide_fetcher_config.maxroll_parser.bearer_token,
            cache_file=guide_fetcher_config.maxroll_parser.cache_file,
            cache_ttl=0,
        ),
    )
    fetcher = MaxrollGuideFetcher(config)
    guides = fetcher.fetch_guides()
    assert len(guides) == 2
    assert guides[0].url == "https://maxroll.gg/d3/guides/local-build-1"
    assert guides[1].url == "https://maxroll.gg/d3/guides/local-build-2"
    assert guides[0].name == "Local Build 1"
    assert guides[1].name == "Local Build 2"


def test_fetch_guides_local_file_no_hits(
    tmp_path: Path, guide_fetcher_config: AppConfig
) -> None:
    """Test fetching guides from a local file with no hits."""
    local_json: dict[str, list] = {"hits": []}
    local_path = tmp_path / "empty_guides.json"
    with local_path.open("w", encoding="utf-8") as f:
        json.dump(local_json, f)
    config = AppConfig(
        database=DatabaseConfig(),
        logging=LoggingConfig(),
        maxroll_parser=MaxrollParserConfig(
            api_url=str(local_path),
            bearer_token=guide_fetcher_config.maxroll_parser.bearer_token,
            cache_file=guide_fetcher_config.maxroll_parser.cache_file,
            cache_ttl=0,
        ),
    )
    fetcher = MaxrollGuideFetcher(config)
    guides = fetcher.fetch_guides()
    assert guides == []


def test_fetch_guides_local_file_missing_hits(
    tmp_path: Path, guide_fetcher_config: AppConfig
) -> None:
    """Test fetching guides from a local file missing 'hits' key."""
    local_json: dict[str, list] = {"not_hits": []}
    local_path = tmp_path / "missing_hits.json"
    with local_path.open("w", encoding="utf-8") as f:
        json.dump(local_json, f)
    config = AppConfig(
        database=DatabaseConfig(),
        logging=LoggingConfig(),
        maxroll_parser=MaxrollParserConfig(
            api_url=str(local_path),
            bearer_token=guide_fetcher_config.maxroll_parser.bearer_token,
            cache_file=guide_fetcher_config.maxroll_parser.cache_file,
            cache_ttl=0,
        ),
    )
    fetcher = MaxrollGuideFetcher(config)
    guides = fetcher.fetch_guides()
    assert guides == []


def test_fetch_guides_api_mocked(
    mocker: MockerFixture, guide_fetcher_config: AppConfig
) -> None:
    """Test fetching guides from a mocked API response."""
    mock_post = mocker.patch("requests.post")
    mock_post.return_value.json.return_value = {
        "hits": [
            {"permalink": "https://maxroll.gg/d3/guides/api-build-1"},
            {"permalink": "https://maxroll.gg/d3/guides/api-build-2"},
        ]
    }
    mock_post.return_value.raise_for_status.return_value = None
    config = AppConfig(
        database=DatabaseConfig(),
        logging=LoggingConfig(),
        maxroll_parser=MaxrollParserConfig(
            api_url="https://fake-api-url",
            bearer_token=guide_fetcher_config.maxroll_parser.bearer_token,
            cache_file=guide_fetcher_config.maxroll_parser.cache_file,
            cache_ttl=0,
        ),
    )
    fetcher = MaxrollGuideFetcher(config)
    guides = fetcher.fetch_guides()
    assert len(guides) == 2
    assert guides[0].url == "https://maxroll.gg/d3/guides/api-build-1"
    assert guides[1].url == "https://maxroll.gg/d3/guides/api-build-2"
    assert guides[0].name == "Api Build 1"
    assert guides[1].name == "Api Build 2"
