"""
Module for fetching Diablo 3 build guides from Maxroll's Meilisearch API.
Provides a class-based interface for guide retrieval and future extension.
"""

import json
from pathlib import Path
from typing import Any

import requests
from loguru import logger

from d3_item_salvager.config.settings import AppConfig, get_config

from .get_guide_cache_utils import (
    load_guides_from_cache,
    save_guides_to_cache,
)
from .types import GuideInfo


class MaxrollGuideFetcher:
    """
    Fetches Diablo 3 build guides from Maxroll's Meilisearch API.
    Provides a public method for guide retrieval.
    """

    def __init__(self, app_config: AppConfig | None = None) -> None:
        self.app_config = app_config or get_config()
        # Load cache on instantiation
        self._cached_guides = load_guides_from_cache(self.app_config)

    def _fetch_hits_from_api(self) -> list[dict[str, Any]]:
        """
        Fetch raw hits from Maxroll API.

        Returns:
            list[dict[str, Any]]: List of raw hit dictionaries from the API.

        Raises:
            requests.RequestException: If the API request fails.
        """
        api_url = self.app_config.maxroll_parser.api_url
        bearer_token = self.app_config.maxroll_parser.bearer_token
        limit = self.app_config.maxroll_parser.limit

        headers = {
            "accept": "*/*",
            "authorization": f"Bearer {bearer_token}",
            "content-type": "application/json",
        }
        offset = 0
        all_hits: list[dict[str, Any]] = []
        try:
            while True:
                body: dict[str, Any] = {
                    "q": "",
                    "facets": [],
                    "limit": limit,
                    "offset": offset,
                }
                resp = requests.post(
                    api_url, headers=headers, data=json.dumps(body), timeout=10
                )
                resp.raise_for_status()
                data = resp.json()
                hits: list[dict[str, Any]] = data.get("hits", [])
                if not hits:
                    break
                all_hits.extend(hits)
                if len(hits) < limit:
                    break
                offset += limit
        except requests.RequestException:
            logger.exception("Failed to fetch hits from API")
            return []
        return all_hits

    def _extract_guide_links_from_hits(
        self, hits: list[dict[str, Any]]
    ) -> list[GuideInfo]:
        """
        Extract guide links from hits.

        Args:
            hits: List of hit dictionaries from the API.

        Returns:
            list[GuideInfo]: List of GuideInfo objects extracted from hits.
        """
        all_guides: list[GuideInfo] = []
        seen_urls: set[str] = set()
        for hit in hits:
            url = hit.get("permalink", "")
            if url.startswith("https://maxroll.gg/d3/guides/") and url not in seen_urls:
                build_slug = url.split("/d3/guides/")[-1].strip("/")
                name = build_slug.replace("-", " ").replace("guide", "Guide").strip()
                name = " ".join(
                    [w.capitalize() if w != "Guide" else w for w in name.split()]
                )
                all_guides.append(GuideInfo(name=name, url=url))
                seen_urls.add(url)
        return all_guides

    def _fetch_guides_from_api(self) -> list[GuideInfo]:
        """
        Fetch guides from Maxroll API.

        Returns:
            list[GuideInfo]: List of GuideInfo objects fetched from the API.
        """
        hits = self._fetch_hits_from_api()
        all_guides = self._extract_guide_links_from_hits(hits)
        logger.info("Fetched %d guides from API", len(all_guides))
        if all_guides:
            save_guides_to_cache(all_guides, self.app_config)
        return all_guides

    def fetch_guides(self) -> list[GuideInfo]:
        """
        Fetch all Diablo 3 build guides from Maxroll's Meilisearch API or local file, with caching.

        Returns:
            list[GuideInfo]: List of GuideInfo objects representing build guides.
        """
        if self._cached_guides is not None:
            return self._cached_guides
        api_url = self.app_config.maxroll_parser.api_url
        if api_url is not None and Path(api_url).is_file():
            # Local file: parse JSON and extract guide links
            with open(api_url, encoding="utf-8") as f:
                data = json.load(f)
            hits = data.get("hits", [])
            guides = self._extract_guide_links_from_hits(hits)
            logger.info("Fetched %d guides from local file", len(guides))
            if guides:
                save_guides_to_cache(guides, self.app_config)
            return guides
        # Otherwise, hit the API
        guides = self._fetch_guides_from_api()
        return guides

    def print_guides(self) -> None:
        """
        Fetch and log deduplicated build guide names and URLs.

        Returns:
            None
        """
        guides = self.fetch_guides()
        for guide in guides:
            logger.info("{}: {}", guide.name, guide.url)
        logger.info("Total guides found: {}", len(guides))
