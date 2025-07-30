"""Custom exception for scraping/parsing/network errors."""

from .base import BaseError


class ScrapingError(BaseError):
    """Custom exception for scraping/parsing/network errors.

    Args:
        message: Error message describing the scraping error.
        code: Integer error code (see error code table).
        context: Optional dict with additional error context (e.g., url, step).

    Example:
        >>> raise ScrapingError(
        ...     "Parsing error", code=2002, context={"url": "https://example.com/guide"}
        ... )
    """
