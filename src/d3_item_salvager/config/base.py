"""Base config dataclasses and shared types."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    model_config = {"env_prefix": "DATABASE_"}
    # Production defaults
    url: str = "sqlite:///d3_items.db"


class LoggingConfig(BaseSettings):
    """Logging configuration for Loguru and observability hooks."""

    enabled: bool = True
    level: str = "INFO"
    metrics_enabled: bool = False
    log_file: str = "logs/app.log"


class MaxrollParserConfig(BaseSettings):
    """
    Data source configuration for switching between environments.

    Args:
        mode: Environment mode ('dev', 'prod', etc.).
        data_paths: Mapping of mode to data.json path or URL.
        build_paths: Mapping of mode to build object path or URL.
    """

    model_config = {"env_prefix": "MAXROLL_"}

    bearer_token: str | None = Field(None, description="Bearer token for Maxroll API")
    data_paths: str = "https://assets-ng.maxroll.gg/d3planner/data.json"
    build_paths: str = "https://assets-ng.maxroll.gg/d3planner/profile_object.json"
    guide_paths: str = "https://meilisearch-proxy.maxroll.gg/indexes/wp_posts_1/search"
    api_url: str = "https://meilisearch-proxy.maxroll.gg/indexes/wp_posts_1/search"
    cache_ttl: int = 604800  # seconds
    cache_file: Path = Path("cache/maxroll_guides.json")
    limit: int = 21
