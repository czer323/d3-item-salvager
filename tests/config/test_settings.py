"""Unit tests for config loading and validation."""

import pytest
from pydantic import ValidationError

from d3_item_salvager.config.base import (
    DatabaseConfig,
    LoggingConfig,
    MaxrollParserConfig,
)
from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.container import Container


@pytest.fixture
def test_config_fixture() -> AppConfig:
    """Provide a valid AppConfig for tests with a test bearer token."""
    return AppConfig(
        database=DatabaseConfig(),
        maxroll_parser=MaxrollParserConfig(bearer_token="test-token"),
        logging=LoggingConfig(),
    )


@pytest.fixture
def test_container_fixture(request: pytest.FixtureRequest) -> Container:
    """Create DI container and override config provider for tests."""
    config = request.getfixturevalue("test_config_fixture")
    container = Container()
    container.config.override(config)
    return container


def test_config_env_override(request: pytest.FixtureRequest) -> None:
    """Config values are overridden by explicit test values via DI."""
    container = request.getfixturevalue("test_container_fixture")

    config = AppConfig(
        database=DatabaseConfig(url="sqlite:///test.db"),
        maxroll_parser=MaxrollParserConfig(bearer_token="dummy-token"),
        logging=LoggingConfig(),
    )
    container.config.override(config)
    actual_config = container.config()
    assert actual_config.database.url == "sqlite:///test.db"
    assert actual_config.maxroll_parser.bearer_token == "dummy-token"


def test_config_loads_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Config loads defaults when environment variables and .env are absent."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("MAXROLL_BEARER_TOKEN", raising=False)
    config = AppConfig(
        database=DatabaseConfig(),
        maxroll_parser=MaxrollParserConfig(bearer_token="prodtoken"),
        logging=LoggingConfig(),
    )
    container = Container()
    container.config.override(config)
    actual_config = container.config()
    assert actual_config.database.url == "sqlite:///d3_items.db"
    assert actual_config.maxroll_parser.bearer_token == "prodtoken"


def test_config_validation_failure() -> None:
    """Config validation fails if a required field is missing."""
    with pytest.raises(ValidationError, match="Field required"):
        AppConfig(  # pyright: ignore[reportCallIssue]
            database=DatabaseConfig(),
            logging=LoggingConfig(),
            # maxroll_parser omitted, should fail
        )
