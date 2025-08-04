"""Utility functions for caching guides from Maxroll."""

import json
import time

from loguru import logger

from d3_item_salvager.config.settings import AppConfig

from .types import GuideInfo


def load_guides_from_cache(config: AppConfig) -> list[GuideInfo] | None:
    """
    Load guides from cache file if fresh, using cache TTL and cache path from AppConfig.

    Args:
        config: AppConfig instance containing cache settings.

    Returns:
        list[GuideInfo] | None: List of GuideInfo objects if cache is fresh, else None.

    Raises:
        OSError: If there is an error accessing the cache file.
        json.JSONDecodeError: If the cache file is not valid JSON.
    """
    cache_path = config.maxroll_parser.cache_file
    cache_ttl = config.maxroll_parser.cache_ttl
    now = time.time()
    if cache_path is not None and cache_path.exists():
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


def save_guides_to_cache(
    guides: list[GuideInfo],
    config: AppConfig,
) -> None:
    """
    Save guides to cache file using config.maxroll_parser.cache_file (Path).

    Args:
        guides: List of GuideInfo objects to save.
        config: AppConfig instance containing cache settings.

    Returns:
        None

    Raises:
        OSError: If there is an error writing to the cache file.
        TypeError: If guides cannot be serialized.
        ValueError: If there is a value error during serialization.
    """
    cache_path = config.maxroll_parser.cache_file
    if cache_path is not None:
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with cache_path.open("w", encoding="utf-8") as f:
                json_str = json.dumps(
                    {"guides": [g.__dict__ for g in guides]}, indent=2
                )
                f.write(json_str)
                f.write("\n")
            logger.info("Saved %d guides to file cache", len(guides))
        except (OSError, TypeError, ValueError) as e:
            logger.warning("Failed to save cache file: %s", e)
    else:
        logger.warning("Cache path is None, cannot save guides to cache.")
