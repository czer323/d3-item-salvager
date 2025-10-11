"""CLI entry point for d3_item_salvager. Initializes logging and runs main logic."""

import os
import time

import typer
import uvicorn
from dependency_injector.wiring import Provide, inject

from d3_item_salvager.api.factory import create_app
from d3_item_salvager.config.settings import AppConfig, load_runtime_env
from d3_item_salvager.container import Container
from d3_item_salvager.logging.setup import setup_logger
from d3_item_salvager.workers import (
    build_scheduler,
    shutdown_scheduler,
    start_scheduler,
)

app_cli = typer.Typer()


def _should_load_dotenv() -> bool:
    """Return True when runtime dotenv loading is enabled."""
    flag = os.getenv("APP_USE_DOTENV", "1").lower()
    return flag not in {"0", "false", "no"}


def _build_container() -> Container:
    """Initialise the DI container after loading dotenv configuration."""
    if _should_load_dotenv():
        load_runtime_env()
    container = Container()
    container.wire(modules=[__name__])  # pylint: disable=no-member
    return container


@inject
def run_api(app_config: AppConfig = Provide[Container.config]) -> None:
    """
    Start FastAPI application using uvicorn.
    """
    setup_logger(app_config)
    print(
        f"Logger initialized for {app_config.environment.value} environment."
        " Starting FastAPI app..."
    )

    fastapi_app = create_app()
    uvicorn.run(
        fastapi_app,
        host=app_config.api.host,
        port=app_config.api.port,
        reload=app_config.api.reload,
    )


@inject
def run_cli(app_config: AppConfig = Provide[Container.config]) -> None:
    """
    Run CLI tasks (stub).
    """
    setup_logger(app_config)
    print(
        f"Logger initialized for {app_config.environment.value} environment."
        " Ready to run CLI tasks."
    )
    # dTODO: Implement CLI logic here


def _wait_forever() -> None:
    """Block the current thread until interrupted."""
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass


@inject
def run_workers(app_config: AppConfig = Provide[Container.config]) -> None:
    """Run the background scheduler until interrupted."""
    setup_logger(app_config)
    scheduler = build_scheduler(config=app_config)
    start_scheduler(scheduler)
    typer.echo("Scheduler started. Press Ctrl+C to exit.")

    try:
        _wait_forever()
    finally:
        shutdown_scheduler(
            scheduler,
            timeout_seconds=app_config.scheduler.shutdown_timeout_seconds,
        )


@app_cli.command()
def api() -> None:
    """Run FastAPI server."""
    _build_container()
    run_api()


@app_cli.command()
def cli() -> None:
    """Run CLI tasks."""
    _build_container()
    run_cli()


@app_cli.command()
def workers() -> None:
    """Run background scheduler workers."""
    _build_container()
    run_workers()


@app_cli.command("import-guides")
def import_guides(
    force_refresh: bool = typer.Option(
        False,
        "--force-refresh",
        "-f",
        help="Force a fresh fetch of guide metadata, bypassing any cached data.",
    ),
) -> None:
    """Fetch Maxroll guides and synchronise the local database."""
    container = _build_container()
    app_config = container.config()
    setup_logger(app_config)

    service = container.build_guide_service()
    refresh_flag = force_refresh or app_config.is_production
    summary = service.prepare_database(force_refresh=refresh_flag)
    typer.echo(
        "Guide import complete "
        f"(processed={summary.guides_processed}, skipped={summary.guides_skipped}, "
        f"builds={summary.builds_created}, profiles={summary.profiles_created}, "
        f"items={summary.items_created}, usages={summary.usages_created})."
    )


if __name__ == "__main__":
    app_cli()
