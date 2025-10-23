"""HTTP client utilities for communicating with the FastAPI backend."""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:  # pragma: no cover - type checking only import
    from types import TracebackType


JSONPrimitive = str | int | float | bool | None
JSONType = JSONPrimitive | dict[str, "JSONType"] | list["JSONType"]
QueryParamValue = str | int | float | bool | None
QueryParams = Mapping[str, QueryParamValue]


class BackendClientError(RuntimeError):
    """Raised when a backend request fails permanently."""


class BackendTransportError(BackendClientError):
    """Raised when the backend is unreachable after retries."""


class BackendResponseError(BackendClientError):
    """Raised when the backend returns an unexpected HTTP status."""


@dataclass(slots=True)
class BackendClient:
    """Thin wrapper around httpx with retry and error translation helpers."""

    base_url: str
    timeout_seconds: float
    max_attempts: int = 3
    backoff_seconds: float = 0.25
    _client: httpx.Client = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._client = httpx.Client(
            base_url=self.base_url, timeout=self.timeout_seconds
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def request_json(
        self,
        method: str,
        path: str,
        *,
        params: QueryParams | None = None,
        json: Mapping[str, JSONType] | None = None,
    ) -> JSONType:
        """Execute a request and return the decoded JSON payload."""
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = self._client.request(
                    method=method,
                    url=path,
                    params=params,
                    json=json,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                raise BackendResponseError(str(exc)) from exc
            except httpx.RequestError as exc:
                last_error = exc
                if attempt == self.max_attempts:
                    break
                sleep_seconds = self.backoff_seconds * attempt
                time.sleep(sleep_seconds)
        msg = "Backend request failed after retries"
        raise BackendTransportError(msg) from last_error

    def get_json(
        self,
        path: str,
        *,
        params: QueryParams | None = None,
    ) -> JSONType:
        """Issue a GET request for a JSON resource."""
        return self.request_json("GET", path, params=params)

    def post_json(
        self,
        path: str,
        *,
        params: QueryParams | None = None,
        json: Mapping[str, JSONType] | None = None,
    ) -> JSONType:
        """Issue a POST request and return the JSON response body."""
        return self.request_json("POST", path, params=params, json=json)

    def __enter__(self) -> BackendClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
