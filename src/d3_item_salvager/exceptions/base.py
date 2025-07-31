"""Base exception class for all domain errors in the d3_item_salvager application."""


class BaseError(Exception):
    """Base exception for all domain errors.

    Args:
        message: Error message describing the exception.
        code: Integer error code (see error code table).
        context: Optional dict with additional error context.

    Attributes:
        message: Error message string.
        code: Integer error code.
        context: Dictionary with extra error context.

    Example:
        >>> raise BaseError(
        ...     "Something went wrong", code=500, context={"operation": "update"}
        ... )
    """

    def __init__(self, message: str, code: int, context: dict | None = None) -> None:
        """Initialize a BaseError.

        Args:
            message: Error message string.
            code: Integer error code.
            context: Optional dictionary with extra error context.
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}

    def __str__(self) -> str:
        """Return a string representation of the error.

        Returns:
            str: String describing the error type, message, code, and context.
        """
        return (
            f"{self.__class__.__name__}(message={self.message!r}, "
            f"code={self.code}, "
            f"context={self.context})"
        )
