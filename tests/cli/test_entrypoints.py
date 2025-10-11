"""Tests covering CLI entrypoint configuration behaviour."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from d3_item_salvager.__main__ import app_cli, run_cli, run_workers
from d3_item_salvager.config.base import AppEnvironment
from d3_item_salvager.container import Container


def _reset_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("MAXROLL_PARSER__BEARER_TOKEN", raising=False)


def test_container_uses_local_defaults_in_development(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Container provides a working config in development without remote credentials."""
    _reset_env(monkeypatch)
    container = Container()
    config = container.config()
    assert config.environment is AppEnvironment.DEVELOPMENT
    assert config.maxroll_parser.source == "local"


def test_container_requires_token_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production mode without a bearer token triggers validation failure."""
    _reset_env(monkeypatch)
    monkeypatch.setenv("APP_ENV", "production")
    container = Container()
    with pytest.raises(ValidationError, match="MAXROLL_BEARER_TOKEN"):
        container.config()


def test_run_cli_raises_in_production_without_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI execution fails fast when production credentials are missing."""
    _reset_env(monkeypatch)
    monkeypatch.setenv("APP_ENV", "production")
    container = Container()
    container.wire(modules=["d3_item_salvager.__main__"])
    with pytest.raises(ValidationError, match="MAXROLL_BEARER_TOKEN"):
        run_cli()


def test_run_workers_raises_in_production_without_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Workers execution fails fast when production credentials are missing."""
    _reset_env(monkeypatch)
    monkeypatch.setenv("APP_ENV", "production")
    container = Container()
    container.wire(modules=["d3_item_salvager.__main__"])
    with pytest.raises(ValidationError, match="MAXROLL_BEARER_TOKEN"):
        run_workers()


def test_typer_cli_api_subcommand_fails_without_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Typer CLI surfaces configuration errors when production credentials are absent."""
    _reset_env(monkeypatch)
    monkeypatch.setenv("APP_ENV", "production")
    runner = CliRunner()
    result = runner.invoke(app_cli, ["api"])
    assert result.exit_code != 0
    assert isinstance(result.exception, ValidationError)
    assert "MAXROLL_BEARER_TOKEN" in str(result.exception)
