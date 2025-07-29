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
                    maxroll_parser=MaxrollParserConfig(),
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
    return _ConfigSingleton.get()


def reset_config() -> None:
    """Reset the config singleton (for testing)."""
    _ConfigSingleton.reset()
