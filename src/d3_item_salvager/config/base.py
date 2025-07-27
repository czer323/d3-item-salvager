"""Base config dataclasses and shared types."""

from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    model_config = {"env_prefix": "DATABASE_"}
    """Database configuration.

    Args:
        url: Database connection string (e.g., sqlite:///d3_items.db)
        pool_size: Number of connections in the pool
    """

    url: str = "sqlite:///d3_items.db"
    pool_size: int = 5


class ScraperConfig(BaseSettings):
    model_config = {"env_prefix": "SCRAPER_"}
    """Scraper configuration.

    Args:
        user_agent: HTTP User-Agent string for requests
        timeout: Request timeout in seconds
    """

    user_agent: str = "Mozilla/5.0"
    timeout: int = 10
