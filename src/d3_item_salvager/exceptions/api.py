"""Custom exception for API errors."""

from .base import BaseError


class ApiError(BaseError):
    """Custom exception for API errors.

    Args:
        message: Error message describing the API error.
        code: Integer error code (see error code table).
        context: Optional dict with additional error context (e.g., field, user_id).

    Example:
        >>> raise ApiError("Bad request", code=400, context={"field": "username"})
    """
