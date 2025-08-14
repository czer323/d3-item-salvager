"""
Shared test config helpers for Maxroll tests.
"""

from pathlib import Path

from d3_item_salvager.config.base import (
    DatabaseConfig,
    LoggingConfig,
    MaxrollParserConfig,
)
from d3_item_salvager.config.settings import AppConfig


def make_test_app_config(tmp_path: Path) -> AppConfig:
    """Create an AppConfig instance for testing with a temporary cache file."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(exist_ok=True)
    cache_path = cache_dir / "maxroll_guides.json"
    return AppConfig(
        database=DatabaseConfig(),
        logging=LoggingConfig(),
        maxroll_parser=MaxrollParserConfig(
            api_url="https://dummy-url",
            bearer_token="dummy-token",
            cache_file=cache_path,
        ),
    )
