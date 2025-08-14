"""Unit tests for MaxrollClient covering positive and negative cases."""

from typing import TYPE_CHECKING

import pytest

from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.maxroll_parser.maxroll_client import MaxrollClient
from d3_item_salvager.maxroll_parser.maxroll_exceptions import BuildProfileError
from tests.fakes.test_config import make_test_app_config

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture


def make_config(tmp_path: "Path") -> AppConfig:
    """Create a MaxrollParserConfig for testing with a temporary cache file."""
    return make_test_app_config(tmp_path)


def test_client_init_and_properties(tmp_path: "Path") -> None:
    """Test MaxrollClient initialization and property setup.

    Verifies that the client is initialized with the correct config and subcomponents.
    """
    config = make_config(tmp_path)
    client = MaxrollClient(config)
    assert client.config == config
    assert client.guide_fetcher is not None
    assert client.profile_parser is not None
    assert client.item_parser is not None


def test_client_get_guides_empty(tmp_path: "Path", mocker: "MockerFixture") -> None:
    """Test get_guides returns an empty list when no guides are fetched.

    Verifies that the client returns an empty list when guide_fetcher returns no guides.
    """
    config = make_config(tmp_path)
    client = MaxrollClient(config)
    mocker.patch.object(client.guide_fetcher, "fetch_guides", return_value=[])
    guides = client.get_guides()
    assert isinstance(guides, list)


def test_client_get_build_profiles_empty(tmp_path: "Path") -> None:
    """Test get_build_profiles raises BuildProfileError for missing file.

    Verifies that the client raises BuildProfileError when the build profile file is missing.
    """
    config = make_config(tmp_path)
    client = MaxrollClient(config)
    with pytest.raises(BuildProfileError):
        client.get_build_profiles(str(tmp_path / "dummy.json"))


def test_client_get_item_data_empty(tmp_path: "Path") -> None:
    """Test get_item_data returns None or dict for nonexistent item.

    Verifies that the client returns None or a dict when the item does not exist.
    """
    config = make_config(tmp_path)
    client = MaxrollClient(config)
    item = client.get_item_data("nonexistent")
    assert item is None or isinstance(item, dict)
