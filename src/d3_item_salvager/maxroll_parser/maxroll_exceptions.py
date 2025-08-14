"""Domain-specific exception hierarchy for Maxroll parsing components.

Provides clear separation between expected data/validation issues and unexpected errors,
enables easier user-facing error reporting, and improves testability.
"""

from __future__ import annotations

from typing import Any, Final

__all__: Final = [
    "BuildProfileError",
    "GuideCacheError",
    "GuideFetchError",
    "ItemDataError",
    "MaxrollError",
]


class MaxrollError(RuntimeError):
    """
    Base class for all Maxroll domain errors.
    """


class GuideFetchError(MaxrollError):
    """
    Raised when remote guide metadata cannot be fetched or parsed.
    """


class GuideCacheError(MaxrollError):
    """
    Raised for cache load/save problems (I/O, format, permissions).
    """


class BuildProfileError(MaxrollError):
    """
    Raised when build profile JSON is missing fields or structurally invalid.

    Args:
        message: Error message.
        file_path: Optional file path related to the error.
        context: Optional context dictionary.
    """

    def __init__(
        self,
        message: str,
        *,
        file_path: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.file_path = file_path
        self.context = context or {}


class ItemDataError(MaxrollError):
    """
    Raised for structural or validation issues when loading item master data.

    Args:
        message: Error message.
        data_path: Optional data path related to the error.
        key: Optional key related to the error.
    """

    def __init__(
        self,
        message: str,
        *,
        data_path: str | None = None,
        key: str | None = None,
    ) -> None:
        super().__init__(message)
        self.data_path = data_path
        self.key = key
