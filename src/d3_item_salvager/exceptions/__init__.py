"""Exceptions module for Diablo 3 Item Salvager.

Provides all custom exception types and handler registration utilities for FastAPI.
Use `register_exception_handlers(app)` to register all handlers in one step.
"""

from fastapi import FastAPI

from .api import ApiError
from .base import BaseError
from .data import DataError
from .handlers import (
    handle_api_error,
    handle_data_error,
    handle_scraping_error,
    map_error_code_to_http,
)
from .scraping import ScrapingError


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers with a FastAPI app.

    Args:
        app: FastAPI application instance.

    Example:
        from d3_item_salvager.exceptions import register_exception_handlers
        app = FastAPI()
        register_exception_handlers(app)
    """
    app.add_exception_handler(ApiError, handle_api_error)
    app.add_exception_handler(DataError, handle_data_error)
    app.add_exception_handler(ScrapingError, handle_scraping_error)


__all__ = [
    "ApiError",
    "BaseError",
    "DataError",
    "ScrapingError",
    "handle_api_error",
    "handle_data_error",
    "handle_scraping_error",
    "map_error_code_to_http",
    "register_exception_handlers",
]
