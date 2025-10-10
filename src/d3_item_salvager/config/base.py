"""Base config dataclasses and shared types."""

from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """Database configuration settings.

    Attributes:
        url: Database connection URL.
    """

    model_config = SettingsConfigDict(env_prefix="DATABASE_")
    # Production defaults
    url: str = "sqlite:///d3_items.db"


class LoggingConfig(BaseSettings):
    """Logging configuration for Loguru and observability hooks.

    Attributes:
        enabled: Whether logging is enabled.
        level: Logging level (e.g., 'INFO', 'DEBUG').
        metrics_enabled: Whether metrics are enabled.
        log_file: Path to the log file.
    """

    model_config = SettingsConfigDict(env_prefix="LOGGING_")
    enabled: bool = True
    level: str = "INFO"
    metrics_enabled: bool = False
    log_file: str = "logs/app.log"


class MaxrollParserConfig(BaseSettings):
    """Configuration for Maxroll parser data sources and API access.

    Attributes:
        bearer_token: Bearer token for Maxroll API.
        data_paths: Path or URL to data.json.
        build_paths: Path or URL to build object JSON.
        guide_paths: Path or URL to guide search endpoint.
        api_url: API URL for Meilisearch.
        cache_ttl: Cache time-to-live in seconds.
        cache_file: Path to cache file.
        limit: API result limit per request.
    """

    model_config = SettingsConfigDict(env_prefix="MAXROLL_", env_file=None)

    bearer_token: str = Field(
        "fake-dummy-token",
        description=(
            "Bearer token for Maxroll API (default is dummy; must be set via env for production)"
        ),
    )
    data_paths: str = "https://assets-ng.maxroll.gg/d3planner/data.json"
    build_paths: str = "https://assets-ng.maxroll.gg/d3planner/profile_object.json"
    guide_paths: str = "https://meilisearch-proxy.maxroll.gg/indexes/wp_posts_1/search"
    api_url: str = "https://meilisearch-proxy.maxroll.gg/indexes/wp_posts_1/search"
    cache_ttl: int = 604800  # seconds
    cache_file: Path = Path("cache/maxroll_guides.json")
    limit: int = 21

    @model_validator(mode="after")
    def validate_bearer_token(self) -> "MaxrollParserConfig":
        """Validates that a non-default bearer_token is set for production use.

        Raises:
            ValueError: If bearer_token is missing or set to the default 'fake-dummy-token'.

        Returns:
            MaxrollParserConfig: The validated configuration instance.
        """
        if not self.bearer_token or self.bearer_token == "fake-dummy-token":
            msg = (
                "Configuration validation failed:"
                "MAXROLL_BEARER_TOKEN is required for production use. "
                "\nDefault 'fake-dummy-token' will not work."
            )
            raise ValueError(msg)
        return self


class ApiConfig(BaseSettings):
    """Configuration for FastAPI/Uvicorn server.

    Attributes:
        host: Host address to bind the server.
        port: Port to bind the server.
        reload: Enable auto-reload for development.
    """

    model_config = SettingsConfigDict(env_prefix="API_")
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False


class SchedulerConfig(BaseSettings):
    """Configuration for the APScheduler-based workers module."""

    model_config = SettingsConfigDict(env_prefix="SCHEDULER_")

    enabled: bool = True
    job_store_path: Path = Path("cache/scheduler.sqlite")
    timezone: str = "UTC"
    max_workers: int = 5
    misfire_grace_seconds: int = 300
    shutdown_timeout_seconds: int = 30

    scrape_guides_enabled: bool = True
    scrape_guides_interval_minutes: int = 360

    refresh_cache_enabled: bool = True
    refresh_cache_interval_minutes: int = 1440

    cleanup_logs_enabled: bool = True
    cleanup_logs_interval_minutes: int = 1440
    cleanup_logs_max_age_days: int = 7

    @model_validator(mode="after")
    def validate_timezone(self) -> "SchedulerConfig":
        """Validate that configured timezone is recognised by the system."""
        try:
            ZoneInfo(self.timezone)
        except (
            ZoneInfoNotFoundError
        ) as exc:  # pragma: no cover - depends on host TZ data
            msg = f"Unknown timezone configured for scheduler: {self.timezone}"
            raise ValueError(msg) from exc
        return self
