"""Unit test for register_exception_handlers utility in d3_item_salvager.exceptions."""

from fastapi import FastAPI

from d3_item_salvager.exceptions import (
    ApiError,
    DataError,
    ScrapingError,
    handle_api_error,
    handle_data_error,
    handle_scraping_error,
    register_exception_handlers,
)


def test_register_exception_handlers() -> None:
    """Test that all custom exception handlers are registered with FastAPI app."""
    app = FastAPI()
    register_exception_handlers(app)
    # FastAPI stores handlers in app.exception_handlers dict
    assert app.exception_handlers[ApiError] is handle_api_error
    assert app.exception_handlers[DataError] is handle_data_error
    assert app.exception_handlers[ScrapingError] is handle_scraping_error
