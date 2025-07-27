# Logging and Observability Module – Implementation Plan

## Domain & Purpose

Provides unified, structured logging and hooks for observability (metrics, tracing, error reporting) across all modules. Ensures all logs are consistent, actionable, and integrated with external monitoring if needed.

## Directory Structure

```directory
src/d3_item_salvager/logging/
    __init__.py
    setup.py          # Logger setup/config
    middleware.py     # API logging middleware
    metrics.py        # Metrics/tracing hooks (optional)
```

## Tools & Libraries

- `structlog` or Python `logging` (stdlib)
- `sentry-sdk` (optional, error reporting)
- `prometheus_client` (optional, metrics)
- `opentelemetry` (optional, tracing)

## Design Patterns

- Singleton logger instance
- Structured logging (JSON, key-value)
- Middleware for API request/response logging
- Decorators/context managers for timing, error capture

## Key Classes & Functions

- `setup_logger(config)`: Initializes logger with config
- `get_logger()`: Singleton accessor
- `log_request()`: API middleware for request/response logs
- `log_error()`: Error logging utility
- `log_metric()`: Metrics/tracing utility

## Implementation Details

- Always log at appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Never log secrets or sensitive data
- Use structured logs for easy parsing/analysis
- Integrate with external monitoring if needed
- Example usage:

  ```python
  from d3_item_salvager.logging import get_logger
  logger = get_logger()
  logger.info("Scraper started", extra={"guide_url": url})
  ```

- API middleware should log request/response details, status codes, and errors
- Metrics/tracing hooks should be optional and configurable

## Testing & Extensibility

- Unit tests for logger setup and middleware
- Add new log destinations by extending `setup.py`
- Document all logging changes in this file and in code docstrings

## Example Logger Setup

```python
import structlog

def setup_logger():
    """Configure structured logger for the project."""
    structlog.configure(
        processors=[
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
```

## Summary

This module provides a robust, structured logging and observability system for the project. All logs must be consistent, actionable, and integrated with external monitoring as needed. Middleware and utilities ensure all API and background tasks are logged for debugging and analysis.
