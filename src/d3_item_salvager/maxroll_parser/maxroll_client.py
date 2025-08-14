"""
Central entry point for Maxroll parsing, guide fetching, and item data access.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .build_profile_parser import BuildProfileData, BuildProfileParser
from .get_guide_urls import GuideInfo, MaxrollGuideFetcher
from .guide_cache import FileGuideCache
from .item_data_parser import DataParser, ItemMeta

if TYPE_CHECKING:
    from d3_item_salvager.config.settings import AppConfig


class MaxrollClient:
    """
    Central entry point for Maxroll parsing, guide fetching, and item data access.

    Provides methods to fetch guides, build profiles, and item data using the configured
    Maxroll parser components and cache.
    """

    def get_guides(self) -> list[GuideInfo]:
        """
        Returns all available guides (cached or fetched).

        Returns:
            List of GuideInfo objects.
        """
        return self.guide_fetcher.fetch_guides()

    def get_build_profiles(self, file_path: str) -> list[BuildProfileData]:
        """
        Returns build profiles for a given build profile file path.

        Args:
            file_path: Path to the build profile file.

        Returns:
            List of BuildProfileData objects.
        """
        parser = self.profile_parser(file_path)
        return parser.profiles

    def get_item_data(self, item_id: str) -> ItemMeta | None:
        """
        Returns item data for a given item id.

        Args:
            item_id: The item id to look up.

        Returns:
            ItemMeta if found, else None.
        """
        parser = self.item_parser()
        return parser.get_item(item_id)

    def get_all_items(self) -> dict[str, ItemMeta]:
        """
        Returns all item data available.

        Returns:
            Dictionary mapping item ids to ItemMeta objects.
        """
        parser = self.item_parser()
        return parser.get_all_items()

    def __init__(
        self,
        config: AppConfig,
        *,
        cache: FileGuideCache | None = None,
    ) -> None:
        """
        Initializes MaxrollClient with configuration and optional cache.

        Args:
            config: Application configuration.
            cache: Optional FileGuideCache instance.
        """
        self.config = config
        self.cache = cache or FileGuideCache(config)
        self._guide_fetcher: MaxrollGuideFetcher | None = None
        self._profile_parser: BuildProfileParser | None = None
        self._item_parser: DataParser | None = None

    @property
    def guide_fetcher(self) -> MaxrollGuideFetcher:
        """
        Returns the MaxrollGuideFetcher instance.

        Returns:
            MaxrollGuideFetcher object.
        """
        if self._guide_fetcher is None:
            self._guide_fetcher = MaxrollGuideFetcher(self.config, cache=self.cache)
        return self._guide_fetcher

    def profile_parser(self, file_path: str) -> BuildProfileParser:
        """
        Returns a BuildProfileParser for the given file path.

        Args:
            file_path: Path to the build profile file.

        Returns:
            BuildProfileParser object.
        """
        return BuildProfileParser(file_path)

    def item_parser(self) -> DataParser:
        """
        Returns a DataParser instance for item data.

        Returns:
            DataParser object.
        """
        return DataParser(self.config.maxroll_parser.data_paths)


__all__ = ["MaxrollClient"]
