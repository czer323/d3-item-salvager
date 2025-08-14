# Diablo 3 Item Salvager - Config Module

## Config Overview

This module is responsible for managing the application's configuration. It uses `pydantic-settings` to load configuration from environment variables and `.env` files.

### Configuration Structure

The configuration is split into multiple dataclasses, each representing a specific part of the application. The main configuration class is `AppConfig` in `src/d3_item_salvager/config/settings.py`, which aggregates all other configuration classes.

The following configuration classes are defined in `src/d3_item_salvager/config/base.py`:

- `DatabaseConfig`: Configuration for the database connection.
- `LoggingConfig`: Configuration for the logging setup.
- `MaxrollParserConfig`: Configuration for the Maxroll parser.
- `ApiConfig`: Configuration for the FastAPI/Uvicorn server.

### Loading Configuration

The configuration is loaded when `AppConfig` is instantiated. It automatically loads settings from environment variables and a `.env` file. The environment variables have a higher priority than the values in the `.env` file.

Each configuration class has a specific `env_prefix` that is used to match environment variables. For example, to set the database URL, you would use the environment variable `DATABASE_URL`.

### Usage

The `AppConfig` instance is provided through dependency injection in the API module. You can also instantiate it directly:

```python
from d3_item_salvager.config.settings import AppConfig

config = AppConfig()
print(config.app_name)
```

## Discrepancies

- The `MaxrollParserConfig` has a validator that checks for a non-default `bearer_token`. This is good for production, but it can be inconvenient for local development or testing. It might be better to allow the default token in a "development" environment.
- The `env_file` is hardcoded to `.env` in `AppConfig`. It would be more flexible to allow the environment file to be specified through an environment variable.
- The default `bearer_token` in `MaxrollParserConfig` is `'fake-dummy-token'`. This is a bit misleading as it will fail validation. It should be an optional type or have a more explicit "development" mode.
