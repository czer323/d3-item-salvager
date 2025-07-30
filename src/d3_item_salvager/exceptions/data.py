"""Custom exception for data/model errors."""

from .base import BaseError


class DataError(BaseError):
    """Custom exception for data/model errors.

    Args:
        message: Error message describing the data error.
        code: Integer error code (see error code table).
        context: Optional dict with additional error context (e.g., field, model).

    Example:
        >>> raise DataError(
        ...     "Data validation failed", code=1001, context={"field": "item_id"}
        ... )
    """
