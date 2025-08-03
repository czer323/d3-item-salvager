"""Main AppConfig definition and config loader."""

from pydantic import ValidationError
from pydantic_settings import BaseSettings

from .base import DatabaseConfig, LoggingConfig, MaxrollParserConfig


class AppConfig(BaseSettings):
    """Main application configuration.

    Args:
        database: Database configuration
        maxroll_parser: MaxrollParserConfig
        logging: LoggingConfig
    """

    database: DatabaseConfig
    maxroll_parser: MaxrollParserConfig
    logging: LoggingConfig

    # pylint: disable=too-few-public-methods
    class ConfigDict:
        """Pydantic settings configuration."""

        env_file = ".env"


class _ConfigSingleton:
    """Singleton holder for AppConfig."""

    _instance: AppConfig | None = None

    @classmethod
    def get(cls) -> AppConfig:
        """Get the singleton instance of AppConfig."""
        if cls._instance is None:
            try:
                cls._instance = AppConfig(
                    database=DatabaseConfig(),
                    maxroll_parser=MaxrollParserConfig(),  # pyright: ignore[reportCallIssue]
                    logging=LoggingConfig(),
                )
            except ValidationError as e:
                msg = f"Configuration validation failed: {e}"
                raise RuntimeError(msg) from e
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (for testing purposes)."""
        cls._instance = None


def get_config() -> AppConfig:
    """Singleton accessor for application config."""
    config = _ConfigSingleton.get()
    # Runtime validation for required secrets
    if not config.maxroll_parser.bearer_token:
        msg = (
            "Configuration validation failed: MAXROLL_BEARER_TOKEN is required "
            "but not set in environment or .env file"
        )
        raise RuntimeError(msg)
    return config


def reset_config() -> None:
    """Reset the config singleton (for testing)."""
    _ConfigSingleton.reset()
