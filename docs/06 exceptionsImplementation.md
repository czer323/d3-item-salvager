# Error Handling and Custom Exceptions Module – Implementation Plan

## Domain & Purpose

Defines all domain-specific exceptions, error codes, and centralizes error handling logic for API, scraping, and data layers. Ensures consistent error reporting and robust handling across the project.

## Directory Structure

```directory
src/d3_item_salvager/exceptions/
    __init__.py
    api.py           # API-specific exceptions
    data.py          # Data/model exceptions
    scraping.py      # Scraper exceptions
    handlers.py      # Centralized error handling logic
```

## Tools & Libraries

- Python built-in exceptions
- FastAPI exception handlers

## Design Patterns

- Custom exception classes with context/error codes
- Centralized error handler functions
- API error middleware for consistent JSON error responses

## Key Classes & Functions

- `ApiError`, `DataError`, `ScrapingError`: Custom exception classes
- `handle_api_error()`: FastAPI exception handler
- `handle_scraping_error()`: Scraper error handler

## Implementation Details

- Use narrow exception catching; never catch `Exception` broadly
- Document all exceptions with context and error codes
- Ensure all API errors return consistent JSON responses
- Log all errors with stack traces
- Example usage:

  ```python
  from d3_item_salvager.exceptions.api import ApiError
  raise ApiError("Invalid request", code=400)
  ```

- Centralized error handlers should be registered with FastAPI and used in scraping/data layers

## Testing & Extensibility

- Unit tests for exception classes and handlers
- Add new exception types by extending the relevant module
- Document all error handling changes in this file and in code docstrings

## Example Exception Class

```python
class ApiError(Exception):
    """Custom exception for API errors."""
    def __init__(self, message: str, code: int = 500):
        super().__init__(message)
        self.code = code
```

## Summary

This module provides a robust, consistent error handling and exception system for the project. All errors must be reported with context and codes, and handled centrally for maintainability and debugging.
