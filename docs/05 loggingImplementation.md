# Logging and Observability Module – Implementation Plan (v2)

## 1. Domain & Purpose

This module provides unified, structured logging and observability hooks (metrics, tracing, error reporting) for all project modules. The goal is to ensure logs are consistent, actionable, and extensible, with easy integration for external monitoring if needed.

## 2. Directory Structure

```directory
src/d3_item_salvager/logging/
    __init__.py
    setup.py          # Logger setup/config
    middleware.py     # API logging middleware
    metrics.py        # Metrics/tracing hooks (optional)
```

## 3. Design Patterns

- **Global logger instance**: `from loguru import logger`
- **Structured logging**: Use Loguru format strings, custom sinks (JSON, key-value), and decorators
- **Contextual logging**: `logger.bind()` for per-request or per-task context
- **File sinks**: Rotation, retention, and compression for persistent log collection
- **Decorators/context managers**: For timing, error capture, and contextual logging

## 4. Logging Configuration Requirements

- Define a dedicated `LoggingConfig` class in `base.py`:
  - `enabled: bool = True`
  - `level: str = "INFO"`
  - `metrics_enabled: bool = False`
  - `log_file: str = "logs/app.log"`
- `AppConfig` in `settings.py` must include a `logging: LoggingConfig` field.
- Logger setup must use `get_config().logging` to read these options and apply them when initializing Loguru sinks.
- All logging, verbosity, and metrics/tracing features are controlled via config for easy enable/disable and adjustment.

## 5. Logger Setup Example

This is the canonical logger setup pattern for Loguru. Reference this example for all logger setup throughout the project.

```python
from loguru import logger
from d3_item_salvager.config import get_config
import sys

def setup_logger():
    """Configure Loguru logger for the project."""
    config = get_config().logging
    logger.remove()
    logger.add(sys.stderr, format="<green>{time}</green> | <level>{message}</level>", colorize=True)
    if config.enabled:
        logger.add(config.log_file, level=config.level, rotation="1 week", retention="10 days", compression="zip")
    # Optionally add metrics/tracing hooks if config.metrics_enabled
    if config.metrics_enabled:
        # Metrics/tracing integration is framework-agnostic. Recommended options:
        # - Prometheus (prometheus_client)
        # - OpenTelemetry (opentelemetry)
        # Example: Initialize Prometheus metrics server
        from prometheus_client import start_http_server
        start_http_server(8000)
        # Example: Setup OpenTelemetry tracing hooks
        # from opentelemetry import trace
        # ...tracing setup code...
```

## 6. Logging Decorators

- **Timing Decorator**: Logs function start, end, and duration using Loguru.
- **Error Capture Decorator**: Use Loguru's `@logger.catch` to automatically log exceptions.
- **Contextual Decorator**: Use `logger.bind()` within a decorator to attach function name, arguments, or request context to log records.
- **Structured Output**: Decorators should log structured messages (e.g., key-value pairs or JSON) for easy parsing and analysis.

**Timing Decorator Example:**

```python
import time
from loguru import logger

def log_timing(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        logger.info("Started {}", func.__name__)
        result = func(*args, **kwargs)
        logger.info("Finished {} in {:.2f}s", func.__name__, time.time() - start)
        return result
    return wrapper
```

**Error Capture Decorator Example:**

```python
from loguru import logger

@logger.catch
def my_function():
    ...
```

## 7. API Middleware Logging Example

> **Note:** The following example assumes `request` and `response` objects have attributes like `path`, `method`, `headers`, `body`, and `status_code`. Adapt field names as needed for your web framework (e.g., FastAPI, Flask, Django, Starlette).

```python
from loguru import logger

def log_api_request(request, response):
    api_logger = logger.bind(
        endpoint=getattr(request, "path", None),
        method=getattr(request, "method", None),
        request_id=getattr(request, "headers", {}).get("X-Request-ID"),
        status_code=getattr(response, "status_code", None)
    )
    api_logger.info("API request", request_body=getattr(request, "body", None), response_body=getattr(response, "body", None))
    if getattr(response, "status_code", 200) >= 400:
        api_logger.error("API error", error=getattr(response, "body", None))
```

## 8. Implementation Details (Key Practices)

- Always log at appropriate levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `TRACE`, `SUCCESS`).
- Never log secrets or sensitive data.
- Use structured logs via format strings, custom sinks (e.g., JSON), and decorators.
- Configure file sinks with rotation, retention, and compression for persistent logs.
- Use contextual logging with `bind()` for request/response or task context.
- Use decorators for timing, error capture, and contextual logging on critical business logic functions.
- Logging level, enable/disable, and metrics/tracing hooks are configurable via the config module. Logger setup should read these values and apply them when initializing Loguru sinks.
- API middleware should log request/response details, status codes, and errors.
- Metrics/tracing hooks should be optional and configurable via config.

## 9. Testing & Extensibility

- Unit tests for logger setup, custom sinks, and contextual logging
- Add new log destinations by extending `setup.py` with additional `logger.add()` calls
- Document all logging changes in this file and in code docstrings

## 10. Summary

This module provides a robust, structured logging system for the project using Loguru. All logs are collected locally, are consistent, actionable, and extensible. Key sections for implementation and reference:

- **Domain & Purpose**: Overview and goals of the logging module
- **Directory Structure**: File layout for maintainability
- **Design Patterns**: Best practices and reusable patterns
- **Logging Configuration Requirements**: How to configure logging via the config module
- **Logger Setup Example**: Canonical setup pattern for Loguru
- **Logging Decorators**: Decorator patterns for timing, error capture, and context
- **API Middleware Logging**: Example for automatic request/response logging
- **Implementation Details (Key Practices)**: Checklist for robust, secure, and maintainable logging
- **Testing & Extensibility**: Guidance for testing and extending logging

Contextual logging, file sinks, and custom formatting ensure all API and background tasks are logged for debugging and analysis. No third-party endpoints are used by default.

## 11. Step by step Implementation Plan

- [ ] Step 1: Create the logging module directory and files
  - src/d3_item_salvager/logging/**init**.py
  - src/d3_item_salvager/logging/setup.py
  - src/d3_item_salvager/logging/middleware.py
  - src/d3_item_salvager/logging/metrics.py (optional, if metrics/tracing needed)
- [ ] Step 2: Define LoggingConfig dataclass in src/d3_item_salvager/config/base.py
  - Fields: enabled, level, metrics_enabled, log_file
- [ ] Step 3: Update AppConfig in src/d3_item_salvager/config/settings.py
  - Add logging: LoggingConfig field
- [ ] Step 4: Implement get_config().logging integration
  - Ensure get_config() returns AppConfig with logging field populated
- [ ] Step 5: Implement logger setup in src/d3_item_salvager/logging/setup.py
  - Use Loguru, configure sinks, levels, rotation, retention, compression
  - Read config from get_config().logging
  - Add metrics/tracing hooks if metrics_enabled is True
- [ ] Step 6: Implement logging decorators in src/d3_item_salvager/logging/setup.py or a dedicated decorators.py
  - Timing decorator (log_timing)
  - Error capture decorator (@logger.catch)
  - Contextual decorator (using logger.bind)
- [ ] Step 7: Implement API logging middleware in src/d3_item_salvager/logging/middleware.py
  - Function to log request/response details using logger.bind
  - Handle error logging for status_code >= 400
- [ ] Step 8: Integrate logger setup into application startup
  - Ensure setup_logger() is called at app entry point (e.g., **main**.py or FastAPI startup)
- [ ] Step 9: Refactor existing modules to use the new logger
  - Replace any legacy logging with Loguru logger from logging module
  - Use decorators/contextual logging where appropriate
- [ ] Step 10: Implement unit tests for logger setup, decorators, and middleware
  - Test logger configuration, custom sinks, contextual logging
- [ ] Step 11: Document logging usage and configuration in code docstrings and README
  - Add examples for setup, decorators, and middleware
- [ ] Step 12: (Optional) Implement metrics/tracing integration in metrics.py
  - Prometheus (prometheus_client) and/or OpenTelemetry hooks
  - Make sure metrics are enabled/disabled via config
