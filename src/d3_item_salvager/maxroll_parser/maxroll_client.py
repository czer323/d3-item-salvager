"""
Central entry point for Maxroll parsing, guide fetching, and item data access.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .build_profile_parser import BuildProfileData, _BuildProfileParser
from .get_guide_urls import GuideInfo, _MaxrollGuideFetcher
from .guide_cache import _FileGuideCache
from .item_data_parser import _DataParser, ItemMeta
from .types import BuildProfileItems

if TYPE_CHECKING:
    from collections.abc import Mapping
    from d3_item_salvager.config.settings import AppConfig


class MaxrollClient:
    """
    Central entry point for Maxroll parsing, guide fetching, and item data access.

    This client simplifies interaction with the module by managing its own internal
    components, including parsers and caches. It ensures that data sources are
    initialized efficiently and that results are cached where appropriate.
    """

    def __init__(self, config: AppConfig) -> None:
        """
        Initializes MaxrollClient with the application configuration.

        Args:
            config: Application configuration.
        """
        self._config = config
        self._guide_cache = _FileGuideCache(config)
        self._guide_fetcher = _MaxrollGuideFetcher(config, cache=self._guide_cache)
        self._item_parser = _DataParser(config.maxroll_parser.data_paths)
        self._parser_cache: dict[str, _BuildProfileParser] = {}

    def _get_parser(self, file_path: str) -> _BuildProfileParser:
        """Gets a build profile parser from cache or creates a new one."""
        if file_path not in self._parser_cache:
            self._parser_cache[file_path] = _BuildProfileParser(file_path)
        return self._parser_cache[file_path]

    def get_guides(self) -> list[GuideInfo]:
        """
        Returns all available guides, using a cache to avoid redundant fetching.

        Returns:
            List of GuideInfo objects.
        """
        return self._guide_fetcher.fetch_guides()

    def get_build_profiles(self, file_path: str) -> list[BuildProfileData]:
        """
        Returns build profiles for a given build profile file path.

        Results are cached in memory to avoid re-parsing the same file.

        Args:
            file_path: Path to the build profile file.

        Returns:
            List of BuildProfileData objects.
        """
        parser = self._get_parser(file_path)
        return parser.profiles

    def get_item_usages(self, file_path: str) -> list[BuildProfileItems]:
        """
        Returns all item usages for a given build profile file path.

        Results are cached in memory to avoid re-parsing the same file.

        Args:
            file_path: Path to the build profile file.

        Returns:
            List of BuildProfileItems objects.
        """
        parser = self._get_parser(file_path)
        return parser.extract_usages()

    def get_item_data(self, item_id: str) -> ItemMeta | None:
        """
        Returns metadata for a given item ID.

        Args:
            item_id: The item ID to look up.

        Returns:
            ItemMeta if found, else None.
        """
        return self._item_parser.get_item(item_id)

    def get_all_items(self) -> Mapping[str, ItemMeta]:
        """
        Returns all item data available from the master item list.

        Returns:
            A mapping of item IDs to ItemMeta objects.
        """
        return self._item_parser.get_all_items()


__all__ = ["MaxrollClient"]
