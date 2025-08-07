"""Unit tests for config loading and validation."""

import pytest

from d3_item_salvager.config.settings import AppConfig


# Fixture to set required env var for all tests except validation failure
@pytest.fixture(autouse=True)
def set_required_env(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    """Set required environment variable for tests."""
    if "no_bearer_token" not in request.keywords:
        monkeypatch.setenv("MAXROLL_BEARER_TOKEN", "prodtoken")


def test_config_loads_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Config loads defaults when environment variables are unset."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    config = AppConfig()
    assert config.database.url == "sqlite:///d3_items.db"
    assert config.maxroll_parser.bearer_token == "prodtoken"


def test_config_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Config values are overridden by environment variables."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("MAXROLL_BEARER_TOKEN", "dummy-token")

    config = AppConfig()
    assert config.database.url == "sqlite:///test.db"
    assert config.maxroll_parser.bearer_token == "dummy-token"


@pytest.mark.no_bearer_token
def test_config_validation_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Config validation fails if a required field is missing."""
    monkeypatch.delenv("MAXROLL_BEARER_TOKEN", raising=False)
    with pytest.raises(ValueError, match="Configuration validation failed"):
        AppConfig()
