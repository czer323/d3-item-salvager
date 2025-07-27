"""Unit tests for config loading and validation."""

import pytest

from d3_item_salvager.config import get_config, reset_config


def test_config_loads_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that config loads default values when env vars are not set."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    reset_config()
    config = get_config()
    assert config.database.url is not None
    assert config.scraper.user_agent == "Mozilla/5.0"
    assert config.scraper.timeout == 10


def test_config_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that config values are overridden by environment variables."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("SCRAPER_USER_AGENT", "TestAgent")
    monkeypatch.setenv("SCRAPER_TIMEOUT", "5")

    reset_config()
    config = get_config()
    assert config.database.url == "sqlite:///test.db"
    assert config.scraper.user_agent == "TestAgent"
    assert config.scraper.timeout == 5


def test_config_validation_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that config validation fails if required fields are missing."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    reset_config()
    with pytest.raises(RuntimeError, match="Configuration validation failed"):
        get_config()
