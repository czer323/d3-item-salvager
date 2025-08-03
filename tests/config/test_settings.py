"""Unit tests for config loading and validation."""

import pytest

from d3_item_salvager.config import get_config, reset_config


# Reset config before each test to ensure fresh singleton
@pytest.fixture(autouse=True)
def reset_config_fixture() -> None:
    """Reset the config singleton before each test."""
    reset_config()


# Fixture to set required env var for all tests except validation failure
@pytest.fixture(autouse=True)
def set_required_env(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    """Set required environment variable for tests."""
    if request.node.name != "test_config_validation_failure":
        monkeypatch.setenv("MAXROLL_BEARER_TOKEN", "prodtoken")


def test_config_loads_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Config loads defaults when environment variables are unset."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("MAXROLL_BEARER_TOKEN", "prodtoken")

    reset_config()
    config = get_config()
    assert config.database.url == "sqlite:///d3_items.db"
    assert config.maxroll_parser.bearer_token == "prodtoken"


def test_config_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Config values are overridden by environment variables."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("MAXROLL_BEARER_TOKEN", "dummy-token")

    reset_config()
    config = get_config()
    assert config.database.url == "sqlite:///test.db"
    assert config.maxroll_parser.bearer_token == "dummy-token"


def test_config_validation_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Config validation fails if a required field is missing."""
    reset_config()
    monkeypatch.delenv("MAXROLL_BEARER_TOKEN", raising=False)
    # Should not raise ValidationError, but should raise RuntimeError from get_config
    with pytest.raises(RuntimeError, match="Configuration validation failed"):
        get_config()
