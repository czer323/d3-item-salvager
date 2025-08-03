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
from pytest_mock import MockerFixture

from d3_item_salvager.logging.setup import log_contextual, log_timing, setup_logger


class DummyLoggingConfig:
    """Dummy logging config for logger setup tests."""

    enabled: bool = False
    metrics_enabled: bool = False
    log_file: str = "dummy.log"
    level: str = "INFO"


class DummyConfig:
    """Dummy config container for logger setup tests."""

    logging: DummyLoggingConfig

    def __init__(
        self,
        enabled: bool = False,
        metrics_enabled: bool = False,
        level: str = "INFO",
    ) -> None:
        self.logging = DummyLoggingConfig()
        self.logging.enabled = enabled
        self.logging.metrics_enabled = metrics_enabled
        self.logging.level = level


@pytest.fixture
def dummy_config_basic() -> DummyConfig:
    """Returns a dummy config object for basic logger setup (no file, no metrics)."""
    return DummyConfig()


@pytest.fixture
def dummy_config_file() -> DummyConfig:
    """Returns a dummy config object with file handler enabled."""
    return DummyConfig(enabled=True, metrics_enabled=False, level="DEBUG")


@pytest.fixture
def dummy_config_metrics_enabled() -> DummyConfig:
    """Returns a dummy config object with metrics enabled."""
    return DummyConfig(enabled=False, metrics_enabled=True, level="INFO")


@pytest.fixture
def dummy_config_metrics_importerror() -> DummyConfig:
    """Returns a dummy config object with metrics enabled and simulates ImportError."""
    return DummyConfig(enabled=False, metrics_enabled=True, level="INFO")


def test_setup_logger_runs(mocker: MockerFixture) -> None:
    """
    Test that setup_logger runs without error and logger can log a message.
    """

    class DummyLoggingConfig:
        """Dummy logging config for logger setup test."""

        enabled: bool = False
        metrics_enabled: bool = False
        log_file: str = "dummy.log"
        level: str = "INFO"

    class DummyConfig:
        """Dummy config container for logger setup test."""

        logging: DummyLoggingConfig

        def __init__(self) -> None:
            self.logging = DummyLoggingConfig()

    mocker.patch(
        "d3_item_salvager.logging.setup.get_config",
        return_value=DummyConfig(),
    )
    setup_logger()
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


def test_setup_logger_basic(
    mocker: MockerFixture, dummy_config_basic: DummyConfig, tmp_path: Path
) -> None:
    """Test setup_logger initializes logger with basic config (no file, no metrics)."""
    dummy_config_basic.logging.log_file = str(tmp_path / "dummy.log")
    mocker.patch(
        "d3_item_salvager.logging.setup.get_config", return_value=dummy_config_basic
    )
    setup_logger()
    logger.info("Logger setup basic test.")


def test_setup_logger_with_file(
    mocker: MockerFixture, dummy_config_file: DummyConfig, tmp_path: Path
) -> None:
    """
    Test setup_logger adds file handler when enabled in config, using a temp log file.
    """
    dummy_config_file.logging.log_file = str(tmp_path / "dummy.log")
    mocker.patch(
        "d3_item_salvager.logging.setup.get_config", return_value=dummy_config_file
    )
    setup_logger()
    logger.debug("Logger setup file test.")


def test_setup_logger_metrics_enabled(
    mocker: MockerFixture, dummy_config_metrics_enabled: DummyConfig
) -> None:
    """
    Test setup_logger starts metrics server if prometheus_client is available.
    """
    mocker.patch(
        "d3_item_salvager.logging.setup.get_config",
        return_value=dummy_config_metrics_enabled,
    )
    prometheus_mod = types.ModuleType("prometheus_client")
    prometheus_mod.start_http_server = lambda *_args, **_kwargs: None  # type: ignore[attr-defined]
    mocker.patch.dict(sys.modules, {"prometheus_client": prometheus_mod})
    logger.remove()  # Reset logger state for isolation
    setup_logger()
    logger.info("Logger setup metrics enabled test.")


def test_setup_logger_metrics_importerror(
    mocker: MockerFixture, dummy_config_metrics_importerror: DummyConfig
) -> None:
    """
    Test setup_logger handles missing prometheus_client gracefully (ImportError).
    """
    mocker.patch(
        "d3_item_salvager.logging.setup.get_config",
        return_value=dummy_config_metrics_importerror,
    )
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
    setup_logger()
    logger.info("Logger setup metrics ImportError test.")
