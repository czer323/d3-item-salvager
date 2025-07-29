"""
Module for fetching Diablo 3 build guides from Maxroll's Meilisearch API.
Provides a class-based interface for guide retrieval and future extension.
"""

import json
import logging
from pathlib import Path

import requests

from d3_item_salvager.config import get_config

from .get_guide_cache_utils import (
    load_guides_from_cache,
    save_guides_to_cache,
)
from .types import GuideInfo

CONFIG = get_config()
DEFAULT_MAXROLL_API_URL = CONFIG.maxroll_parser.api_url
DEFAULT_BEARER_TOKEN = CONFIG.maxroll_parser.bearer_token


class MaxrollGuideFetcher:
    """
    Fetches Diablo 3 build guides from Maxroll's Meilisearch API.
    Provides a public method for guide retrieval.
    """

    def __init__(
        self,
        api_url: str = DEFAULT_MAXROLL_API_URL,
        bearer_token: str | None = DEFAULT_BEARER_TOKEN,
        logger: logging.Logger | None = None,
        cache_ttl: int = 604800,  # seconds
        cache_file: str | None = None,
        limit: int = 21,
    ) -> None:
        self.api_url = api_url
        self.bearer_token = bearer_token
        self.logger = logger or logging.getLogger(__name__)
        self.cache_ttl = cache_ttl
        self.limit = limit
        # Default cache file location: <project-root>/cache/maxroll_guides.json
        if cache_file is None:
            self.cache_path = Path(Path.cwd(), "cache", "maxroll_guides.json")
        else:
            self.cache_path = Path(cache_file)
        # Load cache on instantiation
        self._cached_guides = load_guides_from_cache(
            self.cache_path, self.cache_ttl, self.logger
        )

    def _fetch_hits_from_api(self) -> list[dict]:
        """
        Fetch raw hits from Maxroll API.
        """
        headers = {
            "accept": "*/*",
            "authorization": f"Bearer {self.bearer_token}",
            "content-type": "application/json",
        }
        offset = 0
        all_hits: list[dict] = []
        try:
            while True:
                body = {"q": "", "facets": [], "limit": self.limit, "offset": offset}
                resp = requests.post(
                    self.api_url, headers=headers, data=json.dumps(body), timeout=10
                )
                resp.raise_for_status()
                data = resp.json()
                hits = data.get("hits", [])
                if not hits:
                    break
                all_hits.extend(hits)
                if len(hits) < self.limit:
                    break
                offset += self.limit
        except requests.RequestException:
            self.logger.exception("Failed to fetch hits from API")
            return []
        return all_hits

    def _extract_guide_links_from_hits(self, hits: list[dict]) -> list[GuideInfo]:
        """
        Extract guide links from hits.
        """
        all_guides: list[GuideInfo] = []
        seen_urls = set()
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
        """
        hits = self._fetch_hits_from_api()
        all_guides = self._extract_guide_links_from_hits(hits)
        self.logger.info("Fetched %d guides from API", len(all_guides))
        if all_guides:
            save_guides_to_cache(all_guides, self.cache_path, self.logger)
        return all_guides

    def fetch_guides(self) -> list[GuideInfo]:
        """
        Fetch all Diablo 3 build guides from Maxroll's Meilisearch API or local file, with caching.
        """
        if self._cached_guides is not None:
            return self._cached_guides
        if Path(self.api_url).is_file():
            # Local file: parse JSON and extract guide links
            with open(self.api_url, encoding="utf-8") as f:
                data = json.load(f)
            hits = data.get("hits", [])
            guides = self._extract_guide_links_from_hits(hits)
            self.logger.info("Fetched %d guides from local file", len(guides))
            if guides:
                save_guides_to_cache(guides, self.cache_path, self.logger)
            return guides
        # Otherwise, hit the API
        guides = self._fetch_guides_from_api()
        return guides

    def print_guides(self) -> None:
        """
        Fetch and print deduplicated build guide names and URLs.
        """
        guides = self.fetch_guides()
        for guide in guides:
            print(f"{guide.name}: {guide.url}")
        print(f"\nTotal guides found: {len(guides)}")
