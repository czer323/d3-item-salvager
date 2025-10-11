"""API logging middleware for request/response logging."""

from collections.abc import Mapping
from typing import Protocol, cast, runtime_checkable

from loguru import logger


@runtime_checkable
class _HeaderLike(Protocol):
    def get(self, key: str, default: str | None = None) -> str | None:
        """Retrieve a header value if available."""


def log_api_request(request: object, response: object) -> None:
    """Log API request and response details with contextual information.

    Args:
        request: API request object (must have path, method, headers, body attributes)
        response: API response object (must have status_code, body attributes)
    """
    # Defensive extraction of request_id
    headers_obj = getattr(request, "headers", None)
    request_id: str | None = None
    raw_request_id: str | None = None
    if isinstance(headers_obj, Mapping):
        mapped_headers = cast("Mapping[str, object]", headers_obj)
        header_value = mapped_headers.get("X-Request-ID")
        if isinstance(header_value, str):
            raw_request_id = header_value
    elif isinstance(headers_obj, _HeaderLike):
        raw_request_id = headers_obj.get("X-Request-ID")

    if isinstance(raw_request_id, str):
        request_id = raw_request_id
    api_logger = logger.bind(
        endpoint=getattr(request, "path", None),
        method=getattr(request, "method", None),
        request_id=request_id,
        status_code=getattr(response, "status_code", None),
    )
    api_logger.info(
        "API request",
        request_body=getattr(request, "body", None),
        response_body=getattr(response, "body", None),
    )
    if getattr(response, "status_code", 200) >= 400:
        api_logger.error("API error", error=getattr(response, "body", None))
