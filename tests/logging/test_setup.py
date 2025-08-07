# pylint: disable=redefined-outer-name
# pylint: disable=too-few-public-methods
"""
Unit tests for logger setup and decorators using pytest and pytest-mock.

This module tests the setup_logger function and the log_timing/log_contextual decorators.
All tests use type annotations and pytest-mock's mocker fixture for patching and isolation.
"""

import builtins
import sys
import types
from pathlib import Path
from typing import Any

import pytest
from loguru import logger
from pytest import CaptureFixture
from pytest_mock import MockerFixture

from d3_item_salvager.config.base import LoggingConfig
from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.logging.setup import log_contextual, log_timing, setup_logger


@pytest.fixture
def dummy_config_basic(monkeypatch: pytest.MonkeyPatch) -> AppConfig:
    """Returns a dummy config object for basic logger setup (no file, no metrics)."""
    monkeypatch.setenv("MAXROLL_BEARER_TOKEN", "dummy-token")
    app_config = AppConfig()
    app_config.logging = LoggingConfig(enabled=False, metrics_enabled=False)
    return app_config


@pytest.fixture
def dummy_config_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> AppConfig:
    """Returns a dummy config object with file handler enabled."""
    monkeypatch.setenv("MAXROLL_BEARER_TOKEN", "dummy-token")
    log_file = tmp_path / "dummy.log"
    app_config = AppConfig()
    app_config.logging = LoggingConfig(
        enabled=True, metrics_enabled=False, level="DEBUG", log_file=str(log_file)
    )
    return app_config


@pytest.fixture
def dummy_config_metrics_enabled(monkeypatch: pytest.MonkeyPatch) -> AppConfig:
    """Returns a dummy config object with metrics enabled."""
    monkeypatch.setenv("MAXROLL_BEARER_TOKEN", "dummy-token")
    app_config = AppConfig()
    app_config.logging = LoggingConfig(
        enabled=False, metrics_enabled=True, level="INFO"
    )
    return app_config


@pytest.fixture
def dummy_config_metrics_importerror(monkeypatch: pytest.MonkeyPatch) -> AppConfig:
    """Returns a dummy config object with metrics enabled and simulates ImportError."""
    monkeypatch.setenv("MAXROLL_BEARER_TOKEN", "dummy-token")
    app_config = AppConfig()
    app_config.logging = LoggingConfig(
        enabled=False, metrics_enabled=True, level="INFO"
    )
    return app_config


def test_setup_logger_runs(dummy_config_basic: AppConfig) -> None:
    """
    Test that setup_logger runs without error and logger can log a message.
    """
    setup_logger(dummy_config_basic)
    logger.info("Logger setup test message.")


@log_timing
def dummy_timed_func() -> str:
    """
    Dummy function to test log_timing decorator.
    """
    return "timed"


def test_log_timing_decorator() -> None:
    """
    Test that log_timing decorator logs timing info and returns correct value.
    """
    result = dummy_timed_func()
    assert result == "timed"


@log_contextual({"test_key": "test_value"})
def dummy_contextual_func() -> str:
    """
    Dummy function to test log_contextual decorator.
    """
    return "contextual"


def test_log_contextual_decorator() -> None:
    """
    Test that log_contextual decorator logs context info and returns correct value.
    """
    result = dummy_contextual_func()
    assert result == "contextual"


def test_setup_logger_basic(dummy_config_basic: AppConfig) -> None:
    """Test setup_logger initializes logger with basic config (no file, no metrics)."""
    setup_logger(dummy_config_basic)
    logger.info("Logger setup basic test.")


def test_setup_logger_with_file(dummy_config_file: AppConfig) -> None:
    """
    Test setup_logger adds file handler when enabled in config, using a temp log file.
    """
    setup_logger(dummy_config_file)
    logger.debug("Logger setup file test.")
    log_file = Path(dummy_config_file.logging.log_file)
    assert log_file.exists()
    assert log_file.read_text() != ""


def test_setup_logger_metrics_enabled(
    mocker: MockerFixture, dummy_config_metrics_enabled: AppConfig
) -> None:
    """
    Test setup_logger starts metrics server if prometheus_client is available.
    """
    prometheus_mod = types.ModuleType("prometheus_client")
    start_http_server_mock = mocker.Mock()
    prometheus_mod.start_http_server = start_http_server_mock  # type: ignore[attr-defined]
    mocker.patch.dict(sys.modules, {"prometheus_client": prometheus_mod})
    logger.remove()  # Reset logger state for isolation
    setup_logger(dummy_config_metrics_enabled)
    logger.info("Logger setup metrics enabled test.")
    start_http_server_mock.assert_called_once_with(8000)


def test_setup_logger_metrics_importerror(
    mocker: MockerFixture, dummy_config_metrics_importerror: AppConfig
) -> None:
    """
    Test setup_logger handles missing prometheus_client gracefully (ImportError).
    """
    # Patch builtins.__import__ to raise ImportError for prometheus_client
    original_import = builtins.__import__

    def fake_import(
        name: str,
        globals_: dict[str, Any] | None = None,
        locals_: dict[str, object] | None = None,
        fromlist: tuple[str, ...] | list[str] | None = (),
        level: int = 0,
    ) -> object:
        if name == "prometheus_client":
            msg = "No module named 'prometheus_client'"
            raise ImportError(msg)
        if fromlist is None:
            fromlist = ()
        return original_import(name, globals_, locals_, fromlist, level)

    mocker.patch("builtins.__import__", side_effect=fake_import)
    logger.remove()  # Reset logger state for isolation
    setup_logger(dummy_config_metrics_importerror)
    logger.info("Logger setup metrics ImportError test.")


def test_setup_logger_level(dummy_config_basic: AppConfig, capsys: CaptureFixture) -> None:
    """Test that the logger level from the config is respected."""
    dummy_config_basic.logging.level = "INFO"
    setup_logger(dummy_config_basic)

    logger.debug("This should not be logged.")
    logger.info("This should be logged.")
    logger.warning("This should also be logged.")

    captured = capsys.readouterr()
    assert "This should not be logged." not in captured.err
    assert "This should be logged." in captured.err
    assert "This should also be logged." in captured.err
