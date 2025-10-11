"""Tests covering CLI entrypoint configuration behaviour."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from d3_item_salvager.__main__ import app_cli, run_cli, run_workers
from d3_item_salvager.config.base import AppEnvironment, LoggingConfig
from d3_item_salvager.container import Container

if TYPE_CHECKING:  # pragma: no cover - typing only
    from pytest_mock import MockerFixture
else:

    class MockerFixture:  # pragma: no cover - runtime placeholder
        pass


def _reset_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("MAXROLL_PARSER__BEARER_TOKEN", raising=False)
    monkeypatch.delenv("APP_USE_DOTENV", raising=False)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("APP_USE_DOTENV", "0")


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


def test_import_guides_command_invokes_service(
    monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
) -> None:
    """CLI import command wires container, loads env, and calls the service."""
    _reset_env(monkeypatch)

    summary = SimpleNamespace(
        guides_processed=5,
        guides_skipped=0,
        builds_created=5,
        profiles_created=10,
        items_created=15,
        usages_created=20,
    )
    mock_service = mocker.Mock()
    mock_service.prepare_database.return_value = summary

    class _StubConfig:
        def __init__(self, production: bool) -> None:
            self._production = production
            logging_config = LoggingConfig()
            logging_config.enabled = False
            self.logging = logging_config

        @property
        def is_production(self) -> bool:
            return self._production

    class _StubContainer:
        def __init__(self, config: _StubConfig) -> None:
            self._config = config

        def wire(self, modules: list[str]) -> None:  # pragma: no cover - noop
            _ = modules

        def config(self) -> _StubConfig:
            return self._config

        def build_guide_service(self) -> object:
            return mock_service

    stub_container = _StubContainer(_StubConfig(production=False))
    monkeypatch.setattr(
        "d3_item_salvager.__main__._build_container", lambda: stub_container
    )

    runner = CliRunner()
    result = runner.invoke(app_cli, ["import-guides"])

    assert result.exit_code == 0
    mock_service.prepare_database.assert_called_once_with(force_refresh=False)


def test_import_guides_command_forces_refresh_in_production(
    monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
) -> None:
    """Production mode forces a cache refresh even without explicit flag."""
    _reset_env(monkeypatch)

    mock_service = mocker.Mock()
    mock_service.prepare_database.return_value = SimpleNamespace(
        guides_processed=0,
        guides_skipped=0,
        builds_created=0,
        profiles_created=0,
        items_created=0,
        usages_created=0,
    )

    class _StubConfig:
        def __init__(self) -> None:
            logging_config = LoggingConfig()
            logging_config.enabled = False
            self.logging = logging_config

        @property
        def is_production(self) -> bool:
            return True

    class _StubContainer:
        def wire(self, modules: list[str]) -> None:  # pragma: no cover - noop
            _ = modules

        def config(self) -> _StubConfig:
            return _StubConfig()

        def build_guide_service(self) -> object:
            return mock_service

    monkeypatch.setattr(
        "d3_item_salvager.__main__._build_container", lambda: _StubContainer()
    )

    runner = CliRunner()
    result = runner.invoke(app_cli, ["import-guides"])

    assert result.exit_code == 0
    mock_service.prepare_database.assert_called_once_with(force_refresh=True)
