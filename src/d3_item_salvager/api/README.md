# Diablo 3 Item Salvager - API Module

## API Overview

This module is responsible for creating and configuring the FastAPI application. It defines the API endpoints, dependencies, and the application factory.

### Application Factory

The `create_app()` function in `src/d3_item_salvager/api/factory.py` is the entry point for creating the FastAPI application. It initializes the app and registers the API endpoints.

**Example:**
```python
from d3_item_salvager.api.factory import create_app

app = create_app()
```

### Dependencies

The `src/d3_item_salvager/api/dependencies.py` file defines the dependency injection (DI) providers for the application. It uses FastAPI's `Depends` system to provide instances of `AppConfig`, `Session`, and `ItemSalvageService` to the API endpoints.

The dependencies are defined using `typing.Annotated` for better type hinting and clarity.

**Available Dependencies:**
- `ConfigDep`: Provides the `AppConfig` instance.
- `SessionDep`: Provides a `sqlmodel.Session` instance for database access.
- `ServiceDep`: Provides the `ItemSalvageService` instance.

### Endpoints

The following endpoints are defined in `src/d3_item_salvager/api/factory.py`:

- **GET /health**: A health check endpoint that returns the application's status and name.
- **GET /sample**: A sample endpoint that demonstrates the usage of the dependency injection system.

## Discrepancies

- The `/sample` endpoint is for demonstration purposes and should be removed or replaced with actual application endpoints.
- The module is tightly coupled with the `ItemSalvageService`. If more services are added, the dependency providers will need to be updated. A more generic service provider might be beneficial.
- There are no routers implemented. As the application grows, using FastAPI's `APIRouter` would be a better way to organize endpoints.
