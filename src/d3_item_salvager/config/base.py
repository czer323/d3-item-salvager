"""Base config dataclasses and shared types."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(str, Enum):
    """Enumerates supported runtime environments."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"


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
        source: Indicates whether to use local files or remote API.
        planner_profile_url: Template URL used to fetch planner profiles.
        planner_request_timeout: Timeout (seconds) for planner HTTP requests.
        planner_user_agent: User agent used when requesting planner resources.
        planner_retry_attempts: Maximum attempts when planner requests fail.
        planner_retry_backoff: Base backoff multiplier applied between retries.
        planner_retry_status_codes: HTTP status codes that trigger retries.
        planner_request_interval: Minimum seconds between planner requests.
        planner_cache_dir: Directory used to persist planner payload cache files.
        planner_cache_ttl: Cache TTL (seconds) before planner payloads are refreshed.
        planner_cache_enabled: Toggle for using the planner payload cache.
    """

    model_config = SettingsConfigDict(
        env_prefix="MAXROLL_",
        env_file=None,
        env_nested_delimiter="__",
    )

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
    planner_profile_url: str = Field(
        default="https://planners.maxroll.gg/profiles/load/d3/{planner_id}",
        description="Template URL for loading planner profiles (must contain {planner_id}).",
    )
    planner_request_timeout: float = Field(
        default=10.0,
        description="Timeout in seconds applied to planner HTTP requests.",
    )
    planner_user_agent: str = Field(
        default="d3-item-salvager/1.0 (+https://github.com/czer323/d3-item-salvager)",
        description="User agent string supplied when calling Maxroll planner endpoints.",
    )
    planner_retry_attempts: int = Field(
        default=4,
        description="Maximum number of attempts for planner profile requests.",
        ge=1,
    )
    planner_retry_backoff: float = Field(
        default=1.5,
        description="Base multiplier used when calculating exponential backoff.",
        gt=1.0,
    )
    planner_retry_status_codes: tuple[int, ...] = Field(
        default=(429, 502, 503, 504),
        description="HTTP status codes that should be retried when fetching planners.",
    )
    planner_request_interval: float = Field(
        default=0.4,
        description="Minimum interval (seconds) enforced between planner requests.",
        ge=0.0,
    )
    planner_cache_dir: Path = Field(
        default=Path("cache/planner_profiles"),
        description="Directory path used to persist planner payload cache files.",
    )
    planner_cache_ttl: int = Field(
        default=86400,
        description="Planner cache time-to-live in seconds.",
        ge=0,
    )
    planner_cache_enabled: bool = Field(
        default=True,
        description="Enable cached planner payload reuse between runs.",
    )
    source: str = Field(
        default="remote", description="Data source mode: 'local' or 'remote'."
    )

    @model_validator(mode="after")
    def validate_bearer_token(self) -> MaxrollParserConfig:
        """Validates that a non-default bearer_token is set for production use.

        Raises:
            ValueError: If bearer_token is missing or set to the default 'fake-dummy-token'.

        Returns:
            MaxrollParserConfig: The validated configuration instance.
        """
        import os
        import warnings

        source_mode = self.source.lower()
        env_value = os.getenv("APP_ENV", AppEnvironment.DEVELOPMENT.value).lower()
        try:
            env = AppEnvironment(env_value)
        except ValueError:
            env = AppEnvironment.DEVELOPMENT

        if source_mode == "remote":
            if not self.bearer_token or self.bearer_token == "fake-dummy-token":
                msg = (
                    "Configuration validation failed: MAXROLL_BEARER_TOKEN is required"
                    " for remote Maxroll access. Provide a valid bearer token."
                )
                if env is AppEnvironment.PRODUCTION:
                    raise ValueError(msg)
                warnings.warn(msg)
        else:
            local_paths = [self.data_paths, self.api_url]
            for path_value in local_paths:
                path = Path(path_value)
                if not path.exists():
                    warnings.warn(
                        f"Local Maxroll source path does not exist: {path_value}"
                    )
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
    def validate_timezone(self) -> SchedulerConfig:
        """Validate that configured timezone is recognised by the system."""
        try:
            ZoneInfo(self.timezone)
        except (
            ZoneInfoNotFoundError
        ) as exc:  # pragma: no cover - depends on host TZ data
            msg = f"Unknown timezone configured for scheduler: {self.timezone}"
            raise ValueError(msg) from exc
        return self
