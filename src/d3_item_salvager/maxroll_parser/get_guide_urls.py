"""
Module for fetching Diablo 3 build guides from Maxroll's Meilisearch API.
Provides a class-based interface for guide retrieval and future extension.
"""

import json
import logging
from pathlib import Path

import requests
from dotenv import load_dotenv

from .get_guide_cache_utils import (
    load_guides_from_cache,
    save_guides_to_cache,
)
from .types import GuideInfo

load_dotenv()


class MaxrollGuideFetcher:
    """
    Fetches Diablo 3 build guides from Maxroll's Meilisearch API.
    Provides a public method for guide retrieval.
    """

    def __init__(
        self,
        api_url: str = "https://meilisearch-proxy.maxroll.gg/indexes/wp_posts_1/search",
        bearer_token: str | None = None,
        logger: logging.Logger | None = None,
        cache_ttl: int = 604800,  # seconds
        cache_file: str | None = None,
    ) -> None:
        self.api_url = api_url
        self.bearer_token = bearer_token
        self.logger = logger or logging.getLogger(__name__)
        self.cache_ttl = cache_ttl
        # Default cache file location: <project-root>/cache/maxroll_guides.json
        if cache_file is None:
            self.cache_path = Path(Path.cwd(), "cache", "maxroll_guides.json")
        else:
            self.cache_path = Path(cache_file)
        # Load cache on instantiation
        self._cached_guides = load_guides_from_cache(
            self.cache_path, self.cache_ttl, self.logger
        )

    def _fetch_guides_from_api(self, limit: int = 21) -> list[GuideInfo]:
        """
        Fetch guides from Maxroll API.
        """
        headers = {
            "accept": "*/*",
            "authorization": f"Bearer {self.bearer_token}",
            "content-type": "application/json",
        }
        offset = 0
        all_guides: list[GuideInfo] = []
        seen_urls = set()
        try:
            while True:
                body = {"q": "", "facets": [], "limit": limit, "offset": offset}
                resp = requests.post(
                    self.api_url, headers=headers, data=json.dumps(body), timeout=10
                )
                resp.raise_for_status()
                data = resp.json()
                hits = data.get("hits", [])
                if not hits:
                    break
                for hit in hits:
                    url = hit.get("permalink", "")
                    if (
                        url.startswith("https://maxroll.gg/d3/guides/")
                        and url not in seen_urls
                    ):
                        build_slug = url.split("/d3/guides/")[-1].strip("/")
                        name = (
                            build_slug.replace("-", " ")
                            .replace("guide", "Guide")
                            .strip()
                        )
                        name = " ".join(
                            [
                                w.capitalize() if w != "Guide" else w
                                for w in name.split()
                            ]
                        )
                        all_guides.append(GuideInfo(name=name, url=url))
                        seen_urls.add(url)
                if len(hits) < limit:
                    break
                offset += limit
        except requests.RequestException:
            self.logger.exception("Failed to fetch guides from API")
            return []
        self.logger.info("Fetched %d guides from API", len(all_guides))

        if all_guides:
            save_guides_to_cache(all_guides, self.cache_path, self.logger)
        return all_guides

    def fetch_guides(self, limit: int = 21) -> list[GuideInfo]:
        """
        Fetch all Diablo 3 build guides from Maxroll's Meilisearch API with caching.
        """
        if self._cached_guides is not None:
            return self._cached_guides
        guides = self._fetch_guides_from_api(limit=limit)
        return guides

    def print_guides(self, limit: int = 21) -> None:
        """
        Fetch and print deduplicated build guide names and URLs.
        """
        guides = self.fetch_guides(limit=limit)
        for guide in guides:
            print(f"{guide.name}: {guide.url}")
        print(f"\nTotal guides found: {len(guides)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    MaxrollGuideFetcher().print_guides()
