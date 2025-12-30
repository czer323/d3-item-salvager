"""Unit tests for `frontend.src.routes.items` error handling."""

from __future__ import annotations

from typing import TYPE_CHECKING

from frontend.src.routes import items
from frontend.src.services.backend_client import (
    BackendResponseError,
    BackendTransportError,
)
from frontend.src.services.preferences import PreferencesValidationError

if TYPE_CHECKING:
    import pytest
    from flask.testing import FlaskClient


def test_summary_json_returns_400_on_validation_error(
    client: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise_validation(_client_arg: object, _source: object) -> None:
        msg = "bad prefs"
        raise PreferencesValidationError(msg)

    monkeypatch.setattr(items, "_build_usage_table", _raise_validation)

    resp = client.get("/frontend/items/summary.json")

    assert resp.status_code == 400
    assert resp.get_json() == {"error": "Invalid request parameters"}


def test_summary_json_returns_503_on_transport_error(
    client: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise_transport(_client_arg: object, _source: object) -> None:
        msg = "timeout"
        raise BackendTransportError(msg)

    monkeypatch.setattr(items, "_build_usage_table", _raise_transport)

    resp = client.get("/frontend/items/summary.json")

    assert resp.status_code == 503
    assert resp.get_json() == {"error": "Service temporarily unavailable"}


def test_summary_json_returns_502_on_backend_response_error(
    client: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise_response(_client_arg: object, _source: object) -> None:
        msg = "bad status"
        raise BackendResponseError(msg)

    monkeypatch.setattr(items, "_build_usage_table", _raise_response)

    resp = client.get("/frontend/items/summary.json")

    assert resp.status_code == 502
    assert resp.get_json() == {"error": "Upstream service error"}


def test_summary_json_returns_500_on_unexpected_error(
    client: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise_unexpected(_client_arg: object, _source: object) -> None:
        msg = "oh no"
        raise RuntimeError(msg)

    monkeypatch.setattr(items, "_build_usage_table", _raise_unexpected)

    resp = client.get("/frontend/items/summary.json")

    assert resp.status_code == 500
    assert resp.get_json() == {"error": "Internal server error"}
