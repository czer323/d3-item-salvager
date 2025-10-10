"""Application factory for FastAPI app with DI."""

from fastapi import FastAPI

from d3_item_salvager.api.dependencies import ConfigDep, ServiceDep, SessionDep


# 'AppConfig' and 'ItemSalvageService' are no longer needed here
def _health_endpoint(config: ConfigDep) -> dict[str, str]:
    """Return a simple health payload for monitoring probes."""
    return {"status": "ok", "app_name": config.app_name}


def _sample_endpoint(
    db: SessionDep,
    config: ConfigDep,
    service: ServiceDep,
) -> dict[str, str]:
    """Expose sample dependency-injected information for diagnostics."""
    return {
        "app_name": config.app_name,
        "db_type": type(db).__name__,
        "service_type": type(service).__name__,
    }


def _register_routes(app: FastAPI) -> None:
    """Attach API routes to the provided FastAPI application."""
    app.add_api_route(
        "/health",
        _health_endpoint,
        methods=["GET"],
        summary="Health check",
        tags=["system"],
    )
    app.add_api_route(
        "/sample",
        _sample_endpoint,
        methods=["GET"],
        summary="Sample endpoint",
        tags=["demo"],
        response_model=None,
    )


def create_app() -> FastAPI:
    """
    Create and configure FastAPI app with dependency injection.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    app = FastAPI(title="Diablo 3 Item Salvager API")
    _register_routes(app)
    return app
