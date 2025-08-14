"""Guide fetching and caching for Diablo 3 build guides from Maxroll.

Implements GuideFetcherProtocol semantics, supports dependency-injected cache,
and provides force_refresh to bypass cache. Network and parsing failures are
mapped to GuideFetchError for precise error handling.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import requests
from loguru import logger

from .guide_cache import FileGuideCache
from .maxroll_exceptions import GuideFetchError
from .protocols import GuideCacheProtocol, GuideFetcherProtocol
from .types import GuideInfo

if TYPE_CHECKING:  # pragma: no cover - typing only
    from d3_item_salvager.config.settings import AppConfig


__all__ = ["GuideInfo", "MaxrollGuideFetcher"]


class MaxrollGuideFetcher(
    GuideFetcherProtocol
):  # pragma: no cover - behaviour tested via unit tests
    """
    Fetches, normalizes, and caches Diablo 3 build guides from Maxroll.

    Args:
        config: Application configuration supplying API URL, bearer token, limits,
            and cache settings.
        cache: Optional injected cache implementing GuideCacheProtocol.
            If not supplied, a FileGuideCache is created.
    """

    def __init__(
        self,
        config: AppConfig,
        *,
        cache: GuideCacheProtocol | None = None,
    ) -> None:
        self.config = config
        self._cache: GuideCacheProtocol = cache or FileGuideCache(config)
        mp_cfg = config.maxroll_parser
        self._api_url: str = mp_cfg.api_url
        self._bearer_token: str = mp_cfg.bearer_token
        self._limit: int = int(mp_cfg.limit)

    def get_guide_by_id(self, guide_id: str) -> GuideInfo | None:
        """Fetch a single guide by its unique ID. Returns None if not found."""
        guides = self.fetch_guides()
        for guide in guides:
            if getattr(guide, "id", None) == guide_id:
                return guide
        return None

    # ------------------------------------------------------------------
    def fetch_guides(
        self,
        search: str | None = None,
        *,
        force_refresh: bool = False,
    ) -> list[GuideInfo]:
        """
        Fetches a list of guides, optionally filtering by a search substring.

        Args:
            search: Optional substring to filter guides by name or URL.
            force_refresh: If True, bypasses cache and fetches fresh data.

        Returns:
            List of GuideInfo objects representing build guides.

        Raises:
            GuideFetchError: If network or HTTP issues occur during fetch.
        """
        guides: list[GuideInfo] | None = None
        if not force_refresh:
            try:
                guides = self._cache.load()
            except (
                ValueError,
                TypeError,
                KeyError,
            ) as e:  # pragma: no cover - defensive (cache impl bug)
                logger.warning("Guide cache load failed: %s", e)
        if guides is None:  # need fresh data
            hits = (
                self._fetch_from_file(self._api_url)
                if self._is_local_file(self._api_url)
                else self._fetch_from_api(
                    self._api_url, self._bearer_token, self._limit
                )
            )
            guides = self._extract_guide_links_from_hits(hits)
            # best-effort save
            try:
                self._cache.save(guides)
            except (
                ValueError,
                TypeError,
                KeyError,
            ) as e:  # pragma: no cover - defensive
                logger.warning("Guide cache save failed: %s", e)

        if search:
            s = search.lower()
            guides = [g for g in guides if s in g.name.lower() or s in g.url.lower()]
        return guides

    # Helpers -----------------------------------------------------------
    @staticmethod
    def _is_local_file(url: str) -> bool:
        return Path(url).exists()

    def _fetch_from_file(self, file_path: str) -> list[dict[str, Any]]:
        """
        Loads guide data from a local file.

        Args:
            file_path: Path to the local guide file.

        Returns:
            List of guide hit dictionaries.

        Raises:
            GuideFetchError: If the file cannot be loaded or parsed.
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            raw_hits = data.get("hits", [])
            if not isinstance(raw_hits, list):
                return []
            return [h for h in raw_hits if isinstance(h, dict)]
        except Exception as e:
            msg = f"Failed to load local guide file: {e}"
            raise GuideFetchError(msg) from e

    def _fetch_from_api(
        self, api_url: str, bearer_token: str, limit: int
    ) -> list[dict[str, Any]]:
        """
        Fetches guide data from the Maxroll API.

        Args:
            api_url: API endpoint URL.
            bearer_token: Bearer token for authentication.
            limit: Maximum number of results per request.

        Returns:
            List of guide hit dictionaries.

        Raises:
            GuideFetchError: If the API request fails or response is malformed.
        """
        headers = {
            "accept": "*/*",
            "authorization": f"Bearer {bearer_token}",
            "content-type": "application/json",
        }
        offset = 0
        all_hits: list[dict[str, Any]] = []
        while True:
            body = {"q": "", "facets": [], "limit": limit, "offset": offset}
            try:
                resp = requests.post(
                    api_url, headers=headers, data=json.dumps(body), timeout=10
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                msg = f"API fetch failed: {e}"
                raise GuideFetchError(msg) from e
            hits = data.get("hits", [])
            if not hits:
                break
            if not isinstance(hits, list):
                msg = "API response 'hits' must be a list"
                raise GuideFetchError(msg)
            all_hits.extend(h for h in hits if isinstance(h, dict))
            if len(hits) < limit:
                break
            offset += limit
        return all_hits

    def _extract_guide_links_from_hits(
        self, hits: list[dict[str, Any]]
    ) -> list[GuideInfo]:
        """
        Extracts guide links from API or file hits.

        Args:
            hits: List of hit dictionaries from API or file.

        Returns:
            List of GuideInfo objects with name and URL.
        """
        guides: list[GuideInfo] = []
        seen_urls: set[str] = set()
        for hit in hits:
            url = str(hit.get("permalink", ""))
            if url.startswith("https://maxroll.gg/d3/guides/") and url not in seen_urls:
                build_slug = url.rsplit("/d3/guides/", maxsplit=1)[-1].strip("/")
                name = build_slug.replace("-", " ").replace("guide", "Guide").strip()
                name = " ".join(
                    w.capitalize() if w != "Guide" else w for w in name.split()
                )
                guides.append(GuideInfo(name=name, url=url))
                seen_urls.add(url)
        return guides

    # Convenience -------------------------------------------------------
    def print_guides(self) -> None:  # pragma: no cover - thin wrapper
        """Prints all fetched guides in a simple format."""
        for guide in self.fetch_guides():
            print(f"{guide.name}: {guide.url}")
