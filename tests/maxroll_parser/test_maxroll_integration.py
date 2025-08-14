"""
Integration test for the Maxroll pipeline:
guide fetching, build profile parsing, and item data extraction.
"""

from pathlib import Path

import pytest

from d3_item_salvager.config.base import MaxrollParserConfig
from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.container import Container
from d3_item_salvager.maxroll_parser.maxroll_client import MaxrollClient


def test_maxroll_pipeline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Integration test for Maxroll pipeline using config override."""
    monkeypatch.setenv("MAXROLL_BEARER_TOKEN", "dummy-token")
    container = Container()
    # Construct AppConfig with required maxroll_parser field

    app_config = AppConfig(
        maxroll_parser=MaxrollParserConfig(bearer_token="dummy-token")
    )
    container.config.override(app_config)
    client = MaxrollClient(container.config())
    # Step 2: Parse build profiles (simulate with a dummy file)
    dummy_profile_path = tmp_path / "dummy_profiles.json"
    dummy_profile_path.write_text(
        '{"data": {}}', encoding="utf-8"
    )  # Valid empty build profile
    profiles = client.get_build_profiles(str(dummy_profile_path))
    assert isinstance(profiles, list)
    # Step 3: Get all items (should be dict, may be empty)
    items = client.get_all_items()
    assert isinstance(items, dict)
    # Step 4: Get item data (should be None for non-existent id)
    item = client.get_item_data("nonexistent_id")
    assert item is None
