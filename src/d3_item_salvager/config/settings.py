"""Main AppConfig definition and config loader."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv
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

DEFAULT_DOTENV_PATH: Final[Path] = Path(".env")


def load_runtime_env(
    dotenv_path: str | Path | None = None,
    *,
    override: bool = False,
) -> bool:
    """Load environment variables from a ``.env`` file if present.

    Args:
        dotenv_path: Optional path to the dotenv file (defaults to ``.env``).
        override: When True, existing environment variables are overridden.

    Returns:
        True if the dotenv file was loaded, otherwise False.
    """
    path = Path(dotenv_path) if dotenv_path is not None else DEFAULT_DOTENV_PATH
    if not path.exists():
        return False
    load_dotenv(path, override=override)
    return True


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
    model_config = SettingsConfigDict(
        env_file=None,
        env_nested_delimiter="__",
        extra="ignore",
    )

    @property
    def is_development(self) -> bool:
        """Return True when running in development mode."""
        return self.environment is AppEnvironment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Return True when running in production mode."""
        return self.environment is AppEnvironment.PRODUCTION
