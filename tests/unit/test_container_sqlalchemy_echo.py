"""Tests for SQLAlchemy echo configuration via the DI container."""

from __future__ import annotations

from typing import Any, cast

from dependency_injector import providers

from d3_item_salvager.config.base import LoggingConfig
from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.container import Container


def test_engine_echo_defaults_to_false() -> None:
    """By default SQLAlchemy echo should be disabled to reduce console noise."""
    app_config = AppConfig(logging=LoggingConfig())

    container = Container()
    config_provider = cast("Any", container.config)
    config_provider.override(providers.Object(app_config))

    engine = container.engine()
    assert getattr(engine, "echo", False) is False


def test_engine_echo_can_be_enabled() -> None:
    """Enabling the config should set engine echo to True."""
    app_config = AppConfig(logging=LoggingConfig(sqlalchemy_echo=True))

    container = Container()
    config_provider = cast("Any", container.config)
    config_provider.override(providers.Object(app_config))

    engine = container.engine()
    assert engine.echo is True
