# Diablo 3 Item Salvager – Logging & Observability

## Logging Overview

This project uses [Loguru](https://github.com/Delgan/loguru) for unified, structured logging across all modules. Logging configuration is managed via the `LoggingConfig` dataclass in `src/d3_item_salvager/config/base.py` and integrated into the main `AppConfig`.

### Logger Setup

Logger initialization is handled by `setup_logger()` in `src/d3_item_salvager/logging/setup.py`. This function configures log sinks, levels, rotation, retention, and optional metrics/tracing hooks based on config values.

**Example:**

```python
from d3_item_salvager.logging.setup import setup_logger
setup_logger()
```

### Logging Decorators

- **Timing Decorator:**

  ```python
  from d3_item_salvager.logging.setup import log_timing

  @log_timing
  def my_function():
      ...
  ```

- **Contextual Decorator:**

  ```python
  from d3_item_salvager.logging.setup import log_contextual

  @log_contextual({"user_id": "abc123"})
  def my_function():
      ...
  ```

- **Error Capture:** Use Loguru's `@logger.catch` directly on functions.

### API Logging Middleware

Use `log_api_request(request, response)` from `src/d3_item_salvager/logging/middleware.py` to log structured request/response details in API endpoints.

### Configuration Example

```python
from d3_item_salvager.config.base import LoggingConfig
config = LoggingConfig(enabled=True, level="INFO", metrics_enabled=False, log_file="logs/app.log")
```

### SQLAlchemy noise control

To reduce visual noise from SQLAlchemy during import and other bulk operations, set `sqlalchemy_echo` to `False` (the default) in your `LoggingConfig`. You can override via environment using `LOGGING_SQLALCHEMY_ECHO=true` in your `.env` when you need SQL emission for debugging.

## Metrics & Tracing

Optional metrics/tracing integration is available via Prometheus and OpenTelemetry. Enable via config and ensure dependencies are installed.

## Testing

Unit tests for logger setup and decorators are in `tests/logging/test_setup.py`.

---
For more details, see code docstrings in `src/d3_item_salvager/logging/setup.py` and `middleware.py`.
