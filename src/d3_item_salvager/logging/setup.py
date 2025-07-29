# Error capture decorator is Loguru's @logger.catch, used directly on functions
"""Logger setup/configuration for d3_item_salvager project."""

import sys
import time
from collections.abc import Callable
from functools import wraps
from typing import cast

from loguru import logger

from d3_item_salvager.config.settings import get_config


def log_timing[T](func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to log function start, end, and duration using Loguru."""

    def wrapper(*args: object, **kwargs: object) -> T:
        start = time.time()
        func_name = getattr(func, "__name__", repr(func))
        logger.info("Started {}", func_name)
        result: T = func(*args, **kwargs)
        logger.info("Finished {} in {:.2f}s", func_name, time.time() - start)
        return result

    return cast("Callable[..., T]", wrapper)


def log_contextual[T](context: dict) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to bind contextual information to log records."""

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


def setup_logger() -> None:
    """Configure Loguru logger for the project using config settings."""
    config = get_config().logging
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time}</green> | <cyan>{name}</cyan>:<yellow>{function}</yellow>:<magenta>{line}</magenta> | <level>{message}</level>",  # pylint: disable=line-too-long
        colorize=True,
    )
    if config.enabled:
        logger.add(
            config.log_file,
            level=config.level,
            rotation="1 week",
            retention="10 days",
            compression="zip",
        )
    if config.metrics_enabled:
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
