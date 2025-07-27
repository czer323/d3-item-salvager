# Dependency Injection / Application Factory Module – Implementation Plan

## Domain & Purpose

Centralizes dependency injection and application factory logic for API, DB, services, and config. Ensures all dependencies are injected, not global, and supports testability and modularity.

## Directory Structure

```directory
src/d3_item_salvager/api/
    dependencies.py   # Dependency injection logic
    factory.py        # Application factory (FastAPI app creation)
```

## Tools & Libraries

- FastAPI dependency injection
- Python stdlib

## Design Patterns

- Factory pattern for app creation
- Dependency injection via FastAPI Depends

## Key Functions & Classes

- `get_db_session()`: DB session provider
- `get_config()`: Config provider
- `get_service()`: Service provider
- `create_app()`: FastAPI app factory

## Implementation Details

- Never use global state; always inject dependencies
- Document all dependency providers
- Use FastAPI's dependency injection for all endpoints
- Example usage:

  ```python
  from d3_item_salvager.api.factory import create_app
  app = create_app()
  ```

- All endpoints should use dependency providers for DB, config, and services

## Testing & Extensibility

- Unit tests for dependency providers and app factory
- Add new dependencies by updating `dependencies.py` and `factory.py`
- Document all DI changes in this file and in code docstrings

## Example Dependency Provider

```python
from fastapi import Depends

def get_db_session():
    """Provide a database session for requests."""
    # Implementation here
    pass
```

## Summary

This module provides robust dependency injection and application factory logic for the project. All dependencies are injected for modularity and testability, and the app factory pattern ensures clean startup and configuration.
