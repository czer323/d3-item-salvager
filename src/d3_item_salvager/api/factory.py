"""Application factory for FastAPI app with DI."""

from fastapi import FastAPI  # 'Depends' is no longer needed here

from d3_item_salvager.api.dependencies import (
    ConfigDep,
    ServiceDep,
    SessionDep,
)

# 'AppConfig' and 'ItemSalvageService' are no longer needed here


def create_app() -> FastAPI:
    """
    Create and configure FastAPI app with dependency injection.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    app = FastAPI(title="Diablo 3 Item Salvager API")

    @app.get("/health", summary="Health check", tags=["system"])
    def health(config: ConfigDep) -> dict[str, str]:
        """Health check endpoint with config DI."""
        # The 'config' object here is an AppConfig instance
        return {"status": "ok", "app_name": config.app_name}

    @app.get("/sample", summary="Sample endpoint", tags=["demo"], response_model=None)
    def sample(
        db: SessionDep,
        config: ConfigDep,
        service: ServiceDep,
    ) -> dict[str, str]:
        """Sample endpoint demonstrating DI for config, DB, and service."""
        # FastAPI and mypy know the types:
        # db: Session
        # config: AppConfig
        # service: ItemSalvageService
        return {
            "app_name": config.app_name,
            "db_type": type(db).__name__,
            "service_type": type(service).__name__,
        }

    return app
