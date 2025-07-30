"""
Exception Handlers for D3 Item Salvager.

This module provides FastAPI-compatible exception handlers for domain-specific errors:
    - DataError: Data/model validation and integrity errors
    - ScrapingError: Scraping, parsing, and network errors
    - ApiError: API request/response errors

Each handler logs the error and returns a structured JSON response with a mapped HTTP status code.

Recommended usage (register all handlers at once):
    from fastapi import FastAPI
    from d3_item_salvager.exceptions import register_exception_handlers

    app = FastAPI()
    register_exception_handlers(app)

Direct usage (register handlers individually):
    from d3_item_salvager.exceptions import handlers, DataError, ScrapingError, ApiError
    app.add_exception_handler(DataError, handlers.handle_data_error)
    app.add_exception_handler(ScrapingError, handlers.handle_scraping_error)
    app.add_exception_handler(ApiError, handlers.handle_api_error)

Example (Custom raise):
    raise DataError("Validation failed", code=1001, context={"field": "item_id"})

Returns JSON response:
    {
        "error": {
            "message": "Validation failed",
            "code": 1001,
            "context": {"field": "item_id"}
        }
    }
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger

from .api import ApiError
from .data import DataError
from .scraping import ScrapingError


def map_error_code_to_http(code: int) -> int:
    """Map custom error codes to HTTP status codes."""
    mapping = {
        1001: 422,
        1002: 404,
        1003: 500,
        2001: 500,
        2002: 422,
        2003: 502,
        400: 400,
        404: 404,
        422: 422,
        500: 500,
    }
    return mapping.get(code, 500)


def handle_data_error(_request: Request, exc: Exception) -> JSONResponse:
    """Handle DataError exceptions and return a structured JSON response.

    Args:
        _request: FastAPI request object (unused).
        exc: The DataError exception instance (as Exception).

    Returns:
        JSONResponse with error details and appropriate HTTP status code.
    """
    if not isinstance(exc, DataError):
        msg = "Expected DataError"
        raise TypeError(msg)
    http_code = map_error_code_to_http(exc.code)
    logger.error(
        f"Data error: {exc.message} (code={exc.code})", extra={"context": exc.context}
    )
    return JSONResponse(
        status_code=http_code,
        content={
            "error": {"message": exc.message, "code": exc.code, "context": exc.context}
        },
    )


def handle_scraping_error(_request: Request, exc: Exception) -> JSONResponse:
    """Handle ScrapingError exceptions and return a structured JSON response.

    Args:
        _request: FastAPI request object (unused).
        exc: The ScrapingError exception instance (as Exception).

    Returns:
        JSONResponse with error details and appropriate HTTP status code.
    """
    if not isinstance(exc, ScrapingError):
        msg = "Expected ScrapingError"
        raise TypeError(msg)
    http_code = map_error_code_to_http(exc.code)
    logger.error(
        f"Scraping error: {exc.message} (code={exc.code})",
        extra={"context": exc.context},
    )
    return JSONResponse(
        status_code=http_code,
        content={
            "error": {"message": exc.message, "code": exc.code, "context": exc.context}
        },
    )


def handle_api_error(_request: Request, exc: Exception) -> JSONResponse:
    """Handle ApiError exceptions and return a structured JSON response.

    Args:
        _request: FastAPI request object (unused).
        exc: The ApiError exception instance (as Exception).

    Returns:
        JSONResponse with error details and appropriate HTTP status code.
    """
    if not isinstance(exc, ApiError):
        msg = "Expected ApiError"
        raise TypeError(msg)
    http_code = map_error_code_to_http(exc.code)
    logger.error(
        f"API error: {exc.message} (code={exc.code})", extra={"context": exc.context}
    )
    return JSONResponse(
        status_code=http_code,
        content={
            "error": {"message": exc.message, "code": exc.code, "context": exc.context}
        },
    )
