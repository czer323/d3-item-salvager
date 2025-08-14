# Diablo 3 Item Salvager - Exceptions Module

## Exceptions Overview

This module defines the custom exception hierarchy for the application. It provides a `BaseError` class that all other custom exceptions inherit from, and specific exception classes for different types of errors.

### Exception Classes

- **`BaseError`**: The base class for all custom exceptions. It includes a message, a code, and an optional context dictionary.
- **`ApiError`**: For errors related to the API.
- **`DataError`**: For errors related to data and model validation.
- **`ScrapingError`**: For errors related to web scraping and parsing.

### Exception Handlers

The `src/d3_item_salvager/exceptions/handlers.py` file provides exception handlers for the custom exception classes. These handlers are compatible with FastAPI and can be registered to automatically catch and handle the custom exceptions.

The handlers log the error and return a structured JSON response with an appropriate HTTP status code.

### Usage

To raise a custom exception, you can simply instantiate one of the exception classes and raise it:

```python
from d3_item_salvager.exceptions.data import DataError

raise DataError("Invalid item ID", code=1001, context={"item_id": "123"})
```

To register the exception handlers in your FastAPI application, you can add them individually:

```python
from fastapi import FastAPI
from d3_item_salvager.exceptions import handlers, DataError

app = FastAPI()
app.add_exception_handler(DataError, handlers.handle_data_error)
```

## Discrepancies

- The error codes are defined in the `map_error_code_to_http` function in `handlers.py`. This is not ideal as it couples the error codes to the handlers. It would be better to define the error codes in a central place, for example, in an `Enum` or a configuration file.
- The `handle_*_error` functions in `handlers.py` have very similar implementations. They could be refactored into a single generic handler that takes the exception type as an argument.
- The type hint for `exc` in the handler functions is `Exception`, but the code then checks if the exception is of the expected type. It would be better to use the specific exception type in the function signature, as FastAPI supports this. For example: `def handle_data_error(_request: Request, exc: DataError) -> JSONResponse:`. This would remove the need for the `isinstance` check and the `TypeError`.
- There is no function to register all exception handlers at once, as suggested in the docstring of `handlers.py`. This would be a useful addition.
