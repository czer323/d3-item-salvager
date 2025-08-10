"""CLI entry point for d3_item_salvager. Initializes logging and runs main logic."""

import typer
import uvicorn
from dependency_injector.wiring import Provide, inject

from d3_item_salvager.api.factory import create_app
from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.container import Container
from d3_item_salvager.logging.setup import setup_logger

app_cli = typer.Typer()


@inject
def run_api(app_config: AppConfig = Provide[Container.config]) -> None:
    """
    Start FastAPI application using uvicorn.
    """
    setup_logger(app_config)
    print("Logger initialized. Starting FastAPI app...")

    fastapi_app = create_app()
    # WARNING: app_config.api may not exist. Update to use correct config fields if needed.
    uvicorn.run(
        fastapi_app,
        host=getattr(app_config, "api_host", "127.0.0.1"),
        port=getattr(app_config, "api_port", 8000),
        reload=getattr(app_config, "api_reload", False),
    )


@inject
def run_cli(app_config: AppConfig = Provide[Container.config]) -> None:
    """
    Run CLI tasks (stub).
    """
    setup_logger(app_config)
    print("Logger initialized. Ready to run CLI tasks.")
    # dTODO: Implement CLI logic here


@app_cli.command()
def api() -> None:
    """Run FastAPI server."""
    container = Container()
    container.wire(modules=[__name__])  # pylint: disable=no-member
    run_api()


@app_cli.command()
def cli() -> None:
    """Run CLI tasks."""
    container = Container()
    container.wire(modules=[__name__])  # pylint: disable=no-member
    run_cli()


if __name__ == "__main__":
    app_cli()
