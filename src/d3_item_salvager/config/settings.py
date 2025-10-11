"""Main AppConfig definition and config loader."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .base import (
    ApiConfig,
    AppEnvironment,
    DatabaseConfig,
    LoggingConfig,
    MaxrollParserConfig,
    SchedulerConfig,
)


def _default_maxroll_parser_config() -> MaxrollParserConfig:
    """Build a MaxrollParserConfig tailored to the current environment."""
    env_value = os.getenv("APP_ENV", AppEnvironment.DEVELOPMENT.value).lower()
    try:
        environment = AppEnvironment(env_value)
    except ValueError:
        environment = AppEnvironment.DEVELOPMENT

    if environment is AppEnvironment.DEVELOPMENT:
        reference_dir = Path(__file__).resolve().parents[3] / "reference"
        return MaxrollParserConfig(
            source="local",
            bearer_token="",
            data_paths=str(reference_dir / "data.json"),
            build_paths=str(reference_dir / "profile_object_298017784.json"),
            guide_paths=str(reference_dir / "guides_list.json"),
            api_url=str(reference_dir / "guides_list.json"),
        )

    bearer = os.getenv("MAXROLL_PARSER__BEARER_TOKEN", "fake-dummy-token")
    return MaxrollParserConfig(bearer_token=bearer, source="remote")


class AppConfig(BaseSettings):
    """
    Main application configuration.

    Attributes:
        app_name: Application name.
        database: Database configuration.
        maxroll_parser: MaxrollParserConfig instance.
        logging: LoggingConfig instance.
    """

    app_name: str = "D3 Item Salvager"
    environment: AppEnvironment = Field(
        default=AppEnvironment.DEVELOPMENT,
        validation_alias=AliasChoices("APP_ENV", "app_env"),
        description="Runtime environment (development or production).",
    )
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    maxroll_parser: MaxrollParserConfig = Field(
        default_factory=_default_maxroll_parser_config
    )
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    model_config = SettingsConfigDict(env_file=".env")

    @property
    def is_development(self) -> bool:
        """Return True when running in development mode."""
        return self.environment is AppEnvironment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Return True when running in production mode."""
        return self.environment is AppEnvironment.PRODUCTION
