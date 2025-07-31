# pylint: disable=too-few-public-methods
"""Unit tests for custom exceptions in d3_item_salvager.exceptions module."""

from fastapi import FastAPI

from d3_item_salvager.exceptions import (
    ApiError,
    BaseError,
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


class TestBaseError:
    """Test the BaseError class for correct"""

    def test_attributes(self) -> None:
        """Test that BaseError sets message, code, and context attributes correctly."""
        err = BaseError("msg", 123, {"foo": "bar"})
        assert err.message == "msg"
        assert err.code == 123
        assert err.context == {"foo": "bar"}

    def test_str(self) -> None:
        """Test that BaseError string representation includes all key fields."""
        err = BaseError("msg", 123, {"foo": "bar"})
        s = str(err)
        assert "BaseError" in s
        assert "msg" in s
        assert "123" in s
        assert "foo" in s


class TestDataError:
    """Test the DataError class for correct inheritance and attributes."""

    def test_inheritance(self) -> None:
        """Test that DataError is a subclass of BaseError and sets code/context."""
        err = DataError("fail", 1001, {"field": "item_id"})
        assert isinstance(err, BaseError)
        assert err.code == 1001
        assert err.context["field"] == "item_id"


class TestScrapingError:
    """Test the ScrapingError class for correct inheritance and attributes."""

    def test_inheritance(self) -> None:
        """Test that ScrapingError is a subclass of BaseError and sets code/context."""
        err = ScrapingError("parse", 2002, {"url": "x"})
        assert isinstance(err, BaseError)
        assert err.code == 2002
        assert err.context["url"] == "x"


class TestApiError:
    """Test the ApiError class for correct"""

    def test_inheritance(self) -> None:
        """Test that ApiError is a subclass of BaseError and sets code/context."""
        err = ApiError("bad", 400, {"field": "username"})
        assert isinstance(err, BaseError)
        assert err.code == 400
        assert err.context["field"] == "username"
