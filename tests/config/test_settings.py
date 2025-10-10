"""Unit tests for config loading and validation."""

import pytest
from pydantic import ValidationError

from d3_item_salvager.config.base import (
    DatabaseConfig,
    LoggingConfig,
    MaxrollParserConfig,
)
from d3_item_salvager.config.settings import AppConfig


@pytest.fixture
def test_config_fixture() -> AppConfig:
    """Provide a valid AppConfig for tests with a test bearer token."""
    return AppConfig(
        database=DatabaseConfig(),
        maxroll_parser=MaxrollParserConfig(bearer_token="test-token"),
        logging=LoggingConfig(),
    )


def test_config_env_override(request: pytest.FixtureRequest) -> None:
    """Explicit values override defaults when constructing AppConfig."""
    _ = request  # Fixtures available for future extensions
    config = AppConfig(
        database=DatabaseConfig(url="sqlite:///test.db"),
        maxroll_parser=MaxrollParserConfig(bearer_token="dummy-token"),
        logging=LoggingConfig(),
    )
    assert config.database.url == "sqlite:///test.db"
    assert config.maxroll_parser.bearer_token == "dummy-token"


def test_config_loads_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Config loads defaults when environment variables and .env are absent."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("MAXROLL_BEARER_TOKEN", raising=False)
    config = AppConfig(
        database=DatabaseConfig(),
        maxroll_parser=MaxrollParserConfig(bearer_token="prodtoken"),
        logging=LoggingConfig(),
    )
    assert config.database.url == "sqlite:///d3_items.db"
    assert config.maxroll_parser.bearer_token == "prodtoken"


def test_config_validation_failure() -> None:
    """Config validation fails if a required field is missing."""
    with pytest.raises(ValidationError, match="Field required"):
        AppConfig(  # pyright: ignore[reportCallIssue]
            database=DatabaseConfig(),
            logging=LoggingConfig(),
            # maxroll_parser omitted, should fail
        )
