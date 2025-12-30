"""Unit tests for BackendClient error mapping behavior."""

from __future__ import annotations

import httpx
import pytest

from frontend.src.services.backend_client import BackendClient, BackendResponseError


def _make_resp_with_status(status: int) -> httpx.Response:
    req = httpx.Request("GET", "https://example.test")
    resp = httpx.Response(status_code=status, request=req)

    def raise_for_status() -> None:
        msg = "status error"
        raise httpx.HTTPStatusError(msg, request=req, response=resp)

    # Monkeypatch the raise_for_status method on the response
    resp.raise_for_status = raise_for_status  # type: ignore[attr-defined]
    return resp


def test_request_json_converts_4xx_to_backend_response_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = BackendClient(base_url="https://example.test", timeout_seconds=1.0)

    resp = _make_resp_with_status(400)

    def fake_request(*_args: object, **_kwargs: object) -> httpx.Response:
        return resp

    monkeypatch.setattr(client, "_client", type("C", (), {"request": fake_request})())

    with pytest.raises(BackendResponseError):
        client.request_json("GET", "/some/path")


def test_request_json_propagates_5xx_httpstatuserror(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = BackendClient(base_url="https://example.test", timeout_seconds=1.0)

    resp = _make_resp_with_status(502)

    def fake_request(*_args: object, **_kwargs: object) -> httpx.Response:
        return resp

    monkeypatch.setattr(client, "_client", type("C", (), {"request": fake_request})())

    with pytest.raises(httpx.HTTPStatusError):
        client.request_json("GET", "/some/path")
