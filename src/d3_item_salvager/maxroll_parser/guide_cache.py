"""Guide cache abstraction for Maxroll guide metadata.

Implements a protocol-driven design to allow injection of alternative cache strategies.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, is_dataclass
from typing import TYPE_CHECKING, Any

from loguru import logger

from .protocols import GuideCacheProtocol
from .types import GuideInfo

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Iterable
    from pathlib import Path

    from d3_item_salvager.config.settings import AppConfig


class FileGuideCache(GuideCacheProtocol):
    """
    File-based guide cache with TTL semantics.

    Args:
        config: AppConfig whose maxroll_parser group supplies cache_file and cache_ttl.
            The values are captured at construction;
            callers should re-instantiate if configuration changes.
    """

    def __init__(self, config: AppConfig) -> None:
        self._cache_path: Path | None = config.maxroll_parser.cache_file
        self._ttl: int = int(config.maxroll_parser.cache_ttl)

    # Public API ---------------------------------------------------------
    def load(self) -> list[GuideInfo] | None:
        """
        Loads cached guides if present and fresh, else returns None.

        Returns:
            List of GuideInfo if cache is present and fresh, else None.
        """
        if self._cache_path is None or not self._cache_path.exists():
            return None
        try:
            cache_stat = self._cache_path.stat()
            cache_age = time.time() - cache_stat.st_mtime
            if cache_age >= self._ttl:
                return None
            with self._cache_path.open("r", encoding="utf-8") as f:
                cache_data = json.load(f)
            guides = [
                GuideInfo(name=g["name"], url=g["url"])  # minimal validation
                for g in cache_data.get("guides", [])
                if isinstance(g, dict) and "name" in g and "url" in g
            ]
        except (OSError, json.JSONDecodeError) as e:  # pragma: no cover - IO edge
            logger.warning("Failed to load cache file: %s", e)
            return None
        logger.info(
            "Loaded %d guides from file cache (%d seconds old)",
            len(guides),
            int(cache_age),
        )
        return guides

    def save(self, guides: Iterable[GuideInfo]) -> None:
        """
        Persists guides to cache file (best-effort).

        Args:
            guides: Iterable of GuideInfo objects to persist.
        """
        if self._cache_path is None:
            logger.warning("Cache path is None, cannot save guides to cache.")
            return
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            serialisable_guides: list[dict[str, Any]] = []
            for g in guides:
                if is_dataclass(g):  # supports slotted / frozen dataclasses
                    serialisable_guides.append(asdict(g))
                else:  # fallback best-effort
                    serialisable_guides.append(
                        {"name": getattr(g, "name", ""), "url": getattr(g, "url", "")}
                    )
            serialisable = {"guides": serialisable_guides}
            with self._cache_path.open("w", encoding="utf-8") as f:
                json.dump(serialisable, f, indent=2)
                f.write("\n")
            logger.info("Saved %d guides to file cache", len(serialisable["guides"]))
        except (OSError, TypeError, ValueError) as e:  # pragma: no cover
            logger.warning("Failed to save cache file: %s", e)


__all__ = ["FileGuideCache", "GuideInfo"]
