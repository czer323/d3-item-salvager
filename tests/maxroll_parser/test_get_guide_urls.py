"""
Unit tests for get_guide_urls module (fetch_all_guides_meilisearch).
"""

from pytest_mock import MockerFixture

from d3_item_salvager.maxroll_parser.get_guide_urls import (
    fetch_all_guides_meilisearch,
)


def sample_meilisearch_response() -> dict:
    return {
        "hits": [
            {"permalink": "https://maxroll.gg/d3/guides/sample-build-1"},
            {"permalink": "https://maxroll.gg/d3/guides/sample-build-2"},
            {"permalink": "https://maxroll.gg/d3/news/irrelevant-news"},
        ]
    }


def test_fetch_all_guides_meilisearch_filters_and_extracts(
    mocker: MockerFixture,
) -> None:
    """Test that fetch_all_guides_meilisearch filters and extracts only build guides."""
    mock_post = mocker.patch("requests.post")
    # Simulate two pages: first with 3 hits, second empty
    mock_post.side_effect = [
        type(
            "Resp",
            (),
            {
                "json": lambda self=None: sample_meilisearch_response(),
                "raise_for_status": lambda self=None: None,
            },
        )(),
        type(
            "Resp",
            (),
            {
                "json": lambda self=None: {"hits": []},
                "raise_for_status": lambda self=None: None,
            },
        )(),
    ]
    guides = fetch_all_guides_meilisearch(limit=10)
    # Only the two build guides should be present
    assert len(guides) == 2
    assert guides[0]["url"] == "https://maxroll.gg/d3/guides/sample-build-1"
    assert guides[1]["url"] == "https://maxroll.gg/d3/guides/sample-build-2"
    assert all("name" in g and "url" in g for g in guides)
    # Names should be formatted from slug
    assert guides[0]["name"] == "Sample Build 1"
    assert guides[1]["name"] == "Sample Build 2"
