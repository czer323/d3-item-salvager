"""Main AppConfig definition and config loader."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .base import (
    ApiConfig,
    DatabaseConfig,
    LoggingConfig,
    MaxrollParserConfig,
    SchedulerConfig,
)


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
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    maxroll_parser: MaxrollParserConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    model_config = SettingsConfigDict(env_file=".env")
