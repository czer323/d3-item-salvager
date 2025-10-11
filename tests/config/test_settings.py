"""Unit tests for environment-aware config loading and validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from d3_item_salvager.config.base import AppEnvironment, DatabaseConfig, LoggingConfig
from d3_item_salvager.config.settings import AppConfig


def _reset_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("MAXROLL_PARSER__BEARER_TOKEN", raising=False)
    monkeypatch.delenv("APP_USE_DOTENV", raising=False)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("APP_USE_DOTENV", "0")


def test_config_defaults_to_local_development(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default configuration uses local Maxroll sources in development."""
    _reset_env(monkeypatch)
    config = AppConfig(database=DatabaseConfig(), logging=LoggingConfig())
    assert config.environment is AppEnvironment.DEVELOPMENT
    assert config.maxroll_parser.source == "local"


def test_config_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Explicit values override defaults when constructing AppConfig."""
    _reset_env(monkeypatch)
    config = AppConfig(
        database=DatabaseConfig(url="sqlite:///test.db"),
        logging=LoggingConfig(level="DEBUG"),
    )
    assert config.database.url == "sqlite:///test.db"
    assert config.logging.level == "DEBUG"


def test_production_requires_bearer_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Production environment raises when bearer token is missing."""
    _reset_env(monkeypatch)
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(ValidationError, match="MAXROLL_BEARER_TOKEN"):
        AppConfig(database=DatabaseConfig(), logging=LoggingConfig())


def test_production_accepts_explicit_bearer_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Providing a bearer token in production succeeds."""
    _reset_env(monkeypatch)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("MAXROLL_PARSER__BEARER_TOKEN", "test-token")
    config = AppConfig(database=DatabaseConfig(), logging=LoggingConfig())
    assert config.environment is AppEnvironment.PRODUCTION
    assert config.maxroll_parser.source == "remote"
    assert config.maxroll_parser.bearer_token == "test-token"
