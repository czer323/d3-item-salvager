"""Service-layer protocols and shared type aliases."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

from sqlmodel import Session

from d3_item_salvager.maxroll_parser.protocols import (
    BuildProfileParserProtocol,
    GuideFetcherProtocol,
    ItemDataParserProtocol,
)
from d3_item_salvager.maxroll_parser.types import (
    BuildProfileData,
    BuildProfileItems,
    GuideInfo,
)


class ServiceLogger(Protocol):
    """Minimal logging interface required by services."""

    def debug(self, message: str, *args: object, **kwargs: object) -> None:
        """Log a debug-level message with optional formatting arguments."""

    def info(self, message: str, *args: object, **kwargs: object) -> None:
        """Log an info-level message with optional formatting arguments."""

    def warning(self, message: str, *args: object, **kwargs: object) -> None:
        """Log a warning-level message with optional formatting arguments."""

    def error(self, message: str, *args: object, **kwargs: object) -> None:
        """Log an error-level message with optional formatting arguments."""

    def exception(self, message: str, *args: object, **kwargs: object) -> None:
        """Log an exception-level message including traceback information."""


ParserFactory = Callable[[str], BuildProfileParserProtocol]
SessionFactory = Callable[[], Session]
GuideFetcher = GuideFetcherProtocol
ItemDataProvider = ItemDataParserProtocol
BuildProfilePayload = Sequence[BuildProfileData]
BuildItemUsagePayload = Sequence[BuildProfileItems]
GuideList = Sequence[GuideInfo]
