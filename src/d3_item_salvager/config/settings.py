"""Main AppConfig definition and config loader."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .base import DatabaseConfig, LoggingConfig, MaxrollParserConfig


class AppConfig(BaseSettings):
    """
    Main application configuration.

    Attributes:
        database: Database configuration.
        maxroll_parser: MaxrollParserConfig instance.
        logging: LoggingConfig instance.
    """

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    maxroll_parser: MaxrollParserConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    model_config = SettingsConfigDict(env_file=".env")
