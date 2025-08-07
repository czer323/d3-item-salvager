"""Dependency injection container for the application."""

from dependency_injector import containers, providers
from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from d3_item_salvager.config.settings import AppConfig


class Container(containers.DeclarativeContainer):  # pylint: disable=too-few-public-methods
    """
    Main dependency injection container for the application.

    This container holds the configuration and other services that are shared
    across the application.
    """

    config = providers.Singleton(AppConfig)

    engine: providers.Provider[Engine] = providers.Singleton(
        create_engine,
        url=config.provided.database.url,
        echo=True,
    )

    session: providers.Provider[Session] = providers.Factory(
        Session,
        bind=engine,
    )
