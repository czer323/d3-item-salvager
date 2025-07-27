# Configuration Management Module – Implementation Plan

## Domain & Purpose

Centralizes all configuration for the project (API, DB, scraping, web UI, environment variables, CLI args). Ensures immutability, type safety, and environment-specific overrides. All modules must consume configuration via dependency injection, never global variables.

## Directory Structure

```directory
src/d3_item_salvager/config/
    __init__.py
    base.py           # Base config dataclasses
    env.py            # Env var loading logic
    cli.py            # CLI arg parsing (if needed)
    settings.py       # Project-wide settings object
```

## Tools & Libraries

- `pydantic` (for type-safe config models)
- `os` (env vars)
- `argparse` (CLI args, optional)
- `dotenv` (optional, for .env files)

## Design Patterns

- Immutable dataclasses for config (`@dataclass(frozen=True)` or Pydantic `BaseSettings`)
- Factory pattern for loading config from multiple sources
- Dependency injection: pass config objects to all modules/services

## Key Classes & Functions

- `BaseConfig`: Abstract base for all config objects (optional, use Pydantic `BaseSettings` for each config section)
- `DatabaseConfig`: Database config class with sensible defaults and `env_prefix` for environment variable mapping
- `ScraperConfig`: Scraper config class with sensible defaults and `env_prefix` for environment variable mapping
- `AppConfig`: Main config object, aggregates all sub-configs
- `get_config()`: Singleton accessor for config
- `reset_config()`: Helper to reset the config singleton for test isolation

## Implementation Details

- All config fields must be documented with Google-style docstrings
- Each config class must set `model_config = {"env_prefix": ...}` to enable environment variable overrides (e.g., `DATABASE_URL`, `SCRAPER_USER_AGENT`)
- Support overrides for dev/test/prod via environment variables and `.env` file (automatically loaded by Pydantic Settings)
- Validate config at startup and fail fast on errors
- Never use global variables for config; always inject via `get_config()`
- Provide `reset_config()` for test isolation and flexibility
- Example usage:

  ```python
  from d3_item_salvager.config import get_config
  config = get_config()
  db_url = config.database.url
  ```

- If CLI config is needed, use `argparse` and merge with env/.env config (integration planned, not yet implemented)

## Testing & Extensibility

- Unit tests for config loading, environment variable overrides, and validation
- Use `reset_config()` in tests to ensure fresh config loading after environment changes
- Add new config sections by creating new Pydantic `BaseSettings` classes and updating `AppConfig`
- Document all config changes in this file and in code docstrings

## Example Pydantic Config

```python
from pydantic_settings import BaseSettings

class DatabaseConfig(BaseSettings):
    """Database configuration.

    Args:
        url: Database connection string (e.g., sqlite:///d3_items.db)
        pool_size: Number of connections in the pool
    """
    model_config = {"env_prefix": "DATABASE_"}
    url: str = "sqlite:///d3_items.db"
    pool_size: int = 5

class ScraperConfig(BaseSettings):
    """Scraper configuration.

    Args:
        user_agent: HTTP User-Agent string for requests
        timeout: Request timeout in seconds
    """
    model_config = {"env_prefix": "SCRAPER_"}
    user_agent: str = "Mozilla/5.0"
    timeout: int = 10

class AppConfig(BaseSettings):
    """Main application configuration.

    Args:
        database: Database configuration
        scraper: Scraper configuration
    """
    database: DatabaseConfig
    scraper: ScraperConfig
```

## Summary

This module provides a robust, type-safe, and extensible configuration system for the entire project. All modules must use dependency injection for config, and all config fields must be documented and validated. Environment variable overrides are supported via `env_prefix` in each config class. The config singleton can be reset for test isolation. CLI integration is planned. This ensures maintainability, testability, and environment flexibility.
