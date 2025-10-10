"""Dependency injection container for the application."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import containers, providers
from sqlmodel import Session, create_engine

from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.logging.adapters import get_loguru_service_logger
from d3_item_salvager.logging.setup import setup_logger
from d3_item_salvager.services.build_guide_service import (
    BuildGuideDependencies,
    BuildGuideService,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

    from d3_item_salvager.services.protocols import ServiceLogger


def _configure_logger(app_config: AppConfig) -> ServiceLogger:
    """Initialise and return the shared Loguru logger instance."""
    setup_logger(app_config)
    return get_loguru_service_logger()


class Container(containers.DeclarativeContainer):  # pylint: disable=too-few-public-methods
    """Main dependency injection container for the application."""

    config = providers.Singleton(AppConfig)

    logger = providers.Singleton(_configure_logger, app_config=config)

    engine: providers.Provider[Engine] = providers.Singleton(
        create_engine,
        url=config.provided.database.url,  # pylint: disable=no-member
        echo=True,
    )

    session: providers.Provider[Session] = providers.Factory(
        Session,
        bind=engine,
    )

    build_guide_dependencies = providers.Factory(
        BuildGuideDependencies,
        session_factory=session.provider,
    )

    build_guide_service = providers.Factory(
        BuildGuideService,
        config=config,
        logger=logger,
        dependencies=build_guide_dependencies,
    )
