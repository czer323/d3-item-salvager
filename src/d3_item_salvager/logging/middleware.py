"""API logging middleware for request/response logging."""

from loguru import logger


def log_api_request(request: object, response: object) -> None:
    """Log API request and response details with contextual information.

    Args:
        request: API request object (must have path, method, headers, body attributes)
        response: API response object (must have status_code, body attributes)
    """
    # Defensive extraction of request_id
    headers = getattr(request, "headers", {})
    request_id = None
    if isinstance(headers, dict):
        request_id = headers.get("X-Request-ID")
    elif hasattr(headers, "get"):
        try:
            request_id = headers.get("X-Request-ID")
        except TypeError:
            request_id = None
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
