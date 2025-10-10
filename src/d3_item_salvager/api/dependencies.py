"""Dependency providers for config, DB, and services."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.container import Container
from d3_item_salvager.services.item_salvage import (
    ItemSalvageDependencies,
    ItemSalvageService,
)

# --- No changes needed below this line ---


def get_config() -> AppConfig:
    """Provide AppConfig instance for DI."""
    return Container.config()


def get_db_session() -> Generator[Session, None, None]:
    """Provide a SQLModel Session from DI container, yield for proper cleanup."""
    container = Container()
    session = container.session()
    try:
        yield session
    finally:
        session.close()


# --- Your existing SessionDep is perfect ---
SessionDep = Annotated[Session, Depends(get_db_session)]


def get_service(
    db: SessionDep,  # <-- Use the annotated SessionDep here for consistency
    config: AppConfig = Depends(get_config),
) -> ItemSalvageService:
    """Provide ItemSalvageService instance for DI."""
    dependencies = ItemSalvageDependencies(
        session=db,
        config=config,
        logger=Container.logger(),
    )
    return ItemSalvageService(dependencies=dependencies)


# --- Add an Annotated dependency for the service ---
ServiceDep = Annotated[ItemSalvageService, Depends(get_service)]
ConfigDep = Annotated[AppConfig, Depends(get_config)]
