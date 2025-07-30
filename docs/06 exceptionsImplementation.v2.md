# Error Handling and Custom Exceptions – Implementation Plan v2

## Purpose & Scope

This plan defines a practical, maintainable approach for error handling and custom exceptions in the Diablo 3 Item Salvager project. It focuses on domain-specific errors (data, scraping), robust API error responses, and simple, consistent logging. The goal is to provide clarity, context, and actionable error information without unnecessary complexity.

## Directory Structure

```directory
src/d3_item_salvager/exceptions/
    __init__.py
    handlers.py      # Centralized error handling logic
```

## Exception Classes

### BaseError

All custom exceptions for API, data/model, and scraping errors inherit from `BaseError`. This provides consistent attributes (`message`, `code`, `context`).

```python
class BaseError(Exception):
    """Base exception for all domain errors."""
    def __init__(self, message: str, code: int, context: dict | None = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code}, context={self.context})"
```

### Domain-Specific Errors

- `DataError(BaseError)`: Data/model errors (validation, not found, integrity)
- `ScrapingError(BaseError)`: Scraping/parsing/network errors
- `ApiError(BaseError)`: API errors (bad request, not found, etc.)

Use standard Python/SQL exceptions for framework or third-party errors unless domain context is needed.

## Error Codes & Mapping

Focus on domain-specific codes for actionable errors. Use standard HTTP codes for generic API errors.

| Code  | Meaning                  | Error Type      | HTTP Status |
|-------|--------------------------|-----------------|-------------|
| 1001  | Data validation failed   | DataError       | 422         |
| 1002  | Data not found           | DataError       | 404         |
| 1003  | Data integrity error     | DataError       | 500         |
| 2001  | Scraping failed          | ScrapingError   | 500         |
| 2002  | Parsing error            | ScrapingError   | 422         |
| 2003  | Network error            | ScrapingError   | 502         |
| 400   | Bad request              | ApiError        | 400         |
| 404   | Not found                | ApiError        | 404         |
| 422   | Unprocessable entity     | ApiError        | 422         |
| 500   | Internal server error    | All             | 500         |

**Mapping Function:**

```python
def map_error_code_to_http(code: int) -> int:
    mapping = {
        1001: 422, 1002: 404, 1003: 500,
        2001: 500, 2002: 422, 2003: 502,
        400: 400, 404: 404, 422: 422, 500: 500,
    }
    return mapping.get(code, 500)
```

## Exception Context

Context dicts should be simple and relevant. Recommended fields:

- `field`: Field or parameter causing the error
- `model`: Model/table name (for data errors)
- `url`: URL being scraped (for scraping errors)
- `operation`: Operation (insert, update, etc.)
- `details`: Any extra info

## Handler Registration & Usage

Register one handler per domain error type. Use FastAPI’s `add_exception_handler` for API routes. For scripts/background jobs, catch and log exceptions manually.

**FastAPI Example:**

```python
from fastapi import FastAPI
from d3_item_salvager.exceptions import register_exception_handlers

app = FastAPI()
register_exception_handlers(app)
```

**Handler Example:**

```python
def handle_data_error(_request: Request, exc: Exception) -> JSONResponse:
    """Handle DataError exceptions and return a structured JSON response.

    Args:
        _request: FastAPI request object (unused).
        exc: The DataError exception instance (as Exception).

    Returns:
        JSONResponse with error details and appropriate HTTP status code.
    """
    if not isinstance(exc, DataError):
        msg = "Expected DataError"
        raise TypeError(msg)
    http_code = map_error_code_to_http(exc.code)
    logger.error(f"Data error: {exc.message} (code={exc.code})", extra={"context": exc.context})
    return JSONResponse(
        status_code=http_code,
        content={
            "error": {"message": exc.message, "code": exc.code, "context": exc.context}
        },
    )
```

## Logging

Use Loguru for structured logging. Log the error message, code, and context. Avoid custom logging filters unless needed for compliance or external integration.

**Example:**

```python
from loguru import logger
logger.error(f"Scraping error: {exc.message} (code={exc.code})", extra={"context": exc.context})
```

## Testing

- Test exception attributes and inheritance
- Test handler returns correct JSON response and logs error (including type checking and error code in log)
- Add tests for new error types/handlers as needed

## Documentation & Extensibility

- Document new error codes and context fields in this file
- Add Google-style docstrings to exception classes and handlers
- Update usage examples and code comments for new error types
- Only update README or API docs if public interfaces change

## Practical Guidance

- Use domain-specific exceptions for actionable errors (data/scraping)
- Use standard HTTP codes for generic API errors
- Keep context dicts simple and relevant
- Register one handler per domain error type
- Log errors with message, code, and context
- Avoid over-engineering: only add complexity if needed for maintainability or external requirements

---

This v2 plan streamlines error handling for clarity, maintainability, and practical use in the Diablo 3 Item Salvager project.
