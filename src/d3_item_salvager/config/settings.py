"""Main AppConfig definition and config loader."""

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings

from .base import DatabaseConfig, LoggingConfig, MaxrollParserConfig


class AppConfig(BaseSettings):
    """
    Main application configuration.

    Attributes:
        database: Database configuration.
        maxroll_parser: MaxrollParserConfig instance.
        logging: LoggingConfig instance.
    """

    database: DatabaseConfig = Field(default_factory=lambda: DatabaseConfig())
    maxroll_parser: MaxrollParserConfig = Field(
        default_factory=lambda: MaxrollParserConfig()
    )
    logging: LoggingConfig = Field(default_factory=lambda: LoggingConfig())

    # pylint: disable=too-few-public-methods
    class ConfigDict:
        """Pydantic settings configuration."""

        env_file = ".env"

    @model_validator(mode="after")
    def validate_bearer_token(self) -> "AppConfig":
        """Validate that the bearer token is set."""
        if not self.maxroll_parser.bearer_token:
            msg = (
                "Configuration validation failed: MAXROLL_BEARER_TOKEN is required "
                "but not set in environment or .env file"
            )
            raise ValueError(msg)
        return self
