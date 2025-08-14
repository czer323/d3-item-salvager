# pylint: disable=unnecessary-ellipsis
"""Protocol interfaces for the Maxroll parsing domain.

Defines structural contracts for higher-level composition and dependency injection
without requiring concrete class inheritance. Only behavior consumed outside a concrete
module is captured here; internal helper methods remain private.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:  # Local imports for type checking only
    from collections.abc import Iterable, Mapping

    from .types import (
        BuildProfileData,
        BuildProfileItems,
        GuideInfo,
        ItemMeta,
    )


@runtime_checkable
class GuideFetcherProtocol(Protocol):
    """
    Interface for fetching guide metadata from a remote source.
    """

    def fetch_guides(
        self,
        search: str | None = None,
        *,
        force_refresh: bool = False,
    ) -> list[Any]:
        """Fetch guide list, optionally filtering by *search* string."""
        ...

    def get_guide_by_id(self, guide_id: str) -> GuideInfo | None:
        """Fetch a single guide by its unique ID."""
        ...


@runtime_checkable
class BuildProfileParserProtocol(Protocol):  # pragma: no cover - structural
    """
    Interface for parsing and exposing build profile data.
    """

    profiles: list[BuildProfileData]

    def extract_usages(self) -> list[BuildProfileItems]:
        """Return flattened list of item usages across all profiles."""
        ...

    def parse_profile(self, file_path: str) -> object:
        """Parse a build profile from the given file path and return the parsed object."""
        ...


@runtime_checkable
class ItemDataParserProtocol(Protocol):  # pragma: no cover - structural
    """
    Interface for accessing item master data.
    """

    def get_item(self, item_id: str) -> ItemMeta | None:
        """Return metadata for *item_id* if present."""
        ...

    def get_all_items(self) -> Mapping[str, ItemMeta]:
        """Return mapping of all item id -> :class:`ItemMeta`."""
        ...


@runtime_checkable
class GuideCacheProtocol(Protocol):  # pragma: no cover - structural
    """
    Cache interface for persisting and retrieving guide metadata.

    Implementations are responsible for their own freshness/TTL logic.
    """

    def load(self) -> list[GuideInfo] | None:
        """Return cached guides if present and still *fresh* else ``None``."""
        ...

    def save(self, guides: Iterable[GuideInfo]) -> None:
        """Persist the supplied guides (best effort)."""
        ...


@runtime_checkable
class PluginProtocol(Protocol):  # pragma: no cover - structural
    """
    Generic plugin contract (deliberately minimal).

    A plugin can expose any number of callable capabilities; the client stores
    them opaque but typed interaction can be achieved by also implementing one
    of the more specific protocols above.
    """

    name: str  # human readable identifier

    def close(self) -> None:  # pragma: no cover - optional behaviour
        """Close / release any resources (optional)."""
        ...

    def run(self, *args: object, **kwargs: object) -> object:
        """Run the plugin with the given arguments and return the result."""
        ...


__all__ = [
    "BuildProfileParserProtocol",
    "GuideCacheProtocol",
    "GuideFetcherProtocol",
    "ItemDataParserProtocol",
    "PluginProtocol",
]
