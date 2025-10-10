"""Adapters for integrating third-party loggers with project protocols."""

from __future__ import annotations

from loguru import logger as loguru_logger

from d3_item_salvager.services.protocols import ServiceLogger


class LoguruServiceLogger(ServiceLogger):
    """Adapter that delegates logging calls to the global Loguru logger."""

    def debug(self, message: str, *args: object, **kwargs: object) -> None:
        """Log a debug-level message."""
        loguru_logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: object, **kwargs: object) -> None:
        """Log an info-level message."""
        loguru_logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: object, **kwargs: object) -> None:
        """Log a warning-level message."""
        loguru_logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: object, **kwargs: object) -> None:
        """Log an error-level message."""
        loguru_logger.error(message, *args, **kwargs)

    def exception(self, message: str, *args: object, **kwargs: object) -> None:
        """Log an exception-level message including traceback context."""
        loguru_logger.exception(message, *args, **kwargs)


def get_loguru_service_logger() -> ServiceLogger:
    """Return a ServiceLogger instance backed by Loguru."""
    return LoguruServiceLogger()
