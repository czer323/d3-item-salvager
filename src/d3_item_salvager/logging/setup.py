# Error capture decorator is Loguru's @logger.catch, used directly on functions
"""Logger setup/configuration for d3_item_salvager project."""

import sys
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, cast

from loguru import logger

from d3_item_salvager.config.settings import AppConfig

__all__ = ["logger"]


def log_timing[T](func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to log function start, end, and duration using Loguru.

    Args:
        func: The function to decorate.

    Returns:
        Callable[..., T]: The wrapped function with timing logs.
    """

    def wrapper(*args: object, **kwargs: object) -> T:
        start = time.time()
        func_name = getattr(func, "__name__", repr(func))
        logger.info("Started {}", func_name)
        result: T = func(*args, **kwargs)
        logger.info("Finished {} in {:.2f}s", func_name, time.time() - start)
        return result

    return cast("Callable[..., T]", wrapper)


def log_contextual[T](
    context: dict[str, Any],
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to bind contextual information to log records.

    Args:
        context: Dictionary of contextual information to bind to log records.

    Returns:
        Callable[[Callable[..., T]], Callable[..., T]]:
            A decorator that wraps the function with contextual logging.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: object, **kwargs: object) -> T:
            bound_logger = logger.bind(**context)
            func_name = getattr(func, "__name__", repr(func))
            bound_logger.info("Calling {}", func_name)
            result: T = func(*args, **kwargs)
            bound_logger.info("Finished {}", func_name)
            return result

        return cast("Callable[..., T]", wrapper)

    return decorator


def setup_logger(app_config: AppConfig) -> None:
    """
    Configure Loguru logger for the project using config settings.

    Args:
        app_config: AppConfig instance.

    Returns:
        None

    Raises:
        ImportError: If Prometheus metrics are enabled but prometheus_client is not installed.
    """
    # Local import to avoid circular import
    # Only needed for type checking, not runtime
    # from d3_item_salvager.config.settings import AppConfig
    logging_config = app_config.logging
    logger.remove()
    logger.add(
        sys.stderr,
        level=logging_config.level,
        format="<green>{time}</green> | <cyan>{name}</cyan>:<yellow>{function}</yellow>:<magenta>{line}</magenta> | <level>{message}</level>",  # pylint: disable=line-too-long
        colorize=True,
    )
    if logging_config.enabled:
        logger.add(
            logging_config.log_file,
            level=logging_config.level,
            rotation="1 week",
            retention="10 days",
            compression="zip",
        )
    if logging_config.metrics_enabled:
        try:
            from prometheus_client import (  # pylint: disable=import-outside-toplevel
                start_http_server,
            )

            logger.info("Starting Prometheus metrics server on port 8000")
            start_http_server(8000)
        except ImportError:
            logger.warning(
                "Prometheus metrics enabled but prometheus_client not installed."
            )
