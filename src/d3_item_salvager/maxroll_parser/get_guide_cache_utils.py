"""Utility functions for caching guides from Maxroll."""

import json
import time
from pathlib import Path

from loguru import logger

from .types import GuideInfo


def load_guides_from_cache(cache_path: Path, cache_ttl: int) -> list[GuideInfo] | None:
    """
    Load guides from cache file if fresh.
    """
    now = time.time()
    if cache_path.exists():
        try:
            cache_stat = cache_path.stat()
            cache_age = now - cache_stat.st_mtime
            if cache_age < cache_ttl:
                with cache_path.open("r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                guides = [
                    GuideInfo(name=g["name"], url=g["url"])
                    for g in cache_data.get("guides", [])
                    if "name" in g and "url" in g
                ]
                logger.info(
                    "Loaded %d guides from file cache (%d seconds old)",
                    len(guides),
                    int(cache_age),
                )
                return guides
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Failed to load cache file: %s", e)
    return None


def save_guides_to_cache(guides: list[GuideInfo], cache_path: Path) -> None:
    """
    Save guides to cache file.
    """
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open("w", encoding="utf-8") as f:
            json_str = json.dumps({"guides": [g.__dict__ for g in guides]}, indent=2)
            f.write(json_str)
            f.write("\n")
        logger.info("Saved %d guides to file cache", len(guides))
    except (OSError, TypeError, ValueError) as e:
        logger.warning("Failed to save cache file: %s", e)
